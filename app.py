import streamlit as st
from supabase import create_client, Client

st.set_page_config(
    page_title="Decedo",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

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
    .auth-card {
        background: rgba(255,255,255,0.95);
        border: 1px solid #e5e7eb;
        border-radius: 24px;
        padding: 24px;
        box-shadow: 0 10px 30px rgba(15, 23, 42, 0.08);
    }
    .stButton>button {
        border-radius: 14px;
        font-weight: 700;
        height: 3em;
    }
    .stTextInput>div>div>input {
        border-radius: 12px;
    }
</style>
""", unsafe_allow_html=True)

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_ANON_KEY = st.secrets["SUPABASE_ANON_KEY"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "user_email" not in st.session_state:
    st.session_state.user_email = None
if "user_id" not in st.session_state:
    st.session_state.user_id = None

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

if st.session_state.authenticated:
    st.success("Already logged in")
    st.stop()
st.markdown("""
<div class="hero">
    <div style="font-size:38px;font-weight:800;">🧠 Decedo</div>
    <div style="font-size:20px;font-weight:600;margin-top:6px;">
        AI Operating System for Decisions
    </div>
    <div style="font-size:15px;opacity:0.9;margin-top:10px;max-width:760px;">
        Structured reasoning, scenario simulation, strategic insight, and premium downloadable reports.
    </div>
</div>
""", unsafe_allow_html=True)

left, right = st.columns([1.15, 0.85], gap="large")

with left:
    st.markdown("""
    <div class="auth-card">
        <h2 style="margin-top:0;">Why Decedo feels premium</h2>
        <p>• Decision intelligence dashboard</p>
        <p>• AI debate mode</p>
        <p>• Scenario simulation</p>
        <p>• Strategic insights</p>
        <p>• Premium PDF reports</p>
    </div>
    """, unsafe_allow_html=True)

with right:
    st.markdown('<div class="auth-card">', unsafe_allow_html=True)
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
                st.success("Login successful.")
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
                    st.success("Account created. Please log in.")
                else:
                    st.error(str(result))

    st.markdown('</div>', unsafe_allow_html=True)


