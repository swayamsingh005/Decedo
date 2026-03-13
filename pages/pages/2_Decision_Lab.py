import streamlit as st
import json
from datetime import datetime
from zoneinfo import ZoneInfo
from google import genai
from fpdf import FPDF
from supabase import create_client, Client

st.set_page_config(
    page_title="Decision Lab - Decedo",
    page_icon="🧠",
    layout="wide"
)

st.markdown("""
<style>
    .main {
        background: linear-gradient(180deg, #f8fafc 0%, #eef4ff 100%);
    }
    .block-container {
        max-width: 1200px;
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    .hero-card {
        background: linear-gradient(135deg, #0f172a 0%, #1d4ed8 100%);
        border-radius: 28px;
        padding: 28px;
        color: white;
        box-shadow: 0 18px 40px rgba(15, 23, 42, 0.18);
        margin-bottom: 20px;
    }
    .section-card {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 22px;
        padding: 18px;
        box-shadow: 0 8px 24px rgba(15, 23, 42, 0.05);
        margin-bottom: 16px;
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

GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
gemini_client = genai.Client(api_key=GEMINI_API_KEY)

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_ANON_KEY = st.secrets["SUPABASE_ANON_KEY"]
SUPABASE_SERVICE_ROLE_KEY = st.secrets["SUPABASE_SERVICE_ROLE_KEY"]

supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
admin_supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

if not st.session_state.get("authenticated", False):
    st.switch_page("app.py")

if "history" not in st.session_state:
    st.session_state.history = []

user_id = st.session_state["user_id"]
user_email = st.session_state["user_email"]


def logout_user():
    try:
        supabase.auth.sign_out()
    except Exception:
        pass


def get_profile():
    try:
        result = admin_supabase.table("profiles").select("*").eq("user_id", user_id).limit(1).execute()
        if result.data:
            return result.data[0]
    except Exception:
        pass
    return None


def get_user_plan(user_id: str):
    try:
        result = admin_supabase.table("subscriptions").select("*").eq("user_id", user_id).limit(1).execute()
        if result.data:
            return result.data[0].get("plan", "free"), result.data[0].get("status", "active")
    except Exception:
        pass
    return "free", "active"


def get_plan_limit(plan: str):
    plan = (plan or "free").lower()
    if plan == "free":
        return 3
    if plan == "pro":
        return 50
    if plan == "premium":
        return None
    return 3


def get_usage():
    try:
        result = admin_supabase.table("usage_tracking").select("*").eq("user_id", user_id).limit(1).execute()
        if result.data:
            return result.data[0]
    except Exception:
        pass
    return {
        "reports_today": 0,
        "last_reset": datetime.now(ZoneInfo("Asia/Kolkata")).isoformat()
    }


def reset_usage_if_new_day():
    usage = get_usage()
    now = datetime.now(ZoneInfo("Asia/Kolkata"))
    today = now.date()

    try:
        last_reset_date = datetime.fromisoformat(
            usage["last_reset"].replace("Z", "+00:00")
        ).astimezone(ZoneInfo("Asia/Kolkata")).date()
    except Exception:
        last_reset_date = today

    if last_reset_date != today:
        admin_supabase.table("usage_tracking").update({
            "reports_today": 0,
            "last_reset": now.isoformat()
        }).eq("user_id", user_id).execute()
        usage["reports_today"] = 0
        usage["last_reset"] = now.isoformat()

    return usage


def user_can_generate():
    plan, status = get_user_plan(user_id)
    usage = reset_usage_if_new_day()
    used = usage.get("reports_today", 0)
    limit = get_plan_limit(plan)

    if status != "active":
        return False, plan, used, limit

    if limit is None:
        return True, plan, used, limit

    return used < limit, plan, used, limit


def increment_usage():
    usage = reset_usage_if_new_day()
    used = usage.get("reports_today", 0)

    admin_supabase.table("usage_tracking").update({
        "reports_today": used + 1,
        "last_reset": datetime.now(ZoneInfo("Asia/Kolkata")).isoformat()
    }).eq("user_id", user_id).execute()


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


def save_report(question, decision_type, option_a, option_b, analysis_data, scenario_data):
    admin_supabase.table("reports").insert({
        "user_id": user_id,
        "decision_type": decision_type,
        "question": question,
        "option_a": option_a if option_a else None,
        "option_b": option_b if option_b else None,
        "analysis": {
            "analysis": analysis_data,
            "scenario": scenario_data
        }
    }).execute()
    increment_usage()


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
    option_a="",
    option_b="",
    option_a_score="",
    option_b_score="",
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
    sec("Decision Summary", summary)
    sec("Best Choice", best_option)
    sec("Risk Level", risk_level)
    sec("Decision Score", decision_score)
    sec("Confidence", confidence_level)
    sec("Decision Grade", decision_grade)
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

    pdf.ln(2)
    sec("Strategic Insight", strategic_insight)

    return pdf.output(dest="S").encode("latin-1")


profile = get_profile()
username = user_email.split("@")[0]
if profile and profile.get("username"):
    username = profile["username"]

can_generate, plan, used_today, limit = user_can_generate()

with st.sidebar:
    st.title("🧠 Decedo")
    st.caption(f"Welcome, {username}")
    st.divider()
    st.markdown(f"**Plan:** {plan.title()}")
    st.markdown(f"**Usage Today:** {used_today} / {'Unlimited' if limit is None else limit}")
    if limit is not None:
        st.progress(min(used_today / limit, 1.0))

    st.divider()

    if st.button("Profile", use_container_width=True):
        st.switch_page("pages/1_Profile.py")

    if st.button("Back to Home", use_container_width=True):
        st.switch_page("app.py")

    if st.button("Logout", use_container_width=True):
        logout_user()
        st.session_state.authenticated = False
        st.session_state.user_email = None
        st.session_state.user_id = None
        st.switch_page("app.py")

    st.divider()

    decision_type = st.selectbox("Decision Type", ["Career", "Business", "Investment", "Life"])
    option_a = st.text_input("Option A (optional)", placeholder="Example: Learn coding first")
    option_b = st.text_input("Option B (optional)", placeholder="Example: Learn marketing first")
    question = st.text_area("Decision Question", placeholder="Example: Should I start a startup or take a job?")
    analyze = st.button("Analyze Decision", type="primary", use_container_width=True)

st.markdown(f"""
<div class="hero-card">
    <div style="font-size:34px;font-weight:800;">🔬 Decision Lab</div>
    <div style="font-size:18px;font-weight:600;margin-top:6px;">
        Premium AI decision analysis, scenario simulation, and downloadable reports
    </div>
    <div style="font-size:14px;opacity:0.9;margin-top:8px;">
        Profile: {username} • Plan: {plan.title()}
    </div>
</div>
""", unsafe_allow_html=True)

if not can_generate:
    st.error("⚠ Daily limit reached for your current plan.")
    st.markdown("""
    <div class="section-card">
        <h3 style="margin-top:0;">Upgrade Plans</h3>
        <p><b>Free:</b> 3 decisions/day</p>
        <p><b>Pro:</b> 50 decisions/day — <s>₹799</s> <b>₹599/month</b></p>
        <p><b>Premium:</b> Unlimited — <s>₹1999</s> <b>₹1499/month</b></p>
    </div>
    """, unsafe_allow_html=True)

if analyze:
    if not can_generate:
        st.stop()

    if not question.strip():
        st.warning("Please enter a decision question first.")
        st.stop()

    if option_a.strip() and option_b.strip():
        analysis_prompt = f"""
You are Decedo, an AI decision intelligence assistant.

Analyze this decision as a structured comparison.

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

Use this exact JSON structure:
{{
  "comparison_summary": "1 short sentence",
  "ai_1_for_option_a": "1 short paragraph supporting Option A",
  "ai_2_for_option_b": "1 short paragraph supporting Option B",
  "option_a_score": "score out of 10",
  "option_b_score": "score out of 10",
  "better_option": "stronger option in 1 short sentence",
  "market_lens": "1 short sentence",
  "execution_lens": "1 short sentence",
  "risk_lens": "1 short sentence",
  "growth_lens": "1 short sentence",
  "confidence_level": "percentage like 78%",
  "risk_comparison": "Low or Medium or High",
  "why": ["point 1", "point 2"],
  "first_next_step": "1 practical next action"
}}
"""
    else:
        analysis_prompt = f"""
You are Decedo, an AI decision intelligence assistant.

Analyze the user's decision question clearly and briefly.

Decision Type:
{decision_type}

User question:
{question}

Respond only in valid JSON.
Do not write markdown.
Do not add explanation outside JSON.

Use this exact JSON structure:
{{
  "decision_summary": "1 short sentence",
  "best_option": "best choice in 1 short sentence",
  "market_lens": "1 short sentence",
  "execution_lens": "1 short sentence",
  "risk_lens": "1 short sentence",
  "growth_lens": "1 short sentence",
  "confidence_level": "percentage like 78%",
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
        decision_score = analysis_data.get("decision_score", analysis_data.get("option_a_score", "Not available"))
        confidence_level = analysis_data.get("confidence_level", "Not available")
        next_step = analysis_data.get("first_next_step", "Not available")
        decision_grade = calculate_grade(decision_score)

        market_lens = analysis_data.get("market_lens", "")
        execution_lens = analysis_data.get("execution_lens", "")
        risk_lens = analysis_data.get("risk_lens", "")
        growth_lens = analysis_data.get("growth_lens", "")
        why_points = analysis_data.get("why", [])

        if option_a.strip() and option_b.strip():
            scenario_prompt = f"""
You are Decedo, an AI strategic simulation engine.

Simulate the future consequences of both options.

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

Best option:
{best_option}

Market lens:
{market_lens}

Execution lens:
{execution_lens}

Risk lens:
{risk_lens}

Growth lens:
{growth_lens}

Respond only in valid JSON.
Do not write markdown.
Do not add explanation outside JSON.

Use this exact JSON structure:
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

Simulate the future consequences of the user's likely path.

Decision Type:
{decision_type}

User question:
{question}

Existing decision summary:
{summary}

Best option:
{best_option}

Market lens:
{market_lens}

Execution lens:
{execution_lens}

Risk lens:
{risk_lens}

Growth lens:
{growth_lens}

Respond only in valid JSON.
Do not write markdown.
Do not add explanation outside JSON.

Use this exact JSON structure:
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

        history_item = {
            "question": question,
            "answer": {
                "analysis": analysis_data,
                "scenario": scenario_data
            }
        }
        st.session_state.history.append(history_item)

        st.markdown("## 📊 Decision Dashboard")

        st.markdown("### Decision Summary")
        st.info(summary)

        st.markdown("### Decision Lenses")
        l1, l2 = st.columns(2)

        with l1:
            st.markdown("#### Market Lens")
            st.write(market_lens or "Not available")
            st.markdown("#### Execution Lens")
            st.write(execution_lens or "Not available")

        with l2:
            st.markdown("#### Risk Lens")
            st.write(risk_lens or "Not available")
            st.markdown("#### Growth Lens")
            st.write(growth_lens or "Not available")

        st.markdown("### Decision Metrics")
        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("Best Choice", best_option)
        m2.metric("Risk Level", risk_level)
        m3.metric("Score", decision_score)
        m4.metric("Confidence", confidence_level)
        m5.metric("Decision Grade", decision_grade)

        try:
            confidence_number = int(str(confidence_level).replace("%", "").strip())
            st.markdown("#### Confidence Meter")
            st.progress(confidence_number)
        except Exception:
            pass

        if "option_a_score" in analysis_data or "option_b_score" in analysis_data:
            st.markdown("### Comparison Scores")
            c1, c2 = st.columns(2)
            c1.metric("Option A Score", analysis_data.get("option_a_score", "N/A"))
            c2.metric("Option B Score", analysis_data.get("option_b_score", "N/A"))

        if "ai_1_for_option_a" in analysis_data and "ai_2_for_option_b" in analysis_data:
            st.markdown("### 🥊 AI Debate Mode")
            d1, d2 = st.columns(2)
            with d1:
                st.markdown("#### AI 1 - Option A")
                st.write(analysis_data.get("ai_1_for_option_a", ""))
            with d2:
                st.markdown("#### AI 2 - Option B")
                st.write(analysis_data.get("ai_2_for_option_b", ""))

        if why_points:
            st.markdown("### Why")
            for point in why_points:
                st.write(f"• {point}")

        st.markdown("### First Next Step")
        st.success(next_step)

        st.divider()
        st.markdown("## 🔮 Scenario Simulation")

        if option_a_future and option_b_future:
            s1, s2 = st.columns(2)

            with s1:
                st.markdown("### Option A Future")
                st.markdown(f"**{option_a}**")
                st.markdown("**3 Months**")
                st.write(option_a_future.get("3_months", "Not available"))
                st.markdown("**1 Year**")
                st.write(option_a_future.get("1_year", "Not available"))
                st.markdown("**5 Years**")
                st.write(option_a_future.get("5_years", "Not available"))

            with s2:
                st.markdown("### Option B Future")
                st.markdown(f"**{option_b}**")
                st.markdown("**3 Months**")
                st.write(option_b_future.get("3_months", "Not available"))
                st.markdown("**1 Year**")
                st.write(option_b_future.get("1_year", "Not available"))
                st.markdown("**5 Years**")
                st.write(option_b_future.get("5_years", "Not available"))

        elif recommended_path_future:
            st.markdown("### Recommended Path Future")
            st.markdown("**3 Months**")
            st.write(recommended_path_future.get("3_months", "Not available"))
            st.markdown("**1 Year**")
            st.write(recommended_path_future.get("1_year", "Not available"))
            st.markdown("**5 Years**")
            st.write(recommended_path_future.get("5_years", "Not available"))

        st.divider()
        st.markdown("## 🎯 Strategic Insight")
        st.success(strategic_insight)

        st.divider()
        st.markdown("## 📄 Download Report")

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
            option_a=option_a,
            option_b=option_b,
            option_a_score=analysis_data.get("option_a_score", ""),
            option_b_score=analysis_data.get("option_b_score", ""),
            option_a_future=option_a_future,
            option_b_future=option_b_future,
            recommended_path_future=recommended_path_future
        )

        safe_filename = question[:40].replace(" ", "_").replace("/", "_").replace("\\", "_")
        if not safe_filename:
            safe_filename = "decedo_decision_report"

        st.download_button(
            label="Download Decision Report (PDF)",
            data=pdf_bytes,
            file_name=f"{safe_filename}.pdf",
            mime="application/pdf",
            use_container_width=True
        )

    except Exception as e:
        st.error(f"Real error: {e}")

if st.session_state.history:
    st.divider()
    st.markdown("## 📜 Recent Decisions")
    for item in reversed(st.session_state.history[-5:]):
        with st.expander(item["question"]):
            st.write(item["answer"])
