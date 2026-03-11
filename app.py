import streamlit as st
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

Analyze this decision as a comparison.

Decision Type:
{decision_type}

User question:
{question}

Option A:
{option_a}

Option B:
{option_b}

Respond in exactly this format:

Comparison Summary:
Write 1 short sentence.

Option A Score:
Score out of 10

Option B Score:
Score out of 10

Better Option:
Choose the stronger option in 1 short sentence.

Confidence Level:
Give a confidence percentage from 0 to 100%
Why:
• Give 2 short bullet points only

Risk Comparison:
Low / Medium / High

First Next Step:
Give 1 practical next action.

Rules:
- Keep answer under 100 words
- Avoid long paragraphs
- Be concise
"""

        else:

            prompt = f"""
You are Decedo, an AI decision intelligence assistant.

Analyze the user's decision question clearly and briefly.

Decision Type:
{decision_type}

User question:
{question}

Respond in exactly this format:

Decision Summary:
Write 1 short sentence.

Best Option:
Write the best choice in 1 short sentence.

Confidence Level:
Give a confidence percentage from 0 to 100%
Why:
• Give 2 short bullet points only

Risk Level:
Low / Medium / High

Decision Score:
Score out of 10

First Next Step:
Give 1 practical next action.

Rules:
- Keep answer under 100 words
- Avoid long paragraphs
- Be concise
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
            # V3 RESULT CARDS
            # ===============================

            st.markdown("## 🧠 AI Decision Analysis")

            sections = {}
            current_title = None

            for line in result.splitlines():

                line = line.strip()

                if not line:
                    continue

                if line.endswith(":") and len(line) < 40:
                    current_title = line[:-1]
                    sections[current_title] = ""

                elif current_title:
                    sections[current_title] += line + "\n"

            summary = sections.get("Decision Summary",
                      sections.get("Comparison Summary", "Not available")).strip()

            best_option = sections.get("Best Option",
                         sections.get("Better Option", "Not available")).strip()

            risk_level = sections.get("Risk Level",
                         sections.get("Risk Comparison", "Not available")).strip()

            decision_score = sections.get("Decision Score",
                             sections.get("Option A Score", "Not available")).strip()

            next_step = sections.get("First Next Step", "Not available").strip()
            confidence_level = sections.get("Confidence Level", "Not available").strip()

            st.markdown("### Decision Summary")
            st.info(summary)

            col1, col2, col3, col4 = st.columns(4)

            col1.metric("Best Choice", best_option)
            col2.metric("Risk Level", risk_level)
            col3.metric("Score", decision_score)
            col4.metric("Confidence", confidence_level)
if confidence_level and confidence_level != "Not available":
   try:
      confidence_number = int(confidence_level.replace("%", "").strip())
      st.markdown("### Confidence Meter")
      st.progress(confidence_number)
  except:
      pass
if "Option A Score" in sections or "Option B Score" in sections:

    st.markdown("### Comparison Scores")

    c1, c2 = st.columns(2)

    c1.metric("Option A Score",
              sections.get("Option A Score", "N/A").strip())

    c2.metric("Option B Score",
              sections.get("Option B Score", "N/A").strip())

            if "Why" in sections:
                st.markdown("### Why")
                st.write(sections["Why"].strip())

            st.markdown("### First Next Step")
            st.success(next_step)

        except Exception:

            st.error("Decedo is facing high traffic right now. Please try again later.")

    else:

        st.warning("Please enter a decision question first.")

# ===============================
# HISTORY
# ===============================

if st.session_state.history:

    st.markdown("---")
    st.markdown("## 📜 Recent Decisions")

    for item in reversed(st.session_state.history[-5:]):

        with st.expander(item["question"]):
            st.write(item["answer"])






