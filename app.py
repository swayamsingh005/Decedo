import streamlit as st
import json
from datetime import datetime
from zoneinfo import ZoneInfo
from google import genai
from fpdf import FPDF
from supabase import create_client, Client

# =========================================================
# PAGE CONFIG
# =========================================================
st.set_page_config(
    page_title="Decedo",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# =========================================================
# STYLES
# =========================================================
st.markdown("""
<style>
    .main {
        background: linear-gradient(180deg, #f8fafc 0%, #eef4ff 100%);
    }
    .block-container {
        max-width: 1180px;
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    .hero {
        background: linear-gradient(135deg, #0f172a 0%, #1d4ed8 100%);
        border-radius: 28px;
        padding: 36px 32px;
        color: white;
        box-shadow: 0 18px 40px rgba(15, 23, 42, 0.18);
        margin-bottom: 24px;
    }
    .card {
        background: rgba(255,255,255,0.97);
        border: 1px solid #e5e7eb;
        border-radius: 24px;
        padding: 24px;
        box-shadow: 0 10px 30px rgba(15, 23, 42, 0.08);
        margin-bottom: 18px;
    }
    .soft-card {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 20px;
        padding: 20px;
        box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06);
        margin-bottom: 16px;
    }
    .nav-card {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 24px;
        padding: 28px;
        box-shadow: 0 10px 30px rgba(15, 23, 42, 0.08);
        text-align: center;
        min-height: 210px;
    }
    .debate-box {
        background: linear-gradient(180deg, #ffffff 0%, #f8fbff 100%);
        border: 1px solid #dbeafe;
        border-radius: 18px;
        padding: 18px;
        box-shadow: 0 8px 20px rgba(15, 23, 42, 0.04);
        margin-bottom: 14px;
    }
    .judge-box {
        background: linear-gradient(180deg, #f0fdf4 0%, #ecfeff 100%);
        border: 1px solid #bbf7d0;
        border-radius: 18px;
        padding: 18px;
        box-shadow: 0 8px 20px rgba(15, 23, 42, 0.04);
        margin-bottom: 14px;
    }
    .stButton>button {
        border-radius: 14px;
        font-weight: 700;
        height: 3em;
    }
    .stTextInput>div>div>input,
    .stTextArea textarea,
    .stSelectbox>div>div {
        border-radius: 12px;
    }
    div[data-testid="stMetric"] {
        background: white;
        border: 1px solid #e5e7eb;
        padding: 14px;
        border-radius: 18px;
        box-shadow: 0 6px 18px rgba(15, 23, 42, 0.05);
    }
</style>
""", unsafe_allow_html=True)

# =========================================================
# SECRETS / CLIENTS
# =========================================================
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_ANON_KEY = st.secrets["SUPABASE_ANON_KEY"]
SUPABASE_SERVICE_ROLE_KEY = st.secrets["SUPABASE_SERVICE_ROLE_KEY"]
GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]

supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
admin_supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
gemini_client = genai.Client(api_key=GEMINI_API_KEY)

# =========================================================
# SESSION DEFAULTS
# =========================================================
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if "current_page" not in st.session_state:
    st.session_state.current_page = "auth"

if "user_email" not in st.session_state:
    st.session_state.user_email = None

if "user_id" not in st.session_state:
    st.session_state.user_id = None

if "history" not in st.session_state:
    st.session_state.history = []

# =========================================================
# AUTH FUNCTIONS
# =========================================================
def login_user(email: str, password: str):
    try:
        result = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        return True, result
    except Exception as e:
        return False, str(e)

def signup_user(email: str, password: str):
    try:
        result = supabase.auth.sign_up({
            "email": email,
            "password": password
        })
        return True, result
    except Exception as e:
        return False, str(e)

def logout_user():
    try:
        supabase.auth.sign_out()
    except Exception:
        pass

# =========================================================
# DATABASE HELPERS
# =========================================================
def get_profile():
    try:
        result = admin_supabase.table("profiles").select("*").eq("user_id", st.session_state.user_id).limit(1).execute()
        if result.data:
            return result.data[0]
    except Exception:
        pass
    return None

def ensure_profile():
    existing = get_profile()
    if existing:
        return existing

    try:
        admin_supabase.table("profiles").upsert({
            "user_id": st.session_state.user_id,
            "email": st.session_state.user_email,
            "username": "",
            "created_at": datetime.now(ZoneInfo("Asia/Kolkata")).isoformat()
        }).execute()
    except Exception:
        pass

    return get_profile()

def update_username(username: str):
    try:
        admin_supabase.table("profiles").update({
            "username": username.strip()
        }).eq("user_id", st.session_state.user_id).execute()
        return True
    except Exception:
        return False

def get_subscription():
    try:
        result = admin_supabase.table("subscriptions").select("*").eq("user_id", st.session_state.user_id).limit(1).execute()
        if result.data:
            return result.data[0]
    except Exception:
        pass

    return {"plan": "free", "status": "active"}

def get_plan_limit(plan: str):
    plan = (plan or "free").lower()
    if plan == "free":
        return 3
    if plan == "pro":
        return 50
    if plan == "premium":
        return None
    return 3

def get_or_create_usage():
    now = datetime.now(ZoneInfo("Asia/Kolkata")).isoformat()

    try:
        result = admin_supabase.table("usage_tracking").select("*").eq("user_id", st.session_state.user_id).limit(1).execute()
        if result.data:
            return result.data[0]

        new_row = {
            "user_id": st.session_state.user_id,
            "reports_today": 0,
            "last_reset": now
        }
        admin_supabase.table("usage_tracking").insert(new_row).execute()
        return new_row
    except Exception:
        return {
            "user_id": st.session_state.user_id,
            "reports_today": 0,
            "last_reset": now
        }

def reset_usage_if_new_day():
    usage = get_or_create_usage()
    now = datetime.now(ZoneInfo("Asia/Kolkata"))
    today = now.date()

    try:
        last_reset_date = datetime.fromisoformat(
            str(usage["last_reset"]).replace("Z", "+00:00")
        ).astimezone(ZoneInfo("Asia/Kolkata")).date()
    except Exception:
        last_reset_date = today

    if last_reset_date != today:
        try:
            admin_supabase.table("usage_tracking").update({
                "reports_today": 0,
                "last_reset": now.isoformat()
            }).eq("user_id", st.session_state.user_id).execute()
        except Exception:
            pass
        usage["reports_today"] = 0
        usage["last_reset"] = now.isoformat()

    return usage

def get_usage():
    return reset_usage_if_new_day()

def user_can_generate():
    sub = get_subscription()
    plan = sub.get("plan", "free")
    status = sub.get("status", "active")
    usage = get_usage()
    used = int(usage.get("reports_today", 0) or 0)
    limit = get_plan_limit(plan)

    if status != "active":
        return False, plan, used, limit

    if limit is None:
        return True, plan, used, limit

    return used < limit, plan, used, limit

def increment_usage():
    usage = get_usage()
    used = int(usage.get("reports_today", 0) or 0)
    now = datetime.now(ZoneInfo("Asia/Kolkata")).isoformat()

    try:
        admin_supabase.table("usage_tracking").update({
            "reports_today": used + 1,
            "last_reset": now
        }).eq("user_id", st.session_state.user_id).execute()
    except Exception:
        try:
            admin_supabase.table("usage_tracking").insert({
                "user_id": st.session_state.user_id,
                "reports_today": used + 1,
                "last_reset": now
            }).execute()
        except Exception:
            pass

def save_report(question, decision_type, option_a, option_b, analysis_data, scenario_data):
    try:
        admin_supabase.table("reports").insert({
            "user_id": st.session_state.user_id,
            "decision_type": decision_type,
            "question": question,
            "option_a": option_a if option_a else None,
            "option_b": option_b if option_b else None,
            "analysis": {
                "analysis": analysis_data,
                "scenario": scenario_data
            }
        }).execute()
    except Exception:
        pass

    increment_usage()

# =========================================================
# AI / PDF HELPERS
# =========================================================
def parse_json_response(raw_text: str) -> dict:
    clean_text = raw_text.strip()

    if clean_text.startswith("```json"):
        clean_text = clean_text.replace("```json", "", 1).strip()
    if clean_text.startswith("```"):
        clean_text = clean_text.replace("```", "", 1).strip()
    if clean_text.endswith("```"):
        clean_text = clean_text[:-3].strip()

    return json.loads(clean_text)

def calculate_grade(score):
    try:
        score = float(str(score).replace("/10", "").strip())
    except Exception:
        return "N/A"

    if score >= 9:
        return "A+"
    elif score >= 8:
        return "A"
    elif score >= 7:
        return "B"
    elif score >= 6:
        return "C"
    return "D"

def confidence_to_int(confidence_text):
    try:
        text = str(confidence_text).replace("%", "").strip()
        return max(0, min(100, int(float(text))))
    except Exception:
        return 0

def clean_pdf_text(text):
    return str(text).replace("–", "-").replace("—", "-").replace("’", "'").replace("•", "-")

class PremiumPDF(FPDF):
    def footer(self):
        self.set_y(-12)
        self.set_font("Arial", "I", 9)
        self.cell(0, 8, f"Page {self.page_no()}", align="C")

def create_pdf_report(
    question,
    decision_type,
    summary,
    best_option,
    risk_level,
    decision_score,
    confidence_level,
    decision_grade,
    market_lens,
    execution_lens,
    risk_lens,
    growth_lens,
    why_points,
    next_step,
    strategic_insight,
    final_opinion,
    ai_1_argument="",
    ai_2_argument="",
    option_a="",
    option_b="",
    option_a_future=None,
    option_b_future=None,
    recommended_path_future=None
):
    pdf = PremiumPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    india_time = datetime.now(ZoneInfo("Asia/Kolkata")).strftime("%d %b %Y, %I:%M %p IST")

    pdf.set_font("Arial", "B", 18)
    pdf.cell(0, 10, "Decedo AI Decision Report", ln=True)
    pdf.set_font("Arial", "", 11)
    pdf.cell(0, 8, f"Generated on: {india_time}", ln=True)
    pdf.ln(4)

    def sec(title, body):
        pdf.set_font("Arial", "B", 13)
        pdf.cell(0, 8, clean_pdf_text(title), ln=True)
        pdf.set_font("Arial", "", 11)
        pdf.multi_cell(0, 7, clean_pdf_text(body))
        pdf.ln(2)

    sec("Decision Type", decision_type)
    sec("Decision Question", question)
    sec("Comparison Summary", summary)
    sec("Best Choice", best_option)
    sec("Risk Level", risk_level)
    sec("Decision Score", str(decision_score))
    sec("Confidence", str(confidence_level))
    sec("Decision Grade", decision_grade)

    if ai_1_argument:
        sec("AI 1 - Argument for Option A", ai_1_argument)
    if ai_2_argument:
        sec("AI 2 - Argument for Option B", ai_2_argument)
    if final_opinion:
        sec("Final Opinion", final_opinion)

    sec("Market Lens", market_lens)
    sec("Execution Lens", execution_lens)
    sec("Risk Lens", risk_lens)
    sec("Growth Lens", growth_lens)

    if why_points:
        pdf.set_font("Arial", "B", 13)
        pdf.cell(0, 8, "Why", ln=True)
        pdf.set_font("Arial", "", 11)
        for point in why_points:
            pdf.multi_cell(0, 7, clean_pdf_text(f"- {point}"))
        pdf.ln(2)

    sec("First Next Step", next_step)
    sec("Strategic Insight", strategic_insight)

    pdf.set_font("Arial", "B", 13)
    pdf.cell(0, 8, "Scenario Simulation", ln=True)
    pdf.set_font("Arial", "", 11)

    if option_a_future and option_b_future:
        pdf.multi_cell(0, 7, clean_pdf_text(f"Option A Future: {option_a}"))
        pdf.multi_cell(0, 7, clean_pdf_text(f"3 Months: {option_a_future.get('3_months', 'Not available')}"))
        pdf.multi_cell(0, 7, clean_pdf_text(f"1 Year: {option_a_future.get('1_year', 'Not available')}"))
        pdf.multi_cell(0, 7, clean_pdf_text(f"5 Years: {option_a_future.get('5_years', 'Not available')}"))
        pdf.ln(1)

        pdf.multi_cell(0, 7, clean_pdf_text(f"Option B Future: {option_b}"))
        pdf.multi_cell(0, 7, clean_pdf_text(f"3 Months: {option_b_future.get('3_months', 'Not available')}"))
        pdf.multi_cell(0, 7, clean_pdf_text(f"1 Year: {option_b_future.get('1_year', 'Not available')}"))
        pdf.multi_cell(0, 7, clean_pdf_text(f"5 Years: {option_b_future.get('5_years', 'Not available')}"))
    elif recommended_path_future:
        pdf.multi_cell(0, 7, clean_pdf_text(f"3 Months: {recommended_path_future.get('3_months', 'Not available')}"))
        pdf.multi_cell(0, 7, clean_pdf_text(f"1 Year: {recommended_path_future.get('1_year', 'Not available')}"))
        pdf.multi_cell(0, 7, clean_pdf_text(f"5 Years: {recommended_path_future.get('5_years', 'Not available')}"))

    return pdf.output(dest="S").encode("latin-1")

# =========================================================
# PAGE RENDERERS
# =========================================================
def render_auth():
    st.markdown("""
    <div class="hero">
        <div style="font-size:38px;font-weight:800;">🧠 Decedo</div>
        <div style="font-size:20px;font-weight:600;margin-top:6px;">
            AI Decision Operating System
        </div>
        <div style="font-size:15px;opacity:0.9;margin-top:10px;max-width:760px;">
            Structured reasoning, scenario simulation, strategic insight, and premium downloadable reports.
        </div>
    </div>
    """, unsafe_allow_html=True)

    left, right = st.columns([1.15, 0.85], gap="large")

    with left:
        st.markdown("""
        <div class="card">
            <h2 style="margin-top:0;">Why Decedo feels premium</h2>
            <p>• AI decision intelligence dashboard</p>
            <p>• AI 1 vs AI 2 reasoning</p>
            <p>• scenario simulation</p>
            <p>• strategic insight</p>
            <p>• premium PDF reports</p>
            <p>• SaaS-style user system</p>
        </div>
        """, unsafe_allow_html=True)

    with right:
        st.markdown('<div class="card">', unsafe_allow_html=True)

        tab1, tab2 = st.tabs(["Login", "Create Account"])

        with tab1:
            st.markdown("### Welcome back")
            login_email = st.text_input("Email", key="login_email")
            login_password = st.text_input("Password", type="password", key="login_password")

            if st.button("Login", type="primary", use_container_width=True):
                ok, result = login_user(login_email, login_password)
                if ok and result.user:
                    st.session_state.authenticated = True
                    st.session_state.user_email = result.user.email
                    st.session_state.user_id = result.user.id
                    ensure_profile()
                    get_or_create_usage()
                    st.session_state.current_page = "home"
                    st.rerun()
                else:
                    st.error("Invalid email or password.")

        with tab2:
            st.markdown("### Create your account")
            signup_email = st.text_input("Email", key="signup_email")
            signup_password = st.text_input("Password", type="password", key="signup_password")
            signup_confirm = st.text_input("Confirm Password", type="password", key="signup_confirm")

            if st.button("Create Account", use_container_width=True):
                if signup_password != signup_confirm:
                    st.error("Passwords do not match.")
                else:
                    ok, result = signup_user(signup_email, signup_password)
                    if ok:
                        st.success("Account created. Now login.")
                    else:
                        st.error(str(result))

        st.markdown('</div>', unsafe_allow_html=True)

def render_home():
    usage = get_usage()
    sub = get_subscription()
    plan = sub.get("plan", "free")
    limit = get_plan_limit(plan)
    used_today = int(usage.get("reports_today", 0) or 0)

    st.markdown("""
    <div class="hero">
        <div style="font-size:38px;font-weight:800;">🧠 Decedo</div>
        <div style="font-size:20px;font-weight:600;margin-top:6px;">
            AI Decision Operating System
        </div>
        <div style="font-size:15px;opacity:0.9;margin-top:10px;max-width:760px;">
            Premium decision intelligence for ambitious people.
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.success(f"Logged in as {st.session_state.user_email}")

    usage_text = f"{used_today}/{limit}" if limit is not None else f"{used_today}/Unlimited"
    st.info(f"Plan: {plan.title()} • Usage Today: {usage_text}")

    col1, col2 = st.columns(2, gap="large")

    with col1:
        st.markdown("""
        <div class="nav-card">
            <div style="font-size:30px;">👤</div>
            <h3>Profile</h3>
            <p>Manage username, plan, and account overview.</p>
        </div>
        """, unsafe_allow_html=True)

        if st.button("Open Profile", use_container_width=True, type="primary"):
            st.session_state.current_page = "profile"
            st.rerun()

    with col2:
        st.markdown("""
        <div class="nav-card">
            <div style="font-size:30px;">🔬</div>
            <h3>Decision Lab</h3>
            <p>Run decision analysis, scenario simulation, and download premium reports.</p>
        </div>
        """, unsafe_allow_html=True)

        if st.button("Open Decision Lab", use_container_width=True):
            st.session_state.current_page = "lab"
            st.rerun()

def render_profile():
    profile = ensure_profile()
    subscription = get_subscription()
    usage = get_usage()

    username_value = ""
    if profile and profile.get("username"):
        username_value = profile["username"]

    plan = subscription.get("plan", "free")
    limit = get_plan_limit(plan)
    used_today = int(usage.get("reports_today", 0) or 0)
    usage_text = f"{used_today}/{limit}" if limit is not None else f"{used_today}/Unlimited"

    st.markdown(f"""
    <div class="hero">
        <div style="font-size:34px;font-weight:800;">👤 Profile</div>
        <div style="font-size:18px;font-weight:600;margin-top:6px;">
            {username_value if username_value else "Set your Decedo username"}
        </div>
        <div style="font-size:14px;opacity:0.9;margin-top:8px;">
            Manage your account, username, plan, and usage.
        </div>
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)

    with c1:
        if st.button("← Back Home", use_container_width=True):
            st.session_state.current_page = "home"
            st.rerun()

    with c2:
        if st.button("Open Decision Lab", use_container_width=True):
            st.session_state.current_page = "lab"
            st.rerun()

    with c3:
        if st.button("Logout", use_container_width=True):
            logout_user()
            st.session_state.authenticated = False
            st.session_state.user_email = None
            st.session_state.user_id = None
            st.session_state.current_page = "auth"
            st.rerun()

    col1, col2 = st.columns([1.1, 0.9], gap="large")

    with col1:
        st.markdown('<div class="soft-card">', unsafe_allow_html=True)
        st.markdown("### Account identity")

        new_username = st.text_input(
            "Choose your username",
            value=username_value,
            placeholder="Example: swayam"
        )

        if st.button("Save Username", use_container_width=True):
            if new_username.strip():
                if update_username(new_username):
                    st.success("Username updated successfully.")
                    st.rerun()
                else:
                    st.error("Could not update username.")
            else:
                st.warning("Username cannot be empty.")

        st.markdown(f"**Email:** {st.session_state.user_email}")
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="soft-card">', unsafe_allow_html=True)
        st.markdown("### Account overview")
        st.markdown(f"**Plan:** {plan.title()}")
        st.markdown(f"**Status:** {subscription.get('status', 'active').title()}")
        st.markdown(f"**Usage Today:** {usage_text}")
        st.markdown('</div>', unsafe_allow_html=True)

def render_lab():
    profile = get_profile()
    username = st.session_state.user_email.split("@")[0]
    if profile and profile.get("username"):
        username = profile["username"]

    usage = get_usage()
    can_generate, plan, used_today, limit = user_can_generate()
    usage_text = f"{used_today}/{limit}" if limit is not None else f"{used_today}/Unlimited"

    st.markdown(f"""
    <div class="hero">
        <div style="font-size:34px;font-weight:800;">🔬 Decision Lab</div>
        <div style="font-size:18px;font-weight:600;margin-top:6px;">
            Premium AI decision analysis, scenario simulation, and downloadable reports
        </div>
        <div style="font-size:14px;opacity:0.9;margin-top:8px;">
            Profile: {username} • Plan: {plan.title()} • Usage Today: {usage_text}
        </div>
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)

    with c1:
        if st.button("← Back Home", use_container_width=True):
            st.session_state.current_page = "home"
            st.rerun()

    with c2:
        if st.button("Open Profile", use_container_width=True):
            st.session_state.current_page = "profile"
            st.rerun()

    with c3:
        if st.button("Logout", use_container_width=True):
            logout_user()
            st.session_state.authenticated = False
            st.session_state.user_email = None
            st.session_state.user_id = None
            st.session_state.current_page = "auth"
            st.rerun()

    if not can_generate:
        st.error("⚠ Daily limit reached for your current plan.")
        st.markdown("Free: 3/day | Pro: 50/day | Premium: Unlimited")

    decision_type = st.selectbox("Decision Type", ["Career", "Business", "Investment", "Life"])
    option_a = st.text_input("Option A (optional)", placeholder="Example: Learn coding first")
    option_b = st.text_input("Option B (optional)", placeholder="Example: Learn marketing first")
    question = st.text_area("Decision Question", placeholder="Example: Should I start a startup or take a job?")

    if st.button("Analyze Decision", type="primary", use_container_width=True):
        if not can_generate:
            st.stop()

        if not question.strip():
            st.warning("Please enter a decision question first.")
            st.stop()

        if option_a.strip() and option_b.strip():
            analysis_prompt = f"""
You are Decedo, an AI Decision Operating System.

Analyze this decision as a strong structured comparison.

Decision Type:
{decision_type}

User question:
{question}

Option A:
{option_a}

Option B:
{option_b}

Respond only in valid JSON.
Do not write markdown.
Do not add explanation outside JSON.

{{
  "comparison_summary": "1 short sentence",
  "ai_1_for_option_a": "1 short paragraph strongly supporting Option A",
  "ai_2_for_option_b": "1 short paragraph strongly supporting Option B",
  "final_opinion": "1 clear final verdict in 1-2 short sentences",
  "option_a_score": "score out of 10",
  "option_b_score": "score out of 10",
  "better_option": "stronger option in 1 short sentence",
  "market_lens": "1 short sentence",
  "execution_lens": "1 short sentence",
  "risk_lens": "1 short sentence",
  "growth_lens": "1 short sentence",
  "confidence_level": "percentage like 85%",
  "risk_comparison": "Low or Medium or High",
  "why": ["point 1", "point 2"],
  "first_next_step": "1 practical next action"
}}
"""
        else:
            analysis_prompt = f"""
You are Decedo, an AI Decision Operating System.

Analyze the user's decision clearly and briefly.

Decision Type:
{decision_type}

User question:
{question}

Respond only in valid JSON.
Do not write markdown.
Do not add explanation outside JSON.

{{
  "decision_summary": "1 short sentence",
  "best_option": "best choice in 1 short sentence",
  "final_opinion": "1 clear final verdict in 1-2 short sentences",
  "market_lens": "1 short sentence",
  "execution_lens": "1 short sentence",
  "risk_lens": "1 short sentence",
  "growth_lens": "1 short sentence",
  "confidence_level": "percentage like 85%",
  "risk_level": "Low or Medium or High",
  "decision_score": "score out of 10",
  "why": ["point 1", "point 2"],
  "first_next_step": "1 practical next action"
}}
"""

        try:
            with st.spinner("Analyzing your decision..."):
                analysis_response = gemini_client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=analysis_prompt,
                )

            analysis_data = parse_json_response(analysis_response.text)

            summary = analysis_data.get("decision_summary", analysis_data.get("comparison_summary", "Not available"))
            best_option = analysis_data.get("best_option", analysis_data.get("better_option", "Not available"))
            risk_level = analysis_data.get("risk_level", analysis_data.get("risk_comparison", "Not available"))
            confidence_level = analysis_data.get("confidence_level", "Not available")
            next_step = analysis_data.get("first_next_step", "Not available")
            final_opinion = analysis_data.get("final_opinion", "Not available")

            ai_1_argument = analysis_data.get("ai_1_for_option_a", "")
            ai_2_argument = analysis_data.get("ai_2_for_option_b", "")

            option_a_score = analysis_data.get("option_a_score", "")
            option_b_score = analysis_data.get("option_b_score", "")
            decision_score = analysis_data.get("decision_score", option_a_score if option_a_score else "Not available")

            decision_grade = calculate_grade(decision_score)

            market_lens = analysis_data.get("market_lens", "")
            execution_lens = analysis_data.get("execution_lens", "")
            risk_lens = analysis_data.get("risk_lens", "")
            growth_lens = analysis_data.get("growth_lens", "")
            why_points = analysis_data.get("why", [])

            if option_a.strip() and option_b.strip():
                scenario_prompt = f"""
You are Decedo, an AI strategic simulation engine.

Decision Type:
{decision_type}

User question:
{question}

Option A:
{option_a}

Option B:
{option_b}

Existing decision summary:
{summary}

Respond only in valid JSON.
Do not write markdown.
Do not add explanation outside JSON.

{{
  "option_a_future": {{
    "3_months": "1 short sentence",
    "1_year": "1 short sentence",
    "5_years": "1 short sentence"
  }},
  "option_b_future": {{
    "3_months": "1 short sentence",
    "1_year": "1 short sentence",
    "5_years": "1 short sentence"
  }},
  "strategic_insight": "1 powerful strategic insight in 1-2 short sentences"
}}
"""
            else:
                scenario_prompt = f"""
You are Decedo, an AI strategic simulation engine.

Decision Type:
{decision_type}

User question:
{question}

Existing decision summary:
{summary}

Respond only in valid JSON.
Do not write markdown.
Do not add explanation outside JSON.

{{
  "recommended_path_future": {{
    "3_months": "1 short sentence",
    "1_year": "1 short sentence",
    "5_years": "1 short sentence"
  }},
  "strategic_insight": "1 powerful strategic insight in 1-2 short sentences"
}}
"""

            with st.spinner("Simulating future outcomes..."):
                scenario_response = gemini_client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=scenario_prompt,
                )

            scenario_data = parse_json_response(scenario_response.text)

            option_a_future = scenario_data.get("option_a_future", {})
            option_b_future = scenario_data.get("option_b_future", {})
            recommended_path_future = scenario_data.get("recommended_path_future", {})
            strategic_insight = scenario_data.get("strategic_insight", "Not available")

            save_report(question, decision_type, option_a, option_b, analysis_data, scenario_data)

            # Refresh usage after saving
            refreshed_usage = get_usage()
            refreshed_used_today = int(refreshed_usage.get("reports_today", 0) or 0)
            refreshed_usage_text = f"{refreshed_used_today}/{limit}" if limit is not None else f"{refreshed_used_today}/Unlimited"

            st.session_state.history.append({
                "question": question,
                "answer": {
                    "analysis": analysis_data,
                    "scenario": scenario_data
                }
            })

            st.success(f"Report saved successfully. Usage Today: {refreshed_usage_text}")

            # =====================================
            # DASHBOARD
            # =====================================
            st.markdown("## 📊 Decision Dashboard")
            st.info(summary)

            if option_a_score and option_b_score:
                s1, s2 = st.columns(2)
                with s1:
                    st.metric("Option A Score", option_a_score)
                    if option_a:
                        st.caption(option_a)
                with s2:
                    st.metric("Option B Score", option_b_score)
                    if option_b:
                        st.caption(option_b)

            m1, m2, m3, m4, m5 = st.columns(5)
            m1.metric("Best Choice", best_option)
            m2.metric("Risk Level", risk_level)
            m3.metric("Score", decision_score)
            m4.metric("Confidence", confidence_level)
            m5.metric("Grade", decision_grade)

            # =====================================
            # CONFIDENCE METER
            # =====================================
            st.markdown("### Confidence Meter")
            confidence_value = confidence_to_int(confidence_level)
            st.progress(confidence_value)
            st.caption(f"AI confidence: {confidence_value}%")

            # =====================================
            # AI 1 VS AI 2
            # =====================================
            if ai_1_argument or ai_2_argument:
                st.markdown("## ⚔️ AI 1 vs AI 2")
                d1, d2 = st.columns(2)

                with d1:
                    st.markdown('<div class="debate-box">', unsafe_allow_html=True)
                    st.markdown("### AI 1 — Argument for Option A")
                    if option_a:
                        st.write(f"**{option_a}**")
                    st.write(ai_1_argument if ai_1_argument else "Not available")
                    st.markdown('</div>', unsafe_allow_html=True)

                with d2:
                    st.markdown('<div class="debate-box">', unsafe_allow_html=True)
                    st.markdown("### AI 2 — Argument for Option B")
                    if option_b:
                        st.write(f"**{option_b}**")
                    st.write(ai_2_argument if ai_2_argument else "Not available")
                    st.markdown('</div>', unsafe_allow_html=True)

            # =====================================
            # FINAL OPINION
            # =====================================
            st.markdown("## 🧠 Final Opinion")
            st.markdown('<div class="judge-box">', unsafe_allow_html=True)
            st.write(final_opinion)
            st.markdown('</div>', unsafe_allow_html=True)

            # =====================================
            # LENSES
            # =====================================
            st.markdown("### Decision Lenses")
            l1, l2 = st.columns(2)
            with l1:
                st.write(f"**Market Lens:** {market_lens}")
                st.write(f"**Execution Lens:** {execution_lens}")
            with l2:
                st.write(f"**Risk Lens:** {risk_lens}")
                st.write(f"**Growth Lens:** {growth_lens}")

            # =====================================
            # WHY
            # =====================================
            if why_points:
                st.markdown("### Why")
                for point in why_points:
                    st.write(f"- {point}")

            # =====================================
            # NEXT STEP
            # =====================================
            st.markdown("### First Next Step")
            st.success(next_step)

            # =====================================
            # STRATEGIC INSIGHT
            # =====================================
            st.markdown("### Strategic Insight")
            st.success(strategic_insight)

            # =====================================
            # SCENARIO SIMULATION
            # =====================================
            if option_a_future and option_b_future:
                st.markdown("## 🔮 Scenario Simulation")
                s1, s2 = st.columns(2)

                with s1:
                    st.markdown("### Option A Future")
                    st.write(f"**{option_a}**")
                    st.write(f"**3 Months:** {option_a_future.get('3_months', 'Not available')}")
                    st.write(f"**1 Year:** {option_a_future.get('1_year', 'Not available')}")
                    st.write(f"**5 Years:** {option_a_future.get('5_years', 'Not available')}")

                with s2:
                    st.markdown("### Option B Future")
                    st.write(f"**{option_b}**")
                    st.write(f"**3 Months:** {option_b_future.get('3_months', 'Not available')}")
                    st.write(f"**1 Year:** {option_b_future.get('1_year', 'Not available')}")
                    st.write(f"**5 Years:** {option_b_future.get('5_years', 'Not available')}")

            elif recommended_path_future:
                st.markdown("## 🔮 Scenario Simulation")
                st.write(f"**3 Months:** {recommended_path_future.get('3_months', 'Not available')}")
                st.write(f"**1 Year:** {recommended_path_future.get('1_year', 'Not available')}")
                st.write(f"**5 Years:** {recommended_path_future.get('5_years', 'Not available')}")

            # =====================================
            # PDF
            # =====================================
            pdf_bytes = create_pdf_report(
                question=question,
                decision_type=decision_type,
                summary=summary,
                best_option=best_option,
                risk_level=risk_level,
                decision_score=str(decision_score),
                confidence_level=str(confidence_level),
                decision_grade=decision_grade,
                market_lens=market_lens,
                execution_lens=execution_lens,
                risk_lens=risk_lens,
                growth_lens=growth_lens,
                why_points=why_points,
                next_step=next_step,
                strategic_insight=strategic_insight,
                final_opinion=final_opinion,
                ai_1_argument=ai_1_argument,
                ai_2_argument=ai_2_argument,
                option_a=option_a,
                option_b=option_b,
                option_a_future=option_a_future,
                option_b_future=option_b_future,
                recommended_path_future=recommended_path_future
            )

            st.download_button(
                label="Download Decision Report (PDF)",
                data=pdf_bytes,
                file_name="decedo_decision_report.pdf",
                mime="application/pdf",
                use_container_width=True
            )

        except Exception as e:
            st.error(f"Real error: {e}")

# =========================================================
# ROUTER
# =========================================================
if not st.session_state.authenticated:
    render_auth()
elif st.session_state.current_page == "home":
    render_home()
elif st.session_state.current_page == "profile":
    render_profile()
elif st.session_state.current_page == "lab":
    render_lab()
else:
    render_home()
