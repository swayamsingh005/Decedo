import streamlit as st
import google.genai as genai

# =========================
# CONFIG
# =========================
client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

st.set_page_config(
    page_title="Decedo",
    page_icon="🧠",
    layout="wide"
) 
# =========================
# SIMPLE STYLING
# =========================
st.markdown("""
<style>
.main {
    padding-top: 20px;
}
.card {
    background-color: #1e1e1e;
    padding: 18px;
    border-radius: 16px;
    margin-bottom: 16px;
    border: 1px solid #333333;
}
.card h3 {
    margin-top: 0;
}
.hero-box {
    background: linear-gradient(135deg, #1f1f1f, #111111);
    padding: 24px;
    border-radius: 20px;
    border: 1px solid #333333;
    margin-bottom: 20px;
}
.small-text {
    color: #bbbbbb;
}
</style>
""", unsafe_allow_html=True)

# =========================
# SESSION HISTORY
# =========================
if "history" not in st.session_state:
    st.session_state.history = []

# =========================
# HEADER
# =========================
st.markdown("""
<div class="hero-box">
    <h1>🧠 Decedo</h1>
    <h3>AI Decision Intelligence</h3>
    <p class="small-text">
        Make smarter decisions using AI-powered structured analysis.
    </p>
</div>
""", unsafe_allow_html=True)

# =========================
# EXAMPLES
# =========================
example_questions = [
    "",
    "Should I start a startup or take a job?",
    "Should I focus on studies first or build a business side by side?",
    "Should I learn coding or marketing first for my startup journey?",
    "Should I invest money in skills or save it for business?"
]

selected_example = st.selectbox("Try an example question", example_questions)
decision_type = st.selectbox(
    "Decision Type",
    ["Career", "Business", "Money", "Studies", "Personal"]
)
question = st.text_area(
    "Enter your decision question:",
    value=selected_example,
    placeholder="Example: Should I start a startup or take a job?",
    height=120
)

# =========================
# ANALYZE
# =========================
if st.button("Analyze Decision", type= "primary",use_container_width=True):
    if question.strip():
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

Why:
- Give 2 short bullet points only

Risk Level:
Low / Medium / High

Decision Score:
Score out of 10

First Next Step:
Give 1 practical next action.

Rules:
- Keep the answer under 100 words
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

            st.success("Analysis generated successfully.")

            st.markdown("## 🧠 AI Decision Analysis")

            sections = result.split("##")
            for section in sections:
                if section.strip():
                    lines = section.strip().split("\n")
                    title = lines[0]
                    content = "\n".join(lines[1:]).strip()

                    st.markdown(f"""
                    <div class="card">
                        <h3>{title}</h3>
                        <p>{content}</p>
                    </div>
                    """, unsafe_allow_html=True)

        except Exception as e:
            st.error("Something went wrong while generating the AI response.")
            st.code(str(e))
    else:
        st.warning("Please enter a decision question first.")

# =========================
# HISTORY
# =========================
if st.session_state.history:
    st.markdown("## 📜 Recent Decisions")

    for item in reversed(st.session_state.history[-5:]):
        with st.expander(item["question"]):

            st.write(item["answer"])




