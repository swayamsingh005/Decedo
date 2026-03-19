import json
import re
from datetime import datetime
from zoneinfo import ZoneInfo

import streamlit as st
from fpdf import FPDF
from google import genai
from supabase import Client, create_client


# =========================================================
# PAGE CONFIG
# =========================================================
st.set_page_config(
    page_title="Decedo",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# =========================================================
# PREMIUM UI
# =========================================================
st.markdown(
    """
<style>
    :root {
        --bg-main: #f5f8ff;
        --bg-soft: #eef4ff;
        --card: rgba(255,255,255,0.92);
        --card-solid: #ffffff;
        --text: #0f172a;
        --muted: #64748b;
        --border: rgba(15, 23, 42, 0.08);
        --primary: #2563eb;
        --primary-2: #7c3aed;
        --accent: #ec4899;
        --danger: #ef4444;
        --danger-2: #f43f5e;
        --success: #16a34a;
        --warning: #f59e0b;
    }

    .main {
        background:
            radial-gradient(circle at 8% 8%, rgba(37,99,235,0.09), transparent 24%),
            radial-gradient(circle at 92% 10%, rgba(124,58,237,0.08), transparent 22%),
            radial-gradient(circle at 50% 100%, rgba(236,72,153,0.05), transparent 18%),
            linear-gradient(180deg, #f8fbff 0%, #eef4ff 100%);
    }

    .block-container {
        max-width: 1260px;
        padding-top: 1.3rem;
        padding-bottom: 2.2rem;
    }

    .hero {
        position: relative;
        overflow: hidden;
        background:
            radial-gradient(circle at top right, rgba(255,255,255,0.16), transparent 28%),
            linear-gradient(135deg, #0b1020 0%, #10214a 48%, #6d28d9 100%);
        color: white;
        border-radius: 32px;
        padding: 38px 36px;
        border: 1px solid rgba(255,255,255,0.08);
        box-shadow: 0 26px 72px rgba(15,23,42,0.22);
        margin-bottom: 24px;
    }

    .hero::before {
        content: "";
        position: absolute;
        width: 320px;
        height: 320px;
        right: -90px;
        top: -90px;
        border-radius: 50%;
        background: radial-gradient(circle, rgba(255,255,255,0.12), transparent 65%);
    }

    .hero::after {
        content: "";
        position: absolute;
        width: 220px;
        height: 220px;
        left: -40px;
        bottom: -90px;
        border-radius: 50%;
        background: radial-gradient(circle, rgba(59,130,246,0.20), transparent 70%);
    }

    .glass-card {
        background: rgba(255,255,255,0.84);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(255,255,255,0.70);
        border-radius: 26px;
        padding: 24px;
        box-shadow: 0 16px 40px rgba(15,23,42,0.08);
        margin-bottom: 18px;
    }

    .solid-card {
        background: linear-gradient(180deg, #ffffff 0%, #f8fbff 100%);
        border: 1px solid #e5e7eb;
        border-radius: 26px;
        padding: 24px;
        box-shadow: 0 16px 40px rgba(15,23,42,0.08);
        margin-bottom: 18px;
    }

    .nav-card {
        background: linear-gradient(180deg, #ffffff 0%, #f8fbff 100%);
        border: 1px solid #e5e7eb;
        border-radius: 26px;
        padding: 28px 22px;
        min-height: 225px;
        text-align: center;
        box-shadow: 0 16px 40px rgba(15,23,42,0.08);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }

    .nav-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 22px 48px rgba(15,23,42,0.11);
    }

    .tier-card {
        background: linear-gradient(180deg, #ffffff 0%, #f8fbff 100%);
        border-radius: 28px;
        padding: 26px;
        border: 1px solid #e5e7eb;
        min-height: 540px;
        box-shadow: 0 16px 40px rgba(15,23,42,0.08);
    }

    .tier-card.pro {
        border: 1px solid rgba(37,99,235,0.28);
        box-shadow: 0 22px 52px rgba(37,99,235,0.14);
        transform: translateY(-6px);
    }

    .tier-card.premium {
        border: 1px solid rgba(124,58,237,0.28);
        box-shadow: 0 22px 52px rgba(124,58,237,0.16);
    }

    .badge-free, .badge-pro, .badge-premium {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 8px 14px;
        border-radius: 999px;
        font-size: 12px;
        font-weight: 800;
        letter-spacing: 0.02em;
        color: white;
        margin-bottom: 14px;
    }

    .badge-free {
        background: linear-gradient(135deg, #475569, #64748b);
    }

    .badge-pro {
        background: linear-gradient(135deg, #2563eb, #3b82f6);
    }

    .badge-premium {
        background: linear-gradient(135deg, #7c3aed, #a855f7);
    }

    .pill {
        display: inline-flex;
        padding: 8px 13px;
        border-radius: 999px;
        font-size: 12px;
        font-weight: 800;
        margin-bottom: 14px;
    }

    .pill.free {
        background: rgba(71,85,105,0.12);
        color: #334155;
    }

    .pill.pro {
        background: rgba(37,99,235,0.12);
        color: #1d4ed8;
    }

    .pill.premium {
        background: rgba(124,58,237,0.12);
        color: #7c3aed;
    }

    .price-big {
        font-size: 50px;
        line-height: 1;
        font-weight: 900;
        letter-spacing: -0.05em;
        color: #0f172a;
        margin-bottom: 10px;
    }

    .price-big span {
        font-size: 15px;
        color: #64748b;
        font-weight: 700;
        margin-left: 5px;
    }

    .section-title {
        font-size: 31px;
        font-weight: 900;
        letter-spacing: -0.03em;
        color: #0f172a;
        margin-bottom: 8px;
    }

    .small-muted {
        color: #64748b;
        font-size: 14px;
    }

    .plan-divider {
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(148,163,184,0.35), transparent);
        margin: 14px 0 12px 0;
    }

    .unlock-panel {
        background: linear-gradient(135deg, rgba(37,99,235,0.06), rgba(236,72,153,0.04));
        border: 1px solid rgba(37,99,235,0.10);
        border-radius: 18px;
        padding: 16px;
    }

    .feature-note {
        padding: 12px 14px;
        border-radius: 14px;
        background: rgba(37,99,235,0.06);
        border: 1px solid rgba(37,99,235,0.10);
        color: #1e293b;
        font-size: 14px;
    }

    .debate-box {
        background: linear-gradient(180deg, #ffffff 0%, #f8fbff 100%);
        border: 1px solid #dbeafe;
        border-radius: 20px;
        padding: 18px;
        margin-bottom: 14px;
        box-shadow: 0 8px 20px rgba(15,23,42,0.04);
    }

    .judge-box {
        background: linear-gradient(180deg, #f0fdf4 0%, #ecfeff 100%);
        border: 1px solid #bbf7d0;
        border-radius: 20px;
        padding: 18px;
        margin-bottom: 14px;
        box-shadow: 0 8px 20px rgba(15,23,42,0.04);
    }

    .premium-panel {
        background: linear-gradient(135deg, rgba(124,58,237,0.08), rgba(37,99,235,0.06));
        border: 1px solid rgba(124,58,237,0.16);
        border-radius: 20px;
        padding: 18px;
        margin-bottom: 14px;
        box-shadow: 0 8px 22px rgba(124,58,237,0.06);
    }

    .exec-panel {
        background: linear-gradient(135deg, rgba(15,23,42,0.04), rgba(37,99,235,0.05));
        border: 1px solid rgba(15,23,42,0.08);
        border-radius: 20px;
        padding: 18px;
        margin-bottom: 14px;
    }

    .stButton > button {
        border-radius: 16px !important;
        font-weight: 800 !important;
        height: 3.15em !important;
        border: none !important;
    }

    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #ef4444 0%, #f43f5e 100%) !important;
        color: white !important;
        box-shadow: 0 10px 24px rgba(239,68,68,0.18);
    }

    .stButton > button[kind="secondary"] {
        background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%) !important;
        color: #0f172a !important;
        border: 1px solid #e5e7eb !important;
        box-shadow: 0 8px 20px rgba(15,23,42,0.06);
    }

    .stTextInput > div > div > input,
    .stTextArea textarea,
    .stSelectbox > div > div {
        border-radius: 14px !important;
        border: 1px solid #dbe4f0 !important;
    }

    div[data-testid="stMetric"] {
        background: linear-gradient(180deg, #ffffff 0%, #f8fbff 100%);
        border: 1px solid #e5e7eb;
        padding: 14px;
        border-radius: 18px;
        box-shadow: 0 8px 18px rgba(15,23,42,0.05);
    }
</style>
""",
    unsafe_allow_html=True,
)

# =========================================================
# CONFIG
# =========================================================
APP_NAME = "Decedo"
INDIA_TZ = ZoneInfo("Asia/Kolkata")

PLAN_CONFIG = {
    "free": {
        "label": "Free",
        "price": "₹0",
        "limit": 3,
        "show_debate": False,
        "show_scenarios": False,
        "show_strategic_insight": False,
        "show_confidence_meter": False,
        "show_hidden_risks": False,
        "show_opportunity_cost": False,
        "show_success_drivers": False,
        "show_roadmap": False,
        "show_exec_summary": False,
        "pdf_name": "Basic Report",
        "features": [
            "3 decisions per day",
            "basic recommendation",
            "basic dashboard",
            "basic PDF report",
        ],
    },
    "pro": {
        "label": "Pro",
        "price": "₹599",
        "limit": 50,
        "show_debate": True,
        "show_scenarios": True,
        "show_strategic_insight": True,
        "show_confidence_meter": True,
        "show_hidden_risks": True,
        "show_opportunity_cost": False,
        "show_success_drivers": True,
        "show_roadmap": False,
        "show_exec_summary": True,
        "pdf_name": "Pro Insight Report",
        "features": [
            "50 decisions per day",
            "AI 1 vs AI 2 debate",
            "confidence meter",
            "strategic insight",
            "full simulation",
            "hidden risks analysis",
            "success drivers",
            "enhanced PDF report",
        ],
    },
    "premium": {
        "label": "Premium",
        "price": "₹1499",
        "limit": None,
        "show_debate": True,
        "show_scenarios": True,
        "show_strategic_insight": True,
        "show_confidence_meter": True,
        "show_hidden_risks": True,
        "show_opportunity_cost": True,
        "show_success_drivers": True,
        "show_roadmap": True,
        "show_exec_summary": True,
        "pdf_name": "Premium Executive Report",
        "features": [
            "Unlimited decisions",
            "AI debate + final verdict",
            "confidence meter",
            "strategic insight",
            "full simulation",
            "hidden risks analysis",
            "opportunity cost analysis",
            "success drivers",
            "30-day roadmap",
            "premium executive PDF",
        ],
    },
}

# =========================================================
# CLIENTS
# =========================================================
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_ANON_KEY = st.secrets["SUPABASE_ANON_KEY"]
SUPABASE_SERVICE_ROLE_KEY = st.secrets["SUPABASE_SERVICE_ROLE_KEY"]
GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]

supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
admin_supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
gemini_client = genai.Client(api_key=GEMINI_API_KEY)

# =========================================================
# SESSION
# =========================================================
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "current_page" not in st.session_state:
    st.session_state.current_page = "auth"
if "user_email" not in st.session_state:
    st.session_state.user_email = None
if "user_id" not in st.session_state:
    st.session_state.user_id = None

# =========================================================
# AUTH
# =========================================================
def login_user(email: str, password: str):
    try:
        result = supabase.auth.sign_in_with_password({"email": email, "password": password})
        return True, result
    except Exception as e:
        return False, str(e)


def signup_user(email: str, password: str):
    try:
        result = supabase.auth.sign_up({"email": email, "password": password})
        return True, result
    except Exception as e:
        return False, str(e)


def logout_user():
    try:
        supabase.auth.sign_out()
    except Exception:
        pass


# =========================================================
# HELPERS
# =========================================================
def now_iso():
    return datetime.now(INDIA_TZ).isoformat()


def clean_pdf_text(text):
    text = str(text)
    replacements = {
        "₹": "Rs. ",
        "–": "-",
        "—": "-",
        "’": "'",
        "‘": "'",
        "“": '"',
        "”": '"',
        "•": "-",
        "→": "->",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


def parse_json_response(raw_text: str) -> dict:
    text = raw_text.strip().replace("```json", "").replace("```", "").strip()

    try:
        return json.loads(text)
    except Exception:
        pass

    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        candidate = match.group(0)
        candidate = candidate.replace("“", '"').replace("”", '"')
        candidate = candidate.replace("‘", "'").replace("’", "'")
        candidate = re.sub(r",\s*([}\]])", r"\1", candidate)
        return json.loads(candidate)

    raise ValueError("AI returned invalid JSON")


def safe_generate_json(prompt: str, error_title: str) -> dict:
    response = gemini_client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )
    raw_text = response.text if hasattr(response, "text") else str(response)

    try:
        return parse_json_response(raw_text)
    except Exception:
        st.error(error_title)
        st.code(raw_text)
        st.stop()


def calculate_grade(score):
    try:
        score = float(str(score).replace("/10", "").strip())
    except Exception:
        return "N/A"

    if score >= 9:
        return "A+"
    if score >= 8:
        return "A"
    if score >= 7:
        return "B"
    if score >= 6:
        return "C"
    return "D"


def confidence_to_int(confidence_text):
    try:
        text = str(confidence_text).replace("%", "").strip()
        return max(0, min(100, int(float(text))))
    except Exception:
        return 0


def format_usage(used, limit):
    return f"{used}/Unlimited" if limit is None else f"{used}/{limit}"


def get_plan_features(plan: str):
    return PLAN_CONFIG.get(plan, PLAN_CONFIG["free"])


# =========================================================
# DATABASE
# =========================================================
def get_profile():
    result = (
        admin_supabase.table("profiles")
        .select("*")
        .eq("user_id", st.session_state.user_id)
        .limit(1)
        .execute()
    )
    return result.data[0] if result.data else None


def ensure_profile():
    existing = get_profile()
    if existing:
        return existing

    payload = {
        "user_id": st.session_state.user_id,
        "email": st.session_state.user_email,
        "username": "",
    }
    admin_supabase.table("profiles").upsert(payload).execute()
    return get_profile()
def save_decision_history(question, decision_type, option_a, option_b, selected_option):
    admin_supabase.table("decision_history").insert({
        "user_id": st.session_state.user_id,
        "question": question,
        "decision_type": decision_type,
        "option_a": option_a if option_a else None,
        "option_b": option_b if option_b else None,
        "selected_option": selected_option
    }).execute()

def update_username(username: str):
    admin_supabase.table("profiles").update(
        {"username": username.strip()}
    ).eq("user_id", st.session_state.user_id).execute()
    return True


def get_subscription():
    result = (
        admin_supabase.table("subscriptions")
        .select("*")
        .eq("user_id", st.session_state.user_id)
        .limit(1)
        .execute()
    )

    if result.data:
        row = result.data[0]
        row["plan"] = str(row.get("plan", "free")).strip().lower()
        row["status"] = str(row.get("status", "active")).strip().lower()
        return row

    payload = {
        "user_id": st.session_state.user_id,
        "plan": "free",
        "status": "active",
    }
    admin_supabase.table("subscriptions").insert(payload).execute()
    return payload


def ensure_subscription():
    return get_subscription()


def set_plan_for_testing(plan: str):
    plan = str(plan).strip().lower()
    if plan not in PLAN_CONFIG:
        raise ValueError("Invalid plan")

    admin_supabase.table("subscriptions").upsert(
        {
            "user_id": st.session_state.user_id,
            "plan": plan,
            "status": "active",
        }
    ).execute()
    return True


def get_or_create_usage():
    result = (
        admin_supabase.table("usage_tracking")
        .select("*")
        .eq("user_id", st.session_state.user_id)
        .limit(1)
        .execute()
    )

    if result.data:
        row = result.data[0]
        if row.get("reports_today") is None:
            row["reports_today"] = 0
        return row

    payload = {
        "user_id": st.session_state.user_id,
        "reports_today": 0,
        "last_reset": now_iso(),
    }
    admin_supabase.table("usage_tracking").insert(payload).execute()
    return payload


def reset_usage_if_new_day():
    usage = get_or_create_usage()
    now = datetime.now(INDIA_TZ)
    today = now.date()

    try:
        last_reset_date = datetime.fromisoformat(
            str(usage["last_reset"]).replace("Z", "+00:00")
        ).astimezone(INDIA_TZ).date()
    except Exception:
        last_reset_date = today

    if last_reset_date != today:
        admin_supabase.table("usage_tracking").update(
            {"reports_today": 0, "last_reset": now_iso()}
        ).eq("user_id", st.session_state.user_id).execute()
        usage["reports_today"] = 0
        usage["last_reset"] = now_iso()

    return usage


def get_usage():
    return reset_usage_if_new_day()


def increment_usage():
    usage = get_or_create_usage()
    current = int(usage.get("reports_today", 0) or 0)

    admin_supabase.table("usage_tracking").update(
        {"reports_today": current + 1, "last_reset": now_iso()}
    ).eq("user_id", st.session_state.user_id).execute()


def save_report(question, decision_type, option_a, option_b, plan, report_data):
    normalized_plan = str(plan).strip().lower()

    admin_supabase.table("reports").insert(
        {
            "user_id": st.session_state.user_id,
            "decision_type": decision_type,
            "question": question,
            "option_a": option_a if option_a else None,
            "option_b": option_b if option_b else None,
            "plan": normalized_plan,
            "analysis": report_data,
        }
    ).execute()

    increment_usage()


# =========================================================
# PDF
# =========================================================
class DecedoPDF(FPDF):
    def footer(self):
        self.set_y(-12)
        self.set_font("Arial", "I", 9)
        self.set_text_color(100, 116, 139)
        self.cell(0, 8, f"Page {self.page_no()}", align="C")


def section(pdf, title, body, accent=(37, 99, 235)):
    if not body:
        return
    pdf.set_text_color(*accent)
    pdf.set_font("Arial", "B", 13)
    pdf.cell(0, 8, clean_pdf_text(title), ln=True)
    pdf.set_text_color(20, 24, 39)
    pdf.set_font("Arial", "", 11)
    pdf.multi_cell(0, 7, clean_pdf_text(body))
    pdf.ln(2)


def bullet_section(pdf, title, items, accent=(37, 99, 235)):
    if not items:
        return
    pdf.set_text_color(*accent)
    pdf.set_font("Arial", "B", 13)
    pdf.cell(0, 8, clean_pdf_text(title), ln=True)
    pdf.set_text_color(20, 24, 39)
    pdf.set_font("Arial", "", 11)
    for item in items:
        pdf.multi_cell(0, 7, clean_pdf_text(f"- {item}"))
    pdf.ln(2)


def create_plan_pdf(report: dict, plan: str):
    pdf = DecedoPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    if plan == "premium":
        accent = (124, 58, 237)
        report_name = "Premium Executive Report"
    elif plan == "pro":
        accent = (37, 99, 235)
        report_name = "Pro Insight Report"
    else:
        accent = (71, 85, 105)
        report_name = "Basic Report"

    pdf.set_fill_color(*accent)
    pdf.rect(0, 0, 210, 28, style="F")
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", "B", 19)
    pdf.set_xy(10, 9)
    pdf.cell(0, 8, clean_pdf_text(f"{APP_NAME} - {report_name}"))

    pdf.ln(20)
    pdf.set_text_color(20, 24, 39)
    pdf.set_font("Arial", "", 11)
    pdf.cell(
        0,
        8,
        clean_pdf_text(
            f"Generated: {datetime.now(INDIA_TZ).strftime('%d %b %Y, %I:%M %p IST')}"
        ),
        ln=True,
    )
    pdf.cell(0, 8, clean_pdf_text(f"Plan: {plan.title()}"), ln=True)
    pdf.ln(2)

    section(pdf, "Decision Type", report.get("decision_type"), accent)
    section(pdf, "Decision Question", report.get("question"), accent)

    if report.get("executive_summary"):
        section(pdf, "Executive Summary", report.get("executive_summary"), accent)

    section(pdf, "Summary", report.get("summary"), accent)
    section(pdf, "Best Choice", report.get("best_option"), accent)
    section(pdf, "Risk Level", report.get("risk_level"), accent)
    section(pdf, "Decision Score", str(report.get("decision_score")), accent)
    section(pdf, "Confidence", str(report.get("confidence_level")), accent)
    section(pdf, "Decision Grade", report.get("decision_grade"), accent)

    if plan in ("pro", "premium"):
        section(pdf, "AI 1 - Argument for Option A", report.get("ai_1_argument"), accent)
        section(pdf, "AI 2 - Argument for Option B", report.get("ai_2_argument"), accent)
        section(pdf, "Final Opinion", report.get("final_opinion"), accent)

    section(pdf, "Market Lens", report.get("market_lens"), accent)
    section(pdf, "Execution Lens", report.get("execution_lens"), accent)
    section(pdf, "Risk Lens", report.get("risk_lens"), accent)
    section(pdf, "Growth Lens", report.get("growth_lens"), accent)
    bullet_section(pdf, "Why", report.get("why_points"), accent)
    section(pdf, "First Next Step", report.get("next_step"), accent)

    if plan in ("pro", "premium"):
        section(pdf, "Strategic Insight", report.get("strategic_insight"), accent)

    if plan == "premium":
        bullet_section(pdf, "Hidden Risks", report.get("hidden_risks"), accent)
        section(pdf, "Opportunity Cost", report.get("opportunity_cost"), accent)
        bullet_section(pdf, "Success Drivers", report.get("success_drivers"), accent)
        bullet_section(pdf, "30-Day Action Roadmap", report.get("roadmap_30_days"), accent)

    pdf.set_text_color(*accent)
    pdf.set_font("Arial", "B", 13)
    pdf.cell(0, 8, "Scenario Simulation", ln=True)
    pdf.set_text_color(20, 24, 39)
    pdf.set_font("Arial", "", 11)

    if report.get("option_a_future") and report.get("option_b_future"):
        oaf = report["option_a_future"]
        obf = report["option_b_future"]

        pdf.multi_cell(0, 7, clean_pdf_text(f"Option A Future: {report.get('option_a', '')}"))
        for k in ["3_months", "1_year", "5_years"]:
            if k in oaf:
                pdf.multi_cell(0, 7, clean_pdf_text(f"{k.replace('_', ' ').title()}: {oaf[k]}"))
        pdf.ln(1)

        pdf.multi_cell(0, 7, clean_pdf_text(f"Option B Future: {report.get('option_b', '')}"))
        for k in ["3_months", "1_year", "5_years"]:
            if k in obf:
                pdf.multi_cell(0, 7, clean_pdf_text(f"{k.replace('_', ' ').title()}: {obf[k]}"))
        pdf.ln(1)

    elif report.get("recommended_path_future"):
        rpf = report["recommended_path_future"]
        for k, v in rpf.items():
            pdf.multi_cell(0, 7, clean_pdf_text(f"{k.replace('_', ' ').title()}: {v}"))

    return pdf.output(dest="S").encode("latin-1")


# =========================================================
# UI HELPERS
# =========================================================
def render_plan_badge(plan: str):
    if plan == "premium":
        st.markdown('<div class="badge-premium">Premium</div>', unsafe_allow_html=True)
    elif plan == "pro":
        st.markdown('<div class="badge-pro">Pro</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="badge-free">Free</div>', unsafe_allow_html=True)


def render_top_nav():
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        if st.button("← Back Home", use_container_width=True, type="primary", key="nav_home"):
            st.session_state.current_page = "home"
            st.rerun()
    with c2:
        if st.button("Open Profile", use_container_width=True, type="primary", key="nav_profile"):
            st.session_state.current_page = "profile"
            st.rerun()
    with c3:
        if st.button("Pricing", use_container_width=True, type="primary", key="nav_pricing"):
            st.session_state.current_page = "pricing"
            st.rerun()
    with c4:
        if st.button("Logout", use_container_width=True, type="primary", key="nav_logout"):
            logout_user()
            st.session_state.authenticated = False
            st.session_state.user_email = None
            st.session_state.user_id = None
            st.session_state.current_page = "auth"
            st.rerun()


# =========================================================
# PAGES
# =========================================================
def render_auth():
    st.markdown(
        """
        <div class="hero">
            <div style="font-size:42px;font-weight:900;letter-spacing:-0.04em;">Decedo</div>
            <div style="font-size:21px;font-weight:800;margin-top:6px;">
                AI Decision Operating System
            </div>
            <div style="font-size:15px;opacity:0.96;margin-top:10px;max-width:760px;">
                Structured reasoning, AI debate, scenario simulation, strategic insight, and premium-tier decision reports.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    left, right = st.columns([1.08, 0.92], gap="large")

    with left:
        st.markdown(
            """
            <div class="glass-card">
                <div class="section-title">Why Decedo feels premium</div>
                <p>• AI decision intelligence dashboard</p>
                <p>• plan-aware differentiation across Free, Pro, and Premium</p>
                <p>• stronger strategic insights and tiered premium reports</p>
                <p>• SaaS-ready structure before payment integration</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with right:
        st.markdown('<div class="solid-card">', unsafe_allow_html=True)
        tab1, tab2 = st.tabs(["Login", "Create Account"])

        with tab1:
            st.markdown("### Welcome back")
            login_email = st.text_input("Email", key="login_email")
            login_password = st.text_input("Password", type="password", key="login_password")

            if st.button("Login", type="primary", use_container_width=True, key="login_btn"):
                ok, result = login_user(login_email, login_password)
                if ok and result.user:
                    st.session_state.authenticated = True
                    st.session_state.user_email = result.user.email
                    st.session_state.user_id = result.user.id

                    ensure_profile()
                    ensure_subscription()
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

            if st.button("Create Account", type="primary", use_container_width=True, key="signup_btn"):
                if signup_password != signup_confirm:
                    st.error("Passwords do not match.")
                else:
                    ok, result = signup_user(signup_email, signup_password)
                    if ok:
                        st.success("Account created. Now login.")
                    else:
                        st.error(str(result))

        st.markdown("</div>", unsafe_allow_html=True)


def render_home():
    sub = get_subscription()
    plan = str(sub.get("plan", "free")).strip().lower()
    plan_info = get_plan_features(plan)
    usage = get_usage()
    used_today = int(usage.get("reports_today", 0) or 0)
    usage_text = format_usage(used_today, plan_info["limit"])

    st.markdown(
        """
        <div class="hero">
            <div style="font-size:42px;font-weight:900;letter-spacing:-0.04em;">Decedo</div>
            <div style="font-size:21px;font-weight:800;margin-top:6px;">
                AI Decision Operating System
            </div>
            <div style="font-size:15px;opacity:0.96;margin-top:10px;max-width:760px;">
                Premium AI decision intelligence for ambitious people.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    render_plan_badge(plan)
    st.success(f"Logged in as {st.session_state.user_email}")
    st.info(f"Plan: {plan.title()} • Usage Today: {usage_text}")

    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric("Current Plan", plan.title())
    with m2:
        st.metric("Usage Today", usage_text)
    with m3:
        st.metric("PDF Tier", plan_info["pdf_name"])

    c1, c2, c3 = st.columns(3, gap="large")

    with c1:
        st.markdown(
            """
            <div class="nav-card">
                <div style="font-size:34px;">👤</div>
                <h3 style="margin-top:8px;">Profile</h3>
                <p style="color:#64748b;">Manage username, plan, and account overview.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("Open Profile", use_container_width=True, type="primary", key="home_profile_btn"):
            st.session_state.current_page = "profile"
            st.rerun()

    with c2:
        st.markdown(
            """
            <div class="nav-card">
                <div style="font-size:34px;">🔬</div>
                <h3 style="margin-top:8px;">Decision Lab</h3>
                <p style="color:#64748b;">Run plan-aware analysis, simulation, and premium reports.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("Open Decision Lab", use_container_width=True, type="primary", key="home_lab_btn"):
            st.session_state.current_page = "lab"
            st.rerun()

    with c3:
        st.markdown(
            """
            <div class="nav-card">
                <div style="font-size:34px;">💳</div>
                <h3 style="margin-top:8px;">Pricing</h3>
                <p style="color:#64748b;">See Free, Pro, and Premium value architecture.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("View Pricing", use_container_width=True, type="primary", key="home_pricing_btn"):
            st.session_state.current_page = "pricing"
            st.rerun()


def render_profile():
    profile = ensure_profile()
    sub = get_subscription()
    plan = str(sub.get("plan", "free")).strip().lower()
    plan_info = get_plan_features(plan)
    usage = get_usage()
    used_today = int(usage.get("reports_today", 0) or 0)
    usage_text = format_usage(used_today, plan_info["limit"])

    username_value = profile["username"] if profile and profile.get("username") else ""

    st.markdown(
        f"""
        <div class="hero">
            <div style="font-size:38px;font-weight:900;">Profile</div>
            <div style="font-size:19px;font-weight:800;margin-top:6px;">
                {username_value if username_value else "Set your Decedo username"}
            </div>
            <div style="font-size:14px;opacity:0.95;margin-top:8px;">
                Manage identity, plan, and usage.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    render_top_nav()

    left, right = st.columns([1.05, 0.95], gap="large")

    with left:
        st.markdown('<div class="solid-card">', unsafe_allow_html=True)
        st.markdown("### Account Identity")
        new_username = st.text_input(
            "Choose your username",
            value=username_value,
            placeholder="Example: swayam",
        )
        if st.button("Save Username", use_container_width=True, type="primary", key="save_username_btn"):
            if new_username.strip():
                update_username(new_username)
                st.success("Username updated successfully.")
                st.rerun()
            else:
                st.warning("Username cannot be empty.")
        st.markdown(f"**Email:** {st.session_state.user_email}")
        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        st.markdown('<div class="solid-card">', unsafe_allow_html=True)
        st.markdown("### Account Overview")
        render_plan_badge(plan)
        st.markdown(f"**Plan:** {plan.title()}")
        st.markdown(f"**Status:** {str(sub.get('status', 'active')).title()}")
        st.markdown(f"**Usage Today:** {usage_text}")
        st.markdown(f"**Report Tier:** {plan_info['pdf_name']}")
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div class="solid-card">', unsafe_allow_html=True)
        st.markdown("### Current Plan Features")
        for feat in plan_info["features"]:
            st.write(f"✓ {feat}")
        st.markdown("</div>", unsafe_allow_html=True)


def render_pricing():
    sub = get_subscription()
    current_plan = str(sub.get("plan", "free")).strip().lower()

    st.markdown(
        """
        <div class="hero">
            <div style="font-size:39px;font-weight:900;">Decedo Pricing</div>
            <div style="font-size:20px;font-weight:800;margin-top:6px;">
                Built for value, not just volume
            </div>
            <div style="font-size:14px;opacity:0.95;margin-top:8px;max-width:760px;">
                Payments are not integrated yet. These upgrade actions are testing-mode switches for complete V7 plan testing.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    n1, n2, n3 = st.columns(3)
    with n1:
        if st.button("← Back Home", use_container_width=True, type="primary", key="pricing_home"):
            st.session_state.current_page = "home"
            st.rerun()
    with n2:
        if st.button("Open Profile", use_container_width=True, type="primary", key="pricing_profile"):
            st.session_state.current_page = "profile"
            st.rerun()
    with n3:
        if st.button("Open Decision Lab", use_container_width=True, type="primary", key="pricing_lab"):
            st.session_state.current_page = "lab"
            st.rerun()

    c1, c2, c3 = st.columns(3, gap="large")

    def render_tier(col, plan_key, css_class=""):
        info = PLAN_CONFIG[plan_key]
        with col:
            st.markdown(f'<div class="tier-card {css_class}">', unsafe_allow_html=True)

            pill_class = "free" if plan_key == "free" else ("pro" if plan_key == "pro" else "premium")
            pill_text = "Current Plan" if current_plan == plan_key else info["label"]
            st.markdown(f'<div class="pill {pill_class}">{pill_text}</div>', unsafe_allow_html=True)

            st.markdown(f"## {info['label']}")
            st.markdown(f'<div class="price-big">{info["price"]}<span>/month</span></div>', unsafe_allow_html=True)

            if plan_key == "free":
                st.markdown('<div class="small-muted">Perfect to experience Decedo.</div>', unsafe_allow_html=True)
            elif plan_key == "pro":
                st.markdown('<div class="small-muted">For ambitious users who make decisions frequently.</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="small-muted">For founders, operators, and high-stakes decision-makers.</div>', unsafe_allow_html=True)

            st.markdown('<div class="plan-divider"></div>', unsafe_allow_html=True)

            for feat in info["features"]:
                st.write(f"✓ {feat}")

            st.markdown("")
            if current_plan == plan_key:
                st.success("You are currently on this plan.")
            else:
                label = (
                    "Start Free"
                    if plan_key == "free"
                    else f"Upgrade to {info['label']} (Testing)" if plan_key == "pro" else "Go Premium (Testing)"
                )
                if st.button(label, key=f"switch_{plan_key}", use_container_width=True, type="primary"):
                    set_plan_for_testing(plan_key)
                    st.success(f"{info['label']} activated in testing mode.")
                    st.rerun()

            st.markdown("</div>", unsafe_allow_html=True)

    render_tier(c1, "free")
    render_tier(c2, "pro", "pro")
    render_tier(c3, "premium", "premium")


# =========================================================
# PROMPTS
# =========================================================
def build_analysis_prompt(plan: str, decision_type: str, question: str, option_a: str, option_b: str):
    cfg = PLAN_CONFIG[plan]
    compare_mode = bool(option_a.strip() and option_b.strip())

    if compare_mode:
        extra = ""
        if cfg["show_hidden_risks"]:
            extra += '\n  "hidden_risks": ["risk 1", "risk 2", "risk 3"],'
        if cfg["show_opportunity_cost"]:
            extra += '\n  "opportunity_cost": "1 short paragraph on what is sacrificed by choosing the winning path",'
        if cfg["show_success_drivers"]:
            extra += '\n  "success_drivers": ["driver 1", "driver 2", "driver 3"],'
        if cfg["show_roadmap"]:
            extra += '\n  "roadmap_30_days": ["week 1 action", "week 2 action", "week 3 action", "week 4 action"],'
        if cfg["show_exec_summary"]:
            extra += '\n  "executive_summary": "1 short executive style summary",'

        debate = ""
        if cfg["show_debate"]:
            debate = """
  "ai_1_for_option_a": "1 short paragraph strongly supporting Option A",
  "ai_2_for_option_b": "1 short paragraph strongly supporting Option B",
  "final_opinion": "1 clear final verdict in 1-2 short sentences","""

        return f"""
You are Decedo, an AI Decision Operating System.

Analyze this comparison with sharp, premium-quality reasoning.

Decision Type:
{decision_type}

User question:
{question}

Option A:
{option_a}

Option B:
{option_b}

Return only strict valid JSON.
Use double quotes for JSON keys and string values.
No markdown.
No explanation outside JSON.

{{
  "comparison_summary": "1 short sentence",
  {debate}
  "option_a_score": "score out of 10",
  "option_b_score": "score out of 10",
  "better_option": "stronger option in 1 short sentence",
  "market_lens": "1 short sentence",
  "execution_lens": "1 short sentence",
  "risk_lens": "1 short sentence",
  "growth_lens": "1 short sentence",
  "confidence_level": "percentage like 85%",
  "risk_comparison": "Low or Medium or High",
  "why": ["point 1", "point 2", "point 3"],
  "first_next_step": "1 practical next action"{extra}
}}
"""
    else:
        extra = ""
        if cfg["show_hidden_risks"]:
            extra += '\n  "hidden_risks": ["risk 1", "risk 2", "risk 3"],'
        if cfg["show_opportunity_cost"]:
            extra += '\n  "opportunity_cost": "1 short paragraph on what is sacrificed by choosing this path",'
        if cfg["show_success_drivers"]:
            extra += '\n  "success_drivers": ["driver 1", "driver 2", "driver 3"],'
        if cfg["show_roadmap"]:
            extra += '\n  "roadmap_30_days": ["week 1 action", "week 2 action", "week 3 action", "week 4 action"],'
        if cfg["show_exec_summary"]:
            extra += '\n  "executive_summary": "1 short executive style summary",'

        verdict = ""
        if cfg["show_debate"]:
            verdict = '\n  "final_opinion": "1 clear final verdict in 1-2 short sentences",'

        return f"""
You are Decedo, an AI Decision Operating System.

Analyze the user's decision clearly, practically, and strategically.

Decision Type:
{decision_type}

User question:
{question}

Return only strict valid JSON.
Use double quotes for JSON keys and string values.
No markdown.
No explanation outside JSON.

{{
  "decision_summary": "1 short sentence",
  "best_option": "best choice in 1 short sentence",{verdict}
  "market_lens": "1 short sentence",
  "execution_lens": "1 short sentence",
  "risk_lens": "1 short sentence",
  "growth_lens": "1 short sentence",
  "confidence_level": "percentage like 85%",
  "risk_level": "Low or Medium or High",
  "decision_score": "score out of 10",
  "why": ["point 1", "point 2", "point 3"],
  "first_next_step": "1 practical next action"{extra}
}}
"""


def build_scenario_prompt(plan: str, decision_type: str, question: str, summary: str, option_a: str, option_b: str):
    cfg = PLAN_CONFIG[plan]
    compare_mode = bool(option_a.strip() and option_b.strip())

    if cfg["show_scenarios"]:
        if compare_mode:
            strategic_field = (
                '\n  "strategic_insight": "1 powerful strategic insight in 1-2 short sentences"'
                if cfg["show_strategic_insight"]
                else ""
            )
            return f"""
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

Return only strict valid JSON.
Use double quotes for JSON keys and string values.
No markdown.
No explanation outside JSON.

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
  }}{strategic_field}
}}
"""
        else:
            strategic_field = (
                '\n  "strategic_insight": "1 powerful strategic insight in 1-2 short sentences"'
                if cfg["show_strategic_insight"]
                else ""
            )
            return f"""
You are Decedo, an AI strategic simulation engine.

Decision Type:
{decision_type}

User question:
{question}

Existing decision summary:
{summary}

Return only strict valid JSON.
Use double quotes for JSON keys and string values.
No markdown.
No explanation outside JSON.

{{
  "recommended_path_future": {{
    "3_months": "1 short sentence",
    "1_year": "1 short sentence",
    "5_years": "1 short sentence"
  }}{strategic_field}
}}
"""
    else:
        if compare_mode:
            return f"""
You are Decedo, an AI strategic simulation engine.

Decision Type:
{decision_type}

User question:
{question}

Option A:
{option_a}

Option B:
{option_b}

Return only strict valid JSON.
Use double quotes for JSON keys and string values.
No markdown.
No explanation outside JSON.

{{
  "quick_outlook": "1 short paragraph comparing the medium-term future of both options"
}}
"""
        return f"""
You are Decedo, an AI strategic simulation engine.

Decision Type:
{decision_type}

User question:
{question}

Return only strict valid JSON.
Use double quotes for JSON keys and string values.
No markdown.
No explanation outside JSON.

{{
  "quick_outlook": "1 short paragraph explaining the medium-term outlook"
}}
"""


def render_lab():
    sub = get_subscription()
    plan = str(sub.get("plan", "free")).strip().lower()
    cfg = get_plan_features(plan)
    usage = get_usage()
    used_today = int(usage.get("reports_today", 0) or 0)
    usage_text = format_usage(used_today, cfg["limit"])

    profile = get_profile()
    username = st.session_state.user_email.split("@")[0]
    if profile and profile.get("username"):
        username = profile["username"]

    st.markdown(
        f"""
        <div class="hero">
            <div style="font-size:38px;font-weight:900;">Decision Lab</div>
            <div style="font-size:19px;font-weight:800;margin-top:6px;">
                Premium AI decision analysis based on your current plan
            </div>
            <div style="font-size:14px;opacity:0.95;margin-top:8px;">
                Profile: {username} • Plan: {plan.title()} • Usage Today: {usage_text}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    render_top_nav()

    if cfg["limit"] is not None and used_today >= cfg["limit"]:
        st.error(f"You have reached your {plan.title()} daily limit.")
        st.info("Upgrade from the Pricing page to continue.")
        return

    left, right = st.columns([1.08, 0.92], gap="large")

    with left:
        st.markdown('<div class="solid-card">', unsafe_allow_html=True)
        st.markdown("### Decision Input")
        decision_type = st.selectbox(
            "Decision Type",
            ["Career", "Business", "Investment", "Life", "Pricing", "Product"],
        )
        option_a = st.text_input("Option A (optional)", placeholder="Example: Price 499")
        option_b = st.text_input("Option B (optional)", placeholder="Example: Price 599")
        question = st.text_area(
            "Decision Question",
            placeholder="Example: Which price should I launch at?",
        )
        analyze = st.button("Analyze Decision", type="primary", use_container_width=True, key="analyze_btn")
        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        st.markdown('<div class="solid-card">', unsafe_allow_html=True)
        st.markdown("### Your Current Plan Unlocks")
        st.markdown('<div class="unlock-panel">', unsafe_allow_html=True)
        for feat in cfg["features"]:
            st.write(f"✓ {feat}")
        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("")
        if plan == "free":
            st.markdown(
                '<div class="feature-note">Upgrade to Pro for AI debate, confidence meter, strategic insight, and full scenario simulation.</div>',
                unsafe_allow_html=True,
            )
        elif plan == "pro":
            st.markdown(
                '<div class="feature-note">Upgrade to Premium for opportunity cost, roadmap, and executive-grade report depth.</div>',
                unsafe_allow_html=True,
            )
        else:
            st.success("You have the full Premium stack enabled.")

    if not analyze:
        return

    if not question.strip():
        st.warning("Please enter a decision question first.")
        return

    compare_mode = bool(option_a.strip() and option_b.strip())

    with st.spinner("Analyzing decision intelligence..."):
        analysis_prompt = build_analysis_prompt(plan, decision_type, question, option_a, option_b)
        analysis_data = safe_generate_json(
            analysis_prompt,
            "AI returned an invalid analysis format. Please click Analyze Decision again.",
        )

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
    hidden_risks = analysis_data.get("hidden_risks", [])
    opportunity_cost = analysis_data.get("opportunity_cost", "")
    success_drivers = analysis_data.get("success_drivers", [])
    roadmap_30_days = analysis_data.get("roadmap_30_days", [])
    executive_summary = analysis_data.get("executive_summary", "")

    with st.spinner("Simulating future outcomes..."):
        scenario_prompt = build_scenario_prompt(plan, decision_type, question, summary, option_a, option_b)
        scenario_data = safe_generate_json(
            scenario_prompt,
            "Scenario simulation returned an invalid format. Please try again.",
        )

    option_a_future = scenario_data.get("option_a_future", {})
    option_b_future = scenario_data.get("option_b_future", {})
    recommended_path_future = scenario_data.get("recommended_path_future", {})
    quick_outlook = scenario_data.get("quick_outlook", "")
    strategic_insight = scenario_data.get("strategic_insight", "")

    report = {
        "plan": plan,
        "decision_type": decision_type,
        "question": question,
        "option_a": option_a,
        "option_b": option_b,
        "summary": summary,
        "best_option": best_option,
        "risk_level": risk_level,
        "decision_score": decision_score,
        "confidence_level": confidence_level,
        "decision_grade": decision_grade,
        "market_lens": market_lens,
        "execution_lens": execution_lens,
        "risk_lens": risk_lens,
        "growth_lens": growth_lens,
        "why_points": why_points,
        "next_step": next_step,
        "strategic_insight": strategic_insight,
        "ai_1_argument": ai_1_argument,
        "ai_2_argument": ai_2_argument,
        "final_opinion": final_opinion,
        "option_a_future": option_a_future,
        "option_b_future": option_b_future,
        "recommended_path_future": recommended_path_future,
        "hidden_risks": hidden_risks,
        "opportunity_cost": opportunity_cost,
        "success_drivers": success_drivers,
        "roadmap_30_days": roadmap_30_days,
        "quick_outlook": quick_outlook,
        "executive_summary": executive_summary,
    }

    save_report(question, decision_type, option_a, option_b, plan, report)

    refreshed_usage = get_usage()
    refreshed_used_today = int(refreshed_usage.get("reports_today", 0) or 0)
    refreshed_usage_text = format_usage(refreshed_used_today, cfg["limit"])

    st.success(f"Report saved successfully. Usage Today: {refreshed_usage_text}")

    st.markdown("## Decision Dashboard")
    st.info(summary)

    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Best Choice", best_option)
    m2.metric("Risk Level", risk_level)
    m3.metric("Score", decision_score)
    m4.metric("Confidence", confidence_level)
    m5.metric("Grade", decision_grade)

    if executive_summary and cfg["show_exec_summary"]:
        st.markdown("### Executive Summary")
        st.markdown('<div class="exec-panel">', unsafe_allow_html=True)
        st.write(executive_summary)
        st.markdown("</div>", unsafe_allow_html=True)

    if compare_mode and option_a_score and option_b_score:
        s1, s2 = st.columns(2)
        with s1:
            st.metric("Option A Score", option_a_score)
            st.caption(option_a)
        with s2:
            st.metric("Option B Score", option_b_score)
            st.caption(option_b)

    if cfg["show_confidence_meter"]:
        st.markdown("### Confidence Meter")
        confidence_value = confidence_to_int(confidence_level)
        st.progress(confidence_value)
        st.caption(f"AI confidence: {confidence_value}%")

    if cfg["show_debate"] and (ai_1_argument or ai_2_argument):
        st.markdown("## AI 1 vs AI 2")
        d1, d2 = st.columns(2)
        with d1:
            st.markdown('<div class="debate-box">', unsafe_allow_html=True)
            st.markdown("### AI 1 — Argument for Option A")
            if option_a:
                st.write(f"**{option_a}**")
            st.write(ai_1_argument if ai_1_argument else "Not available")
            st.markdown("</div>", unsafe_allow_html=True)
        with d2:
            st.markdown('<div class="debate-box">', unsafe_allow_html=True)
            st.markdown("### AI 2 — Argument for Option B")
            if option_b:
                st.write(f"**{option_b}**")
            st.write(ai_2_argument if ai_2_argument else "Not available")
            st.markdown("</div>", unsafe_allow_html=True)

    if cfg["show_debate"]:
        st.markdown("## Final Opinion")
        st.markdown('<div class="judge-box">', unsafe_allow_html=True)
        st.write(final_opinion if final_opinion else best_option)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("### Decision Lenses")
    l1, l2 = st.columns(2)
    with l1:
        st.write(f"**Market Lens:** {market_lens}")
        st.write(f"**Execution Lens:** {execution_lens}")
    with l2:
        st.write(f"**Risk Lens:** {risk_lens}")
        st.write(f"**Growth Lens:** {growth_lens}")

    if why_points:
        st.markdown("### Why")
        for point in why_points:
            st.write(f"- {point}")

    st.markdown("### First Next Step")
    st.success(next_step)

    if cfg["show_strategic_insight"]:
        st.markdown("### Strategic Insight")
        st.success(strategic_insight if strategic_insight else "Build a structured plan around the recommended choice.")

    if cfg["show_hidden_risks"] and hidden_risks:
        st.markdown("### Hidden Risks")
        st.markdown('<div class="premium-panel">', unsafe_allow_html=True)
        for risk in hidden_risks:
            st.write(f"- {risk}")
        st.markdown("</div>", unsafe_allow_html=True)

    if cfg["show_success_drivers"] and success_drivers:
        st.markdown("### Success Drivers")
        st.markdown('<div class="premium-panel">', unsafe_allow_html=True)
        for driver in success_drivers:
            st.write(f"- {driver}")
        st.markdown("</div>", unsafe_allow_html=True)

    if cfg["show_opportunity_cost"] and opportunity_cost:
        st.markdown("### Opportunity Cost")
        st.markdown('<div class="premium-panel">', unsafe_allow_html=True)
        st.write(opportunity_cost)
        st.markdown("</div>", unsafe_allow_html=True)

    if cfg["show_roadmap"] and roadmap_30_days:
        st.markdown("### 30-Day Action Roadmap")
        st.markdown('<div class="premium-panel">', unsafe_allow_html=True)
        for step in roadmap_30_days:
            st.write(f"- {step}")
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("## Future Simulation")
    if cfg["show_scenarios"]:
        if option_a_future and option_b_future:
            f1, f2 = st.columns(2)
            with f1:
                st.markdown("### Option A Future")
                st.write(f"**{option_a}**")
                st.write(f"**3 Months:** {option_a_future.get('3_months', 'Not available')}")
                st.write(f"**1 Year:** {option_a_future.get('1_year', 'Not available')}")
                st.write(f"**5 Years:** {option_a_future.get('5_years', 'Not available')}")
            with f2:
                st.markdown("### Option B Future")
                st.write(f"**{option_b}**")
                st.write(f"**3 Months:** {option_b_future.get('3_months', 'Not available')}")
                st.write(f"**1 Year:** {option_b_future.get('1_year', 'Not available')}")
                st.write(f"**5 Years:** {option_b_future.get('5_years', 'Not available')}")
        elif recommended_path_future:
            st.write(f"**3 Months:** {recommended_path_future.get('3_months', 'Not available')}")
            st.write(f"**1 Year:** {recommended_path_future.get('1_year', 'Not available')}")
            st.write(f"**5 Years:** {recommended_path_future.get('5_years', 'Not available')}")
        else:
            st.info("Scenario data not available.")
    else:
        st.info(
            quick_outlook
            if quick_outlook
            else "Upgrade to Pro for full 3-month, 1-year and 5-year scenario simulation."
        )

    pdf_bytes = create_plan_pdf(report, plan)
    st.download_button(
        label=f"Download {cfg['pdf_name']} (PDF)",
        data=pdf_bytes,
        file_name=f"decedo_{plan}_report.pdf",
        mime="application/pdf",
        use_container_width=True,
    )
 if option_a and option_b:
    st.markdown("## Your Final Decision")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Choose Option A", use_container_width=True, type="primary", key="choose_a_btn"):
            save_decision_history(question, decision_type, option_a, option_b, "A")
            st.success("Option A saved successfully!")

    with col2:
        if st.button("Choose Option B", use_container_width=True, type="primary", key="choose_b_btn"):
            save_decision_history(question, decision_type, option_a, option_b, "B")
            st.success("Option B saved successfully!")

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
elif st.session_state.current_page == "pricing":
    render_pricing()
else:
    render_home()
