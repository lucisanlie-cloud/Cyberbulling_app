"""
auth.py
-------
Authentication module for CyberShield AI.
Dark purple/black gradient theme login screen.

Author: Luci Jabba
Copyright (c) 2026 Luci Jabba
"""

import streamlit as st
from .database import create_user, login_user


def init_session_state() -> None:
    defaults = {"logged_in": False, "username": ""}
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def logout() -> None:
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.rerun()


def render_auth_screen(conn) -> None:
    # Centered login card
    st.markdown("""
    <div style="
        max-width: 440px;
        margin: 4rem auto 0 auto;
        text-align: center;
    ">
        <div style="font-size:4rem; filter: drop-shadow(0 0 20px rgba(168,85,247,0.8)); margin-bottom:0.5rem;">🛡</div>
        <h1 style="
            font-family:'Syne',sans-serif;
            font-weight:800;
            font-size:2.4rem;
            background: linear-gradient(135deg, #f0e8ff 0%, #a855f7 50%, #7c3aed 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin: 0 0 0.3rem 0;
        ">CyberShield AI</h1>
        <p style="color:#a594c0; font-family:'DM Sans',sans-serif; font-size:0.95rem; margin-bottom:2rem;">
            AI-Powered Cyberbullying Detection Platform
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Card container
    col_left, col_center, col_right = st.columns([1, 2, 1])
    with col_center:
        st.markdown("""
        <div style="
            background: linear-gradient(135deg, rgba(26,16,48,0.95), rgba(17,10,31,0.95));
            border: 1px solid rgba(124,58,237,0.3);
            border-radius: 20px;
            padding: 2rem 2rem 1.5rem 2rem;
            box-shadow: 0 20px 60px rgba(0,0,0,0.6), 0 0 40px rgba(124,58,237,0.1);
        ">
        """, unsafe_allow_html=True)

        tab_login, tab_signup = st.tabs(["🔑  Log In", "✨  Create Account"])

        with tab_login:
            st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
            username = st.text_input("Username", key="login_user", placeholder="Enter your username")
            password = st.text_input("Password", type="password", key="login_pass", placeholder="Enter your password")
            st.markdown("<div style='height:0.3rem'></div>", unsafe_allow_html=True)

            if st.button("Sign In →", key="btn_login", use_container_width=True):
                if not username or not password:
                    st.warning("Please fill in all fields.")
                    return
                if login_user(conn, username, password):
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.success("Welcome back! ✨")
                    st.rerun()
                else:
                    st.error("Incorrect username or password.")

        with tab_signup:
            st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
            new_user = st.text_input("Username", key="signup_user", placeholder="Choose a username")
            new_pass = st.text_input("Password", type="password", key="signup_pass", placeholder="Create a password")
            confirm_pass = st.text_input("Confirm password", type="password", key="signup_confirm", placeholder="Repeat your password")
            st.markdown("<div style='height:0.3rem'></div>", unsafe_allow_html=True)

            if st.button("Create Account →", key="btn_signup", use_container_width=True):
                if not new_user or not new_pass:
                    st.warning("Please fill in all fields.")
                    return
                if new_pass != confirm_pass:
                    st.error("Passwords do not match.")
                    return
                if len(new_pass) < 6:
                    st.warning("Password must be at least 6 characters long.")
                    return
                success = create_user(conn, new_user, new_pass)
                if success:
                    st.success("Account created! You can now log in.")
                else:
                    st.error("Username already exists. Please choose another.")

        st.markdown("</div>", unsafe_allow_html=True)

    # Footer
    st.markdown("""
    <div style="text-align:center; margin-top:2rem; color:#6b5e80; font-size:0.78rem; font-family:'DM Sans',sans-serif;">
        © 2026 Luci Jabba · CyberShield AI · All rights reserved
    </div>
    """, unsafe_allow_html=True)
