"""FlowState dashboard shell: navigation, header, dialogs and routing.

Run with:  streamlit run app.py
"""

from __future__ import annotations

import streamlit as st

from api_client import API_BASE_URL
from format import inr, short_hash
from api_client import auth_logout
import components as ui
import state
import theme
from views import auth, guide, overview, payouts, storm, workers

st.set_page_config(
    page_title="FlowState · Income protection",
    layout="wide",
    initial_sidebar_state="collapsed",
)

theme.apply()
state.init()

NAV = [
    ("overview", "Overview", "Command centre"),
    ("workers", "Workers", "Risk board"),
    ("storm", "Storm console", "Payout demo"),
    ("payouts", "Payouts", "Ledger"),
    ("guide", "How it works", "Pipeline and rules"),
]

VIEWS = {
    "overview": overview.render,
    "workers": workers.render,
    "storm": storm.render,
    "payouts": payouts.render,
    "guide": guide.render,
    "login": auth.login,
    "signup": auth.signup,
    "profile": auth.profile,
}


# --- dialogs ----------------------------------------------------------------


@st.dialog("Accept loan offer")
def _loan_dialog() -> None:
    pending = st.session_state.pending_loan
    if not pending:
        st.session_state.dialog = None
        st.rerun()
        return
    st.write(
        f"Accept the backend's loan offer of **{inr(pending.get('amount'))}** for "
        f"{pending.get('name')}? Repayment comes from a capped share of future earnings."
    )
    st.caption("The backend re-checks eligibility and returns the updated worker ledger.")
    confirm, cancel = st.columns(2)
    with confirm:
        if st.button("Accept loan", type="primary", use_container_width=True):
            st.session_state.dialog = None
            st.session_state.pending_loan = None
            with st.spinner("Accepting loan and reloading the ledger…"):
                state.accept_loan(int(pending["worker_id"]))
            st.rerun()
    with cancel:
        if st.button("Cancel", use_container_width=True):
            st.session_state.dialog = None
            st.session_state.pending_loan = None
            st.rerun()


@st.dialog("Confirm storm protection run")
def _storm_dialog() -> None:
    st.write("Run the severe-weather protection flow for every eligible worker?")
    st.caption("The backend records eligible payouts and returns their settlement status.")
    confirm, cancel = st.columns(2)
    with confirm:
        if st.button("Run storm simulation", type="primary", use_container_width=True):
            st.session_state.dialog = None
            with st.spinner("Processing eligible payouts…"):
                state.run_storm()
            st.rerun()
    with cancel:
        if st.button("Cancel", use_container_width=True):
            st.session_state.dialog = None
            st.rerun()


# --- navigation -------------------------------------------------------------


def _navbar() -> None:
    with st.container(key="fs-navbar"):
        brand_col, links_col, account_col = st.columns(
            [1.35, 4.8, 1.8], vertical_alignment="center", gap="large"
        )
        with brand_col:
            ui.render(
                '<div class="fs-brand"><span class="fs-brand-mark">F</span>'
                '<span class="fs-brand-name">FlowState</span></div>'
            )
        with links_col:
            nav_cols = st.columns([1, 0.9, 1.25, 0.8, 1.35], gap="small")
            for column, (key, label, _hint) in zip(nav_cols, NAV):
                active = st.session_state.view == key
                with column:
                    if st.button(label, key=f"nav_{key}", use_container_width=True,
                                 type="primary" if active else "secondary"):
                        st.session_state.view = key
                        st.rerun()
        with account_col:
            if st.session_state.get("auth_token"):
                profile_col, logout_col = st.columns([1, 1], gap="small")
                with profile_col:
                    if st.button("Profile", key="nav_profile", use_container_width=True):
                        st.session_state.view = "profile"
                        st.rerun()
                with logout_col:
                    if st.button("Log out", key="nav_logout", use_container_width=True):
                        try:
                            auth_logout(st.session_state.auth_token)
                        finally:
                            st.session_state.auth_token = None
                            st.session_state.auth_user = None
                            st.session_state.view = "overview"
                            st.rerun()
            else:
                login_col, signup_col = st.columns([0.8, 1.2], gap="small")
                with login_col:
                    if st.button("Log in", key="nav_login", use_container_width=True):
                        st.session_state.view = "login"
                        st.rerun()
                with signup_col:
                    if st.button("Create account", key="nav_signup", type="primary",
                                 use_container_width=True):
                        st.session_state.view = "signup"
                        st.rerun()


# --- header -----------------------------------------------------------------


def _backend_down() -> None:
    st.markdown("<div style='height:8vh'></div>", unsafe_allow_html=True)
    ui.render(
        '<div class="fs-card" style="padding:30px 32px">'
        '<div class="fs-eyebrow">Connection needed</div>'
        '<h1 class="fs-page-title" style="margin-top:8px">The backend is not answering.</h1>'
        '<p class="fs-page-sub">FlowState renders only what the API returns, so there is no '
        "offline mock data on this screen. Start the FastAPI service, then retry.</p>"
        "</div>"
    )
    st.error(st.session_state.health_error or f"Cannot reach {API_BASE_URL}")
    if st.button("Retry connection", type="primary"):
        with st.spinner("Reconnecting…"):
            state.refresh_all()
        st.rerun()


# --- boot -------------------------------------------------------------------

if st.session_state.health is None and not st.session_state.health_error:
    with st.spinner("Connecting to the FlowState backend…"):
        state.refresh_all()

if st.session_state.health is None:
    _backend_down()
    st.stop()

_navbar()


def _render_dashboard() -> None:
    VIEWS.get(st.session_state.view, overview.render)()
    ui.footer()


_render_dashboard()

if st.session_state.dialog == "loan":
    _loan_dialog()
elif st.session_state.dialog == "storm":
    _storm_dialog()
