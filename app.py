import streamlit as st
import json
from google import genai
from fpdf import FPDF

# ===============================
# PAGE CONFIG
# ===============================
st.set_page_config(
    page_title="Decedo - AI Decision Intelligence",
    page_icon="🧠",
    layout="wide"
)

st.markdown("""
<style>
    .main {
        background-color: #f8fafc;
    }

    section[data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #e5e7eb;
    }

    div[data-testid="stMetric"] {
        background-color: white;
        border: 1px solid #e5e7eb;
        padding: 15px;
        border-radius: 16px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    }

    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }

    h1, h2, h3 {
        color: #111827;
    }

    .stButton>button {
        border-radius: 12px;
        font-weight: 600;
        height: 3em;
    }

    .stTextInput>div>div>input,
    .stTextArea textarea,
    .stSelectbox>div>div {
        border-radius: 12px;
    }

    .stAlert {
        border-radius: 14px;
    }
</style>
""", unsafe_allow_html=True)

# ===============================
# API SETUP
# ===============================
API_KEY = st.secrets["GEMINI_API_KEY"]
client = genai.Client(api_key=API_KEY)

# ===============================
# SESSION HISTORY
# ===============================
if "history" not in st.session_state:
    st.session_state.history = []

# ===============================
# HELPERS
# ===============================
def parse_json_response(raw_text: str) -> dict:
    clean_text = raw_text.strip()

    if clean_text.startswith("```json"):
        clean_text = clean_text.replace("```json", "", 1).strip()
    if clean_text.startswith("```"):
        clean_text = clean_text.replace("```", "", 1).strip()
    if clean_text.endswith("```"):
        clean_text = clean_text[:-3].strip()

    return json.loads(clean_text)


def safe_text(value):
    if value is None:
        return "Not available"
    return str(value)


def clean_pdf_text(text):
    return safe_text(text).replace("–", "-").replace("’", "'").replace("“", '"').replace("”", '"')


def create_pdf_report(
    question,
    decision_type,
    summary,
    best_option,
    risk_level,
    decision_score,
    confidence_level,
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
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    pdf.set_font("Arial", "B", 18)
    pdf.cell(0, 10, "Decedo AI Decision Report", ln=True)

    pdf.set_font("Arial", "", 11)
    pdf.cell(0, 8, clean_pdf_text(f"Decision Type: {decision_type}"), ln=True)
    pdf.ln(4)

    pdf.set_font("Arial", "B", 13)
    pdf.cell(0, 8, "Decision Question", ln=True)
    pdf.set_font("Arial", "", 11)
    pdf.multi_cell(0, 8, clean_pdf_text(question))
    pdf.ln(2)

    pdf.set_font("Arial", "B", 13)
    pdf.cell(0, 8, "Decision Summary", ln=True)
    pdf.set_font("Arial", "", 11)
    pdf.multi_cell(0, 8, clean_pdf_text(summary))
    pdf.ln(2)

    pdf.set_font("Arial", "B", 13)
    pdf.cell(0, 8, "Decision Metrics", ln=True)
    pdf.set_font("Arial", "", 11)
    pdf.multi_cell(0, 8, clean_pdf_text(f"Best Choice: {best_option}"))
    pdf.multi_cell(0, 8, clean_pdf_text(f"Risk Level: {risk_level}"))
    pdf.multi_cell(0, 8, clean_pdf_text(f"Score: {decision_score}"))
    pdf.multi_cell(0, 8, clean_pdf_text(f"Confidence: {confidence_level}"))
    pdf.ln(2)

    pdf.set_font("Arial", "B", 13)
    pdf.cell(0, 8, "Decision Lenses", ln=True)
    pdf.set_font("Arial", "", 11)
    pdf.multi_cell(0, 8, clean_pdf_text(f"Market Lens: {market_lens}"))
    pdf.multi_cell(0, 8, clean_pdf_text(f"Execution Lens: {execution_lens}"))
    pdf.multi_cell(0, 8, clean_pdf_text(f"Risk Lens: {risk_lens}"))
    pdf.multi_cell(0, 8, clean_pdf_text(f"Growth Lens: {growth_lens}"))
    pdf.ln(2)

    if option_a_score or option_b_score:
        pdf.set_font("Arial", "B", 13)
        pdf.cell(0, 8, "Comparison Scores", ln=True)
        pdf.set_font("Arial", "", 11)
        if option_a:
            pdf.multi_cell(0, 8, clean_pdf_text(f"{option_a} Score: {option_a_score}"))
        if option_b:
            pdf.multi_cell(0, 8, clean_pdf_text(f"{option_b} Score: {option_b_score}"))
        pdf.ln(2)

    if why_points:
        pdf.set_font("Arial", "B", 13)
        pdf.cell(0, 8, "Why", ln=True)
        pdf.set_font("Arial", "", 11)
        for point in why_points:
            pdf.multi_cell(0, 8, clean_pdf_text(f"- {point}"))
        pdf.ln(2)

    pdf.set_font("Arial", "B", 13)
    pdf.cell(0, 8, "First Next Step", ln=True)
    pdf.set_font("Arial", "", 11)
    pdf.multi_cell(0, 8, clean_pdf_text(next_step))
    pdf.ln(2)

    pdf.set_font("Arial", "B", 13)
    pdf.cell(0, 8, "Scenario Simulation", ln=True)
    pdf.set_font("Arial", "", 11)

    if option_a_future and option_b_future:
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 8, clean_pdf_text(f"Option A Future: {option_a}"), ln=True)
        pdf.set_font("Arial", "", 11)
        pdf.multi_cell(0, 8, clean_pdf_text(f"3 Months: {option_a_future.get('3_months', 'Not available')}"))
        pdf.multi_cell(0, 8, clean_pdf_text(f"1 Year: {option_a_future.get('1_year', 'Not available')}"))
        pdf.multi_cell(0, 8, clean_pdf_text(f"5 Years: {option_a_future.get('5_years', 'Not available')}"))
        pdf.ln(1)

        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 8, clean_pdf_text(f"Option B Future: {option_b}"), ln=True)
        pdf.set_font("Arial", "", 11)
        pdf.multi_cell(0, 8, clean_pdf_text(f"3 Months: {option_b_future.get('3_months', 'Not available')}"))
        pdf.multi_cell(0, 8, clean_pdf_text(f"1 Year: {option_b_future.get('1_year', 'Not available')}"))
        pdf.multi_cell(0, 8, clean_pdf_text(f"5 Years: {option_b_future.get('5_years', 'Not available')}"))
        pdf.ln(2)

    elif recommended_path_future:
        pdf.multi_cell(0, 8, clean_pdf_text(f"3 Months: {recommended_path_future.get('3_months', 'Not available')}"))
        pdf.multi_cell(0, 8, clean_pdf_text(f"1 Year: {recommended_path_future.get('1_year', 'Not available')}"))
        pdf.multi_cell(0, 8, clean_pdf_text(f"5 Years: {recommended_path_future.get('5_years', 'Not available')}"))
        pdf.ln(2)

    pdf.set_font("Arial", "B", 13)
    pdf.cell(0, 8, "Strategic Insight", ln=True)
    pdf.set_font("Arial", "", 11)
    pdf.multi_cell(0, 8, clean_pdf_text(strategic_insight))

    return pdf.output(dest="S").encode("latin-1")


# ===============================
# SIDEBAR INPUT PANEL
# ===============================
with st.sidebar:
    st.title("🧠 Decedo")
    st.caption("AI Decision Intelligence Platform")
    st.divider()

    decision_type = st.selectbox(
        "Decision Type",
        ["Career", "Business", "Investment", "Life"]
    )

    option_a = st.text_input(
        "Option A (optional)",
        placeholder="Example: Learn coding first"
    )

    option_b = st.text_input(
        "Option B (optional)",
        placeholder="Example: Learn marketing first"
    )

    question = st.text_area(
        "Decision Question",
        placeholder="Example: Should I start a startup or take a job?"
    )

    analyze = st.button("Analyze Decision", type="primary", use_container_width=True)

    st.divider()
    st.caption("Structured reasoning • Decision lenses • AI debate • Scenario simulation")

# ===============================
# MAIN HEADER
# ===============================
st.title("🧠 Decedo")
st.subheader("AI Operating System for Decisions")
st.caption("Make better decisions with structured AI reasoning, confidence scoring, and strategic analysis.")
st.divider()

# ===============================
# ANALYZE BUTTON LOGIC
# ===============================
if analyze:

    if question.strip():

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

Rules:
- Keep the full response concise
- Be direct
- Use realistic reasoning
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

Rules:
- Keep the full response concise
- Be direct
- Use realistic reasoning
"""

        try:
            with st.spinner("Analyzing your decision..."):
                analysis_response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=analysis_prompt,
                )

            analysis_result = analysis_response.text
            analysis_data = parse_json_response(analysis_result)

            summary = analysis_data.get("decision_summary", analysis_data.get("comparison_summary", "Not available"))
            best_option = analysis_data.get("best_option", analysis_data.get("better_option", "Not available"))
            risk_level = analysis_data.get("risk_level", analysis_data.get("risk_comparison", "Not available"))
            decision_score = analysis_data.get("decision_score", analysis_data.get("option_a_score", "Not available"))
            next_step = analysis_data.get("first_next_step", "Not available")
            confidence_level = analysis_data.get("confidence_level", "Not available")

            market_lens = analysis_data.get("market_lens", "")
            execution_lens = analysis_data.get("execution_lens", "")
            risk_lens = analysis_data.get("risk_lens", "")
            growth_lens = analysis_data.get("growth_lens", "")
            why_points = analysis_data.get("why", [])

            # ===============================
            # SCENARIO SIMULATION PROMPT
            # ===============================
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

Rules:
- Be realistic
- Be specific
- Keep each point concise
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

Rules:
- Be realistic
- Be specific
- Keep each point concise
"""

            with st.spinner("Simulating future outcomes..."):
                scenario_response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=scenario_prompt,
                )

            scenario_result = scenario_response.text
            scenario_data = parse_json_response(scenario_result)

            option_a_future = scenario_data.get("option_a_future", {})
            option_b_future = scenario_data.get("option_b_future", {})
            recommended_path_future = scenario_data.get("recommended_path_future", {})
            strategic_insight = scenario_data.get("strategic_insight", "Not available")

            st.session_state.history.append({
                "question": question,
                "answer": {
                    "analysis": analysis_data,
                    "scenario": scenario_data
                }
            })

            # ===============================
            # RESULT UI
            # ===============================
            st.markdown("## 📊 Decision Dashboard")

            st.markdown("### Decision Summary")
            st.info(summary)

            st.markdown("### Decision Lenses")
            lens_col1, lens_col2 = st.columns(2)

            with lens_col1:
                st.markdown("#### Market Lens")
                st.write(market_lens if market_lens else "Not available")

                st.markdown("#### Execution Lens")
                st.write(execution_lens if execution_lens else "Not available")

            with lens_col2:
                st.markdown("#### Risk Lens")
                st.write(risk_lens if risk_lens else "Not available")

                st.markdown("#### Growth Lens")
                st.write(growth_lens if growth_lens else "Not available")

            st.markdown("### Decision Metrics")
            col1, col2, col3, col4 = st.columns(4)

            col1.metric("Best Choice", best_option)
            col2.metric("Risk Level", risk_level)
            col3.metric("Score", decision_score)
            col4.metric("Confidence", confidence_level)

            if confidence_level and confidence_level != "Not available":
                try:
                    confidence_number = int(str(confidence_level).replace("%", "").strip())
                    st.markdown("#### Confidence Meter")
                    st.progress(confidence_number)
                except:
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

            # ===============================
            # SCENARIO SIMULATION UI
            # ===============================
            st.divider()
            st.markdown("## 🔮 Scenario Simulation")

            if option_a_future and option_b_future:
                s1, s2 = st.columns(2)

                with s1:
                    st.markdown("### Option A Future")
                    st.markdown(f"**{option_a if option_a else 'Option A'}**")
                    st.markdown("**3 Months**")
                    st.write(option_a_future.get("3_months", "Not available"))
                    st.markdown("**1 Year**")
                    st.write(option_a_future.get("1_year", "Not available"))
                    st.markdown("**5 Years**")
                    st.write(option_a_future.get("5_years", "Not available"))

                with s2:
                    st.markdown("### Option B Future")
                    st.markdown(f"**{option_b if option_b else 'Option B'}**")
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

            # ===============================
            # STRATEGIC INSIGHT
            # ===============================
            st.divider()
            st.markdown("## 🎯 Strategic Insight")
            st.success(strategic_insight)

            # ===============================
            # PDF DOWNLOAD
            # ===============================
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

            st.download_button(
                label="Download Decision Report (PDF)",
                data=pdf_bytes,
                file_name="decedo_decision_report.pdf",
                mime="application/pdf",
                use_container_width=True
            )

        except Exception as e:
            if "RESOURCE_EXHAUSTED" in str(e) or "429" in str(e):
                st.warning("⚠️ AI request limit reached. Please wait a minute and try again.")
            else:
                st.error(f"Real error: {e}")

    else:
        st.warning("Please enter a decision question first.")

# ===============================
# RECENT DECISIONS
# ===============================
if st.session_state.history:
    st.divider()
    st.markdown("## 📜 Recent Decisions")

    for item in reversed(st.session_state.history[-5:]):
        with st.expander(item["question"]):
            st.write(item["answer"])
