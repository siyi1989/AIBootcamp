import streamlit as st


def require_login(allowed_roles=None):
    """Stop page execution if the user isn't logged in or lacks the right role.

    Call this at the very top of every page in pages/.
    """
    if not st.session_state.get("authenticated"):
        st.warning("Please log in from the main page first.")
        st.stop()
    if allowed_roles and st.session_state.get("role") not in allowed_roles:
        st.error("You do not have permission to view this page.")
        st.stop()
