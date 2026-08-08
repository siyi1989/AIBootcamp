import os
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

# OpenAI API key is read directly from the OPENAI_API_KEY environment variable.
if not os.getenv("OPENAI_API_KEY"):
    st.warning("OPENAI_API_KEY is not set. The app will fail to generate responses until it is configured.")

st.set_page_config(
    page_title="CAAS Fees Legislation Assistant",
    page_icon="✈️",
    layout="wide",
)

# ---------- Required Disclaimer (shown on every page) ----------
with st.expander("⚠️ Required Disclaimer — Please Read", expanded=False):
    st.markdown(
        """
**IMPORTANT NOTICE:** This web application is developed as a proof-of-concept
prototype. The information provided here is **NOT intended for actual usage**
and should not be relied upon for making any decisions, especially those
related to financial, legal, or healthcare matters.

**Furthermore, please be aware that the LLM may generate inaccurate or
incorrect information. You assume full responsibility for how you use any
generated output.**

Always consult with qualified professionals for accurate and personalised
advice.
        """
    )

# ---------- Session state defaults ----------
for key, default in {
    "authenticated": False,
    "role": None,
    "username": None,
    "chat_history": [],
    "login_error": "",
}.items():
    if key not in st.session_state:
        st.session_state[key] = default


def check_login(username: str, password: str):
    admin_user = os.getenv("ADMIN_USERNAME", "admin").strip()
    admin_pass = os.getenv("ADMIN_PASSWORD", "admin123").strip()
    username = (username or "").strip()
    password = (password or "").strip()
    if username == admin_user and password == admin_pass:
        return "Admin"
    return None


def do_login():
    username = st.session_state.get("login_username", "")
    password = st.session_state.get("login_password", "")
    role = check_login(username, password)
    if role:
        st.session_state.authenticated = True
        st.session_state.role = role
        st.session_state.username = username
        st.session_state.login_error = ""
    else:
        st.session_state.authenticated = False
        st.session_state.role = None
        st.session_state.username = None
        st.session_state.login_error = "Invalid username or password."
    st.rerun()


# ---------- Admin login lives in the sidebar so the main page can be chat ----------
with st.sidebar:
    if not st.session_state.authenticated:
        with st.expander("🔐 Admin Login"):
            with st.form("login_form"):
                st.text_input("Username", key="login_username")
                st.text_input("Password", type="password", key="login_password")
                st.form_submit_button("Log in", on_click=do_login)
                if st.session_state.login_error:
                    st.error(st.session_state.login_error)
    else:
        st.success(f"Logged in as **{st.session_state.username}** (Admin)")
        if st.button("Log out"):
            st.session_state.authenticated = False
            st.session_state.role = None
            st.session_state.username = None
            st.rerun()

# ---------- Pages visible to everyone ----------
chat_page = st.Page("pages/1_Chat_Assistant.py", title="Chat Assistant", icon="💬", default=True)
about_page = st.Page("pages/3_About_Us.py", title="About Us", icon="ℹ️")
methodology_page = st.Page("pages/4_Methodology.py", title="Methodology", icon="🔍")
fee_register_page = st.Page("pages/5_Fee_Register.py", title="Fee Register", icon="📊")

pages = [chat_page, about_page, methodology_page, fee_register_page]

# ---------- Admin-only page: only added to the nav once logged in ----------
if st.session_state.role == "Admin":
    admin_page = st.Page("pages/2_Admin_Upload.py", title="Admin Upload", icon="📤")
    pages.append(admin_page)

pg = st.navigation(pages)
pg.run()