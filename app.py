import streamlit as st
import json
from google import genai

# ===============================
# PAGE CONFIG
# ===============================
st.set_page_config(
    page_title="Decedo - AI Decision Intelligence",
    page_icon="🧠",
    layout="wide"
)

st.title("🧠 Decedo")
st.subheader("AI Decision Intelligence Assistant")

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
# INPUT SECTION
# ===============================
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
    "Enter your decision question:",
    placeholder="Example: Should I start a startup or take a job?"
)

# ===============================
# ANALYZE BUTTON
# ===============================
if st.button("Analyze Decision", type="primary", use_container_width=True):

    if question.strip():

        if option_a.strip() and option_b.strip():
            prompt = f"""
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
            prompt = f"""
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
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt,
                )

            result = response.text

            st.session_state.history.append({
                "question": question,
                "answer": result
            })

            # ===============================
            # JSON PARSING
            # ===============================
            clean_result = result.strip()

            if clean_result.startswith("```json"):
                clean_result = clean_result.replace("```json", "", 1).strip()

            if clean_result.endswith("```"):
                clean_result = clean_result[:-3].strip()

            data = json.loads(clean_result)

            summary = data.get("decision_summary", data.get("comparison_summary", "Not available"))
            best_option = data.get("best_option", data.get("better_option", "Not available"))
            risk_level = data.get("risk_level", data.get("risk_comparison", "Not available"))
            decision_score = data.get("decision_score", data.get("option_a_score", "Not available"))
            next_step = data.get("first_next_step", "Not available")
            confidence_level = data.get("confidence_level", "Not available")

            market_lens = data.get("market_lens", "")
            execution_lens = data.get("execution_lens", "")
            risk_lens = data.get("risk_lens", "")
            growth_lens = data.get("growth_lens", "")

            why_points = data.get("why", [])

            # ===============================
            # RESULT UI
            # ===============================
            st.markdown("## 🧠 AI Decision Analysis")

            st.markdown("### Decision Summary")
            st.info(summary)

            st.markdown("### Decision Lenses")

            lens_col1, lens_col2 = st.columns(2)

            with lens_col1:
                st.markdown("**Market Lens**")
                st.write(market_lens if market_lens else "Not available")

                st.markdown("**Execution Lens**")
                st.write(execution_lens if execution_lens else "Not available")

            with lens_col2:
                st.markdown("**Risk Lens**")
                st.write(risk_lens if risk_lens else "Not available")

                st.markdown("**Growth Lens**")
                st.write(growth_lens if growth_lens else "Not available")

            col1, col2, col3, col4 = st.columns(4)

            col1.metric("Best Choice", best_option)
            col2.metric("Risk Level", risk_level)
            col3.metric("Score", decision_score)
            col4.metric("Confidence", confidence_level)

            if confidence_level and confidence_level != "Not available":
                try:
                    confidence_number = int(str(confidence_level).replace("%", "").strip())
                    st.markdown("### Confidence Meter")
                    st.progress(confidence_number)
                except:
                    pass

            if "option_a_score" in data or "option_b_score" in data:
                st.markdown("### Comparison Scores")
                c1, c2 = st.columns(2)
                c1.metric("Option A Score", data.get("option_a_score", "N/A"))
                c2.metric("Option B Score", data.get("option_b_score", "N/A"))

            if "ai_1_for_option_a" in data and "ai_2_for_option_b" in data:
                st.markdown("### 🥊 AI Debate Mode")

                d1, d2 = st.columns(2)

                with d1:
                    st.markdown("#### AI 1 - Option A")
                    st.write(data.get("ai_1_for_option_a", ""))

                with d2:
                    st.markdown("#### AI 2 - Option B")
                    st.write(data.get("ai_2_for_option_b", ""))

            if why_points:
                st.markdown("### Why")
                for point in why_points:
                    st.write(f"• {point}")

            st.markdown("### First Next Step")
            st.success(next_step)

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
    st.markdown("---")
    st.markdown("## 📜 Recent Decisions")

    for item in reversed(st.session_state.history[-5:]):
        with st.expander(item["question"]):
            st.write(item["answer"])
