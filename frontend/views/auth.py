"""Functional account screens backed by the FlowState auth API."""
from __future__ import annotations

import re
import streamlit as st

import components as ui
from api_client import ApiError, auth_login, auth_logout, auth_me, auth_signup


def _shell(title: str, subtitle: str, form) -> None:
    left, right = st.columns([1.05, .95], gap="large", vertical_alignment="center")
    with left:
        ui.render(
            '<div class="fs-auth-brand"><div class="fs-auth-mark">F</div>'
            '<div class="fs-eyebrow">FLOWSTATE ACCOUNT</div>'
            '<h1>Protection that moves with you.</h1>'
            '<p>Keep your forecasts and support activity together in one secure account.</p>'
            '<div class="fs-auth-points"><div><span>01</span><strong>Weather-aware forecasts</strong></div>'
            '<div><span>02</span><strong>Clear support options</strong></div>'
            '<div><span>03</span><strong>Payout activity in one place</strong></div></div></div>'
        )
    with right:
        with st.container(border=True):
            st.markdown(f'<div class="fs-auth-heading"><div class="fs-eyebrow">FLOWSTATE</div><h2>{title}</h2><p>{subtitle}</p></div>', unsafe_allow_html=True)
            form()


def login() -> None:
    def form() -> None:
        with st.form("login_form"):
            email = st.text_input("Email address", placeholder="you@example.com")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Log in", type="primary", use_container_width=True)
        if submitted:
            if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email.strip()):
                st.error("Enter a valid email address.")
            elif not password:
                st.error("Enter your password.")
            else:
                try:
                    result = auth_login(email, password)
                    st.session_state.auth_token = result["token"]
                    st.session_state.auth_user = result["user"]
                    st.session_state.view = "profile"
                    st.rerun()
                except ApiError as exc:
                    st.error(str(exc))
        st.caption("New to FlowState?")
        if st.button("Create an account", key="auth_to_signup"):
            st.session_state.view = "signup"
            st.rerun()
    _shell("Welcome back", "Log in to view your protection account.", form)


def signup() -> None:
    def form() -> None:
        with st.form("signup_form"):
            name = st.text_input("Full name", placeholder="Your name")
            email = st.text_input("Email address", placeholder="you@example.com")
            password = st.text_input("Password", type="password", help="Use at least 10 characters.")
            confirm = st.text_input("Confirm password", type="password")
            submitted = st.form_submit_button("Create account", type="primary", use_container_width=True)
        if submitted:
            if len(name.strip()) < 2:
                st.error("Enter your name.")
            elif not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email.strip()):
                st.error("Enter a valid email address.")
            elif len(password) < 10:
                st.error("Password must be at least 10 characters.")
            elif password != confirm:
                st.error("Passwords do not match.")
            else:
                try:
                    result = auth_signup(name.strip(), email.strip(), password)
                    st.session_state.auth_token = result["token"]
                    st.session_state.auth_user = result["user"]
                    st.session_state.view = "profile"
                    st.rerun()
                except ApiError as exc:
                    st.error(str(exc))
        st.caption("Already have an account?")
        if st.button("Log in", key="auth_to_login"):
            st.session_state.view = "login"
            st.rerun()
    _shell("Create your account", "A few details to get started.", form)


def profile() -> None:
    token = st.session_state.get("auth_token")
    if not token:
        st.info("Log in or create an account to view your profile.")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Log in", type="primary", use_container_width=True):
                st.session_state.view = "login"
                st.rerun()
        with col2:
            if st.button("Create account", use_container_width=True):
                st.session_state.view = "signup"
                st.rerun()
        return
    try:
        user = auth_me(token)
        st.session_state.auth_user = user
    except ApiError:
        st.session_state.auth_token = None
        st.session_state.auth_user = None
        st.warning("Your session has expired. Please sign in again.")
        if st.button("Go to login"):
            st.session_state.view = "login"
            st.rerun()
        return
    ui.page_header("Your account", f"Welcome, {user['name']}.", "Manage your FlowState account details.")
    ui.render('<div class="fs-card">')
    st.text_input("Name", value=user["name"], disabled=True)
    st.text_input("Email", value=user["email"], disabled=True)
    ui.render('</div>')
    if st.button("Log out", key="auth_logout"):
        try:
            auth_logout(token)
        finally:
            st.session_state.auth_token = None
            st.session_state.auth_user = None
            st.session_state.view = "overview"
            st.rerun()
