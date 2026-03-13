import streamlit as st
from datetime import datetime
from zoneinfo import ZoneInfo
from supabase import create_client, Client

st.set_page_config(page_title="Profile - Decedo", page_icon="🧠", layout="wide")

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
    .top-card {
        background: linear-gradient(135deg, #0f172a 0%, #1d4ed8 100%);
        border-radius: 26px;
        padding: 30px;
        color: white;
        box-shadow: 0 18px 40px rgba(15, 23, 42, 0.18);
        margin-bottom: 20px;
    }
    .glass-card {
        background: rgba(255,255,255,0.96);
        border: 1px solid #e5e7eb;
        border-radius: 22px;
        padding: 22px;
        box-shadow: 0 8px 24px rgba(15, 23, 42, 0.07);
    }
    .plan-box {
        background: #eff6ff;
        border: 1px solid #bfdbfe;
        border-radius: 18px;
        padding: 16px;
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
SUPABASE_SERVICE_ROLE_KEY = st.secrets["SUPABASE_SERVICE_ROLE_KEY"]

supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
admin_supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

if not st.session_state.get("authenticated", False):
    st.switch_page("app.py")

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

def ensure_profile():
    existing = get_profile()
    if existing:
        return existing
    try:
        admin_supabase.table("profiles").upsert({
            "user_id": user_id,
            "email": user_email,
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
        }).eq("user_id", user_id).execute()
        return True
    except Exception:
        return False

def get_subscription():
    try:
        result = admin_supabase.table("subscriptions").select("*").eq("user_id", user_id).limit(1).execute()
        if result.data:
            return result.data[0]
    except Exception:
        pass
    return {"plan": "free", "status": "active"}

def get_usage():
    try:
        result = admin_supabase.table("usage_tracking").select("*").eq("user_id", user_id).limit(1).execute()
        if result.data:
            return result.data[0]
    except Exception:
        pass
    return {"reports_today": 0}

profile = ensure_profile()
subscription = get_subscription()
usage = get_usage()

username_value = profile["username"] if profile and profile.get("username") else ""

with st.sidebar:
    st.title("🧠 Decedo")
    st.caption(f"Logged in as: {user_email}")
    st.divider()
    if st.button("Go to Decision Lab", use_container_width=True, type="primary"):
        st.switch_page("pages/2_Decision_Lab.py")
    if st.button("Logout", use_container_width=True):
        logout_user()
        st.session_state.authenticated = False
        st.session_state.user_email = None
        st.session_state.user_id = None
        st.switch_page("app.py")

st.markdown(f"""
<div class="top-card">
    <div style="font-size:34px;font-weight:800;">👤 Profile</div>
    <div style="font-size:18px;font-weight:600;margin-top:6px;">
        {username_value if username_value else "Set your Decedo username"}
    </div>
    <div style="font-size:14px;opacity:0.9;margin-top:8px;">
        Personalize your Decedo identity, view your current plan, and manage your account.
    </div>
</div>
""", unsafe_allow_html=True)

col1, col2 = st.columns([1.1, 0.9], gap="large")

with col1:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown("### Account identity")
    new_username = st.text_input("Choose your username", value=username_value, placeholder="Example: swayam")
    if st.button("Save Username", use_container_width=True):
        if update_username(new_username):
            st.success("Username updated.")
            st.rerun()
        else:
            st.error("Could not update username.")
    st.markdown(f"**Email:** {user_email}")
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown("### Account overview")
    st.markdown(f"""
    <div class="plan-box">
        <div style="font-size:13px;font-weight:700;color:#1d4ed8;">Current Plan</div>
        <div style="font-size:28px;font-weight:800;color:#0f172a;">{subscription.get("plan", "free").title()}</div>
        <div style="margin-top:8px;font-size:14px;color:#334155;">
            Status: {subscription.get("status", "active").title()}
        </div>
        <div style="margin-top:8px;font-size:14px;color:#334155;">
            Usage Today: {usage.get("reports_today", 0)}
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("")
if st.button("Open Decision Lab", type="primary", use_container_width=True):
    st.switch_page("pages/2_Decision_Lab.py")
