"""FlowState design system: colour tokens, typography and the global stylesheet.

Streamlit ships a generic look, so the visual language lives in one place here and
every view renders against these tokens. Keep this file free of business logic.
"""

from __future__ import annotations

import streamlit as st

# --- tokens -----------------------------------------------------------------

PALETTE = {
    "canvas": "#F8FAFC",
    "surface": "#FFFFFF",
    "surface_sunk": "#F1F5F9",
    "ink": "#0F172A",
    "ink_soft": "#334155",
    "muted": "#64748B",
    "hairline": "#E2E8F0",
    "hairline_strong": "#CBD5E1",
    "accent": "#0F766E",
    "accent_ink": "#115E59",
    "accent_soft": "#CCFBF1",
    "amber": "#A16207",
    "amber_soft": "#FEF3C7",
    "danger": "#B91C1C",
    "danger_soft": "#FEE2E2",
    "slate_soft": "#F1F5F9",
}

FONT_IMPORT = (
    "@import url('https://fonts.googleapis.com/css2?"
    "family=Inter:wght@400;500;600;700&"
    "family=IBM+Plex+Mono:wght@400;500&display=swap');"
)

CSS = (
    FONT_IMPORT
    + """
:root {
  --fs-canvas: #F8FAFC;
  --fs-surface: #FFFFFF;
  --fs-sunk: #F1F5F9;
  --fs-ink: #0F172A;
  --fs-ink-soft: #334155;
  --fs-muted: #64748B;
  --fs-line: #E2E8F0;
  --fs-line-strong: #CBD5E1;
  --fs-accent: #0F766E;
  --fs-accent-ink: #115E59;
  --fs-accent-soft: #CCFBF1;
  --fs-amber: #A16207;
  --fs-amber-soft: #FEF3C7;
  --fs-danger: #B91C1C;
  --fs-danger-soft: #FEE2E2;
  --fs-slate-soft: #F1F5F9;
  --fs-radius: 10px;
  --fs-shadow: 0 1px 3px rgba(15, 23, 42, 0.06);
}

html, body, [class*="css"], .stApp, .stMarkdown, p, li, span, div {
  font-family: 'Inter', 'Segoe UI', system-ui, -apple-system, sans-serif;
}

.stApp {
  background: var(--fs-canvas);
  color: var(--fs-ink);
  -webkit-font-smoothing: antialiased;
  min-height: 100vh;
}

[data-testid="stHeader"] { background: transparent; height: 0; }
[data-testid="stToolbar"], [data-testid="stStatusWidget"] { display: none !important; }
[data-testid="stDecoration"] { display: none; }
#MainMenu, footer { visibility: hidden; }

[data-testid="stMainBlockContainer"], .block-container {
  max-width: 100vw !important;
  width: 100%;
  padding: 1rem clamp(16px, 2.4vw, 42px) 3rem;
}
[data-testid="stSidebar"], [data-testid="collapsedControl"] { display: none !important; }
[data-testid="stAppViewContainer"] { width: 100%; min-height: 100vh; }
.st-key-fs-navbar {
  position: sticky;
  top: 0;
  z-index: 1000;
  background: rgba(255, 255, 255, 0.92);
  backdrop-filter: blur(14px);
  -webkit-backdrop-filter: blur(14px);
  border-bottom: 1px solid rgba(203, 213, 225, 0.8);
  padding: 10px 0 8px;
  margin-bottom: 24px;
  transition: box-shadow 180ms ease, background 180ms ease;
}
.fs-brand { display: flex; align-items: center; gap: 10px; min-height: 42px; }
.fs-brand-mark { display: grid; place-items: center; width: 34px; height: 34px; border-radius: 9px; background: #0F766E; color: white; font-size: 18px; font-weight: 700; letter-spacing: -0.06em; }
.fs-brand-name { color: #0F172A; font-size: 19px; font-weight: 700; letter-spacing: -0.04em; }

[data-testid="stAppViewContainer"] > .main { background: transparent; }

/* --- typography ---------------------------------------------------------- */

.fs-eyebrow {
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--fs-accent);
}
.fs-page-title {
  font-family: 'Inter', 'Segoe UI', system-ui, sans-serif;
  font-size: clamp(28px, 2.7vw, 36px);
  line-height: 1.15;
  letter-spacing: -0.025em;
  color: var(--fs-ink);
  margin: 6px 0 8px;
  font-weight: 400;
}
.fs-page-sub {
  color: var(--fs-muted);
  font-size: 15px;
  line-height: 1.62;
  max-width: 62ch;
  margin: 0;
}
.fs-hero-copy { padding: 26px 0 30px; }
.fs-hero-title { color: var(--fs-ink); font-size: clamp(38px, 5vw, 58px); font-weight: 700; line-height: 1.04; letter-spacing: -0.055em; margin: 12px 0 16px; }
.fs-hero-sub { color: var(--fs-muted); font-size: 16px; line-height: 1.7; max-width: 58ch; margin: 0; }
.fs-hero-trust { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; color: var(--fs-ink-soft); font-size: 12px; font-weight: 600; margin-top: 22px; }
.fs-hero-trust i { width: 4px; height: 4px; border-radius: 50%; background: var(--fs-accent); }
.fs-hero-card { background: linear-gradient(145deg, #FFFFFF 35%, #F0FDFA); border: 1px solid var(--fs-line); border-radius: 14px; padding: 24px; box-shadow: 0 12px 34px rgba(15, 23, 42, 0.07); }
.fs-hero-card-top { display: flex; align-items: flex-start; justify-content: space-between; gap: 12px; }
.fs-card-kicker { color: var(--fs-muted); font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: .1em; }
.fs-hero-card-title { color: var(--fs-ink); font-size: 22px; font-weight: 650; margin-top: 4px; }
.fs-hero-weather { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin: 22px 0; }
.fs-hero-weather > div { background: #FFFFFF; border: 1px solid var(--fs-line); border-radius: 8px; padding: 12px 14px; }
.fs-hero-weather span { display: block; color: var(--fs-muted); font-size: 11px; }
.fs-hero-weather strong { display: block; color: var(--fs-ink); font-size: 21px; font-variant-numeric: tabular-nums; margin-top: 3px; }
.fs-hero-chart-label { color: var(--fs-ink-soft); font-size: 12px; font-weight: 600; margin: 0 0 10px; }
.fs-activity-row { display: flex; align-items: center; justify-content: space-between; gap: 14px; padding: 14px 16px; background: var(--fs-surface); border: 1px solid var(--fs-line); border-bottom: 0; }
.fs-activity-row:first-of-type { border-radius: 8px 8px 0 0; }
.fs-activity-row:last-of-type { border-bottom: 1px solid var(--fs-line); border-radius: 0 0 8px 8px; }
.fs-activity-row > div:first-child { min-width: 0; }
.fs-activity-row strong { display: block; color: var(--fs-ink); font-size: 13px; }
.fs-activity-row span { display: block; color: var(--fs-muted); font-size: 11px; margin-top: 3px; overflow-wrap: anywhere; }
.fs-activity-right { display: flex; align-items: center; gap: 12px; flex: none; }
.fs-section {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 16px;
  margin: 34px 0 14px;
  padding-bottom: 10px;
  border-bottom: 1px solid var(--fs-line);
}
.fs-section-title {
  font-size: 13px;
  font-weight: 650;
  letter-spacing: 0.02em;
  color: var(--fs-ink);
  margin: 0;
}
.fs-section-meta {
  font-size: 12px;
  color: var(--fs-muted);
  font-variant-numeric: tabular-nums;
}
.fs-mono {
  font-family: 'IBM Plex Mono', 'SFMono-Regular', Consolas, monospace;
  font-size: 12.5px;
  letter-spacing: -0.01em;
}

/* --- cards --------------------------------------------------------------- */

.fs-card {
  background: var(--fs-surface);
  border: 1px solid var(--fs-line);
  border-radius: var(--fs-radius);
  padding: 18px 20px;
  box-shadow: var(--fs-shadow);
  height: 100%;
}
.fs-card--flush { padding: 0; overflow: hidden; }
.fs-card-title {
  font-size: 13px;
  font-weight: 650;
  color: var(--fs-ink);
  margin: 0 0 2px;
}
.fs-card-note {
  font-size: 12.5px;
  color: var(--fs-muted);
  line-height: 1.55;
  margin: 0;
}

/* --- stat tiles ---------------------------------------------------------- */

.fs-stat {
  background: var(--fs-surface);
  border: 1px solid var(--fs-line);
  border-radius: var(--fs-radius);
  padding: 16px 18px 15px;
  box-shadow: var(--fs-shadow);
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: 4px;
  transition: transform 180ms ease, border-color 180ms ease, box-shadow 180ms ease;
}
.fs-stat:hover { transform: translateY(-2px); border-color: var(--fs-line-strong); box-shadow: 0 5px 14px rgba(15, 23, 42, 0.06); }
.fs-stat-top { display: flex; align-items: center; justify-content: space-between; gap: 8px; }
.fs-stat-badge { flex: none; }
.fs-stat-label {
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--fs-muted);
}
.fs-stat-value {
  font-size: 30px;
  font-weight: 600;
  letter-spacing: -0.032em;
  color: var(--fs-ink);
  line-height: 1.12;
  font-variant-numeric: tabular-nums;
}
.fs-stat-value--sm { font-size: 19px; letter-spacing: -0.02em; font-weight: 600; }
.fs-stat-meta {
  font-size: 12.5px;
  color: var(--fs-muted);
  line-height: 1.5;
}

/* --- badges -------------------------------------------------------------- */

.fs-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  border-radius: 4px;
  padding: 4px 8px;
  font-size: 11.5px;
  font-weight: 600;
  letter-spacing: 0.01em;
  border: 1px solid transparent;
  white-space: nowrap;
}
.fs-badge .dot {
  width: 6px; height: 6px; border-radius: 50%;
  background: currentColor; flex: none;
}
.fs-badge--ok      { background: var(--fs-accent-soft); color: var(--fs-accent-ink); border-color: #C6E3DD; }
.fs-badge--warn    { background: var(--fs-amber-soft);  color: var(--fs-amber);      border-color: #EFDCBB; }
.fs-badge--bad     { background: var(--fs-danger-soft); color: var(--fs-danger);     border-color: #F2CFC8; }
.fs-badge--idle    { background: var(--fs-slate-soft);  color: var(--fs-ink-soft);   border-color: #DCE3E6; }
.fs-badge--outline { background: transparent; color: var(--fs-ink-soft); border-color: var(--fs-line-strong); }

/* --- misc ---------------------------------------------------------------- */

.fs-hr { height: 1px; background: var(--fs-line); border: 0; margin: 18px 0; }
.fs-kv { display: flex; justify-content: space-between; gap: 14px; padding: 8px 0; font-size: 13px; }
.fs-kv + .fs-kv { border-top: 1px solid var(--fs-line); }
.fs-kv dt { color: var(--fs-muted); margin: 0; }
.fs-kv dd { color: var(--fs-ink); margin: 0; font-weight: 600; text-align: right; }
.fs-empty {
  border: 1px dashed var(--fs-line-strong);
  border-radius: var(--fs-radius);
  padding: 26px 22px;
  text-align: center;
  color: var(--fs-muted);
  font-size: 13.5px;
  background: rgba(255,255,255,0.55);
}
.fs-quote {
  font-family: 'Instrument Serif', Georgia, serif;
  font-size: 21px;
  line-height: 1.42;
  color: var(--fs-ink);
  margin: 0;
}
.fs-list { margin: 6px 0 0; padding-left: 18px; color: var(--fs-ink-soft); font-size: 13.5px; line-height: 1.65; }
.fs-footer { display: flex; justify-content: space-between; gap: 16px; flex-wrap: wrap; padding: 20px 0 4px; border-top: 1px solid var(--fs-line); color: var(--fs-muted); font-size: 12px; }
.fs-auth-brand { min-height: 500px; padding: 42px; border-radius: 16px; color: white; background: radial-gradient(circle at 90% 10%, rgba(45, 212, 191, .25), transparent 32%), linear-gradient(145deg, #0F172A, #115E59); display: flex; flex-direction: column; justify-content: center; box-shadow: 0 18px 48px rgba(15, 23, 42, .16); }
.fs-auth-mark { display: grid; place-items: center; width: 42px; height: 42px; margin-bottom: 42px; border: 1px solid rgba(255,255,255,.3); border-radius: 12px; color: white; font-size: 22px; font-weight: 700; }
.fs-auth-brand .fs-eyebrow { color: #99F6E4; }
.fs-auth-brand h1 { max-width: 12ch; margin: 12px 0; color: white; font-size: clamp(32px, 3.5vw, 46px); line-height: 1.1; letter-spacing: -.04em; }
.fs-auth-brand p { max-width: 42ch; color: #CBD5E1; font-size: 15px; line-height: 1.7; }
.fs-auth-points { display: grid; gap: 14px; margin-top: 40px; }
.fs-auth-points div { display: flex; align-items: center; gap: 12px; color: #F8FAFC; font-size: 13px; }
.fs-auth-points span { color: #99F6E4; font-family: 'IBM Plex Mono', monospace; font-size: 11px; }
.fs-auth-heading { margin-bottom: 20px; }
.fs-auth-heading h2 { margin: 6px 0; color: var(--fs-ink); font-size: 28px; letter-spacing: -.035em; }
.fs-auth-heading p { margin: 0; color: var(--fs-muted); font-size: 14px; line-height: 1.6; }
.fs-profile-card { min-height: 350px; padding: 38px; border: 1px solid var(--fs-line); border-radius: 14px; background: linear-gradient(150deg,#fff,#F0FDFA); }
.fs-profile-avatar { display: grid; place-items: center; width: 64px; height: 64px; margin-bottom: 28px; border: 1px solid var(--fs-line); border-radius: 50%; background: white; color: var(--fs-accent); font-size: 25px; font-weight: 650; }
.fs-profile-card h1 { margin: 10px 0; color: var(--fs-ink); font-size: 30px; line-height: 1.15; letter-spacing: -.035em; }
.fs-profile-card p { max-width: 45ch; color: var(--fs-muted); line-height: 1.7; }
.fs-list li { margin-bottom: 3px; }
"""
)
WIDGET_CSS = """
/* --- shell: sidebar rail -------------------------------------------------- */

[data-testid="stSidebar"] {
  background: var(--fs-surface);
  border-right: 1px solid var(--fs-line);
  width: 258px !important;
}
[data-testid="stSidebar"] > div:first-child { padding-top: 0.9rem; }
[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] { padding: 0.4rem 0.85rem 1.4rem; }
[data-testid="stSidebar"] hr { border-color: var(--fs-line); margin: 14px 0; }

[data-testid="stSidebar"] .stButton { margin: 0; }
[data-testid="stSidebar"] button,
[data-testid="stSidebar"] [data-testid="stBaseButton-secondary"],
[data-testid="stSidebar"] [data-testid="stBaseButton-primary"] {
  justify-content: flex-start;
  text-align: left;
  width: 100%;
  background: transparent;
  border: 1px solid transparent;
  border-radius: 5px;
  color: var(--fs-ink-soft);
  font-weight: 550;
  font-size: 13.5px;
  min-height: 38px;
  padding: 0.34rem 0.62rem;
  box-shadow: none;
  transition: background 0.14s ease, color 0.14s ease;
}
[data-testid="stSidebar"] button p,
[data-testid="stSidebar"] button div { text-align: left; font-size: 13.5px; }
[data-testid="stSidebar"] button:hover {
  background: var(--fs-sunk);
  color: var(--fs-ink);
  border-color: transparent;
}
[data-testid="stSidebar"] button[kind="primary"],
[data-testid="stSidebar"] [data-testid="stBaseButton-primary"] {
  background: var(--fs-accent-soft);
  color: var(--fs-accent-ink);
  font-weight: 640;
  border-color: transparent;
}
[data-testid="stSidebar"] button[kind="primary"]:hover,
[data-testid="stSidebar"] [data-testid="stBaseButton-primary"]:hover {
  background: #D6EBE6;
  color: var(--fs-accent-ink);
}

/* --- buttons (main canvas) ------------------------------------------------ */

.stButton > button,
.stDownloadButton > button,
[data-testid="stBaseButton-secondary"] {
  border-radius: 10px;
  border: 1px solid var(--fs-line-strong);
  background: var(--fs-surface);
  color: var(--fs-ink);
  font-weight: 600;
  font-size: 13.5px;
  min-height: 40px;
  padding: 0.46rem 0.95rem;
  box-shadow: none;
  transition: background 0.14s ease, border-color 0.14s ease, color 0.14s ease;
}
.stButton > button:hover,
[data-testid="stBaseButton-secondary"]:hover {
  background: #FBFCFA;
  border-color: var(--fs-ink-soft);
  color: var(--fs-ink);
}
.stButton > button:focus-visible { outline: 2px solid var(--fs-accent); outline-offset: 2px; }

/* Primary navigation links: understated labels with a clear active underline. */
.st-key-nav_overview button, .st-key-nav_workers button, .st-key-nav_storm button,
.st-key-nav_payouts button, .st-key-nav_guide button {
  position: relative;
  background: transparent !important; border: 0 !important; border-radius: 0 !important;
  color: var(--fs-muted) !important; box-shadow: none !important; min-height: 44px;
  transition: color 160ms ease, transform 160ms ease !important;
}
.st-key-nav_overview button::after, .st-key-nav_workers button::after,
.st-key-nav_storm button::after, .st-key-nav_payouts button::after,
.st-key-nav_guide button::after {
  content: ""; position: absolute; left: 12%; right: 12%; bottom: 3px; height: 2px;
  background: var(--fs-accent); transform: scaleX(0); transform-origin: center;
  transition: transform 180ms ease;
}
.st-key-nav_overview button:hover, .st-key-nav_workers button:hover, .st-key-nav_storm button:hover,
.st-key-nav_payouts button:hover, .st-key-nav_guide button:hover {
  background: transparent !important; color: var(--fs-ink) !important; transform: translateY(-1px);
}
.st-key-nav_overview button[kind="primary"], .st-key-nav_workers button[kind="primary"],
.st-key-nav_storm button[kind="primary"], .st-key-nav_payouts button[kind="primary"],
.st-key-nav_guide button[kind="primary"] {
  color: var(--fs-accent) !important;
}
.st-key-fs-navbar .stButton > button { white-space: nowrap; }
.st-key-nav_login button, .st-key-nav_profile button {
  background: transparent !important; border-color: transparent !important;
  box-shadow: none !important; color: var(--fs-ink-soft) !important;
}
.st-key-nav_login button:hover, .st-key-nav_profile button:hover {
  background: var(--fs-sunk) !important; color: var(--fs-ink) !important;
}
.st-key-nav_overview button[kind="primary"]::after, .st-key-nav_workers button[kind="primary"]::after,
.st-key-nav_storm button[kind="primary"]::after, .st-key-nav_payouts button[kind="primary"]::after,
.st-key-nav_guide button[kind="primary"]::after { transform: scaleX(1); }
.st-key-nav_signup button {
  border-radius: 7px !important;
  box-shadow: 0 3px 8px rgba(15, 118, 110, 0.16) !important;
  transition: transform 160ms ease, box-shadow 160ms ease, background 160ms ease !important;
}
.st-key-nav_signup button:hover {
  transform: translateY(-1px);
  box-shadow: 0 6px 14px rgba(15, 118, 110, 0.22) !important;
}

.stButton > button[kind="primary"],
[data-testid="stBaseButton-primary"] {
  background: var(--fs-accent);
  border-color: var(--fs-accent);
  color: #FFFFFF;
  font-weight: 620;
}
.stButton > button[kind="primary"]:hover,
[data-testid="stBaseButton-primary"]:hover {
  background: var(--fs-accent-ink);
  border-color: var(--fs-accent-ink);
  color: #FFFFFF;
}
.stButton > button:disabled,
[data-testid="stBaseButton-primary"]:disabled,
[data-testid="stBaseButton-secondary"]:disabled {
  background: var(--fs-sunk);
  border-color: var(--fs-line);
  color: #96A5AC;
  opacity: 1;
}

/* Keyed buttons: Streamlit exposes the widget key as a class on the container. */
.st-key-btn-danger button,
.st-key-btn-danger [data-testid="stBaseButton-secondary"] {
  background: var(--fs-danger);
  border-color: var(--fs-danger);
  color: #FFFFFF;
}
.st-key-btn-danger button:hover { background: #8C2115; border-color: #8C2115; color: #FFFFFF; }

.st-key-btn-storm button {
  background: var(--fs-danger);
  border-color: var(--fs-danger);
  color: #FFFFFF;
  min-height: 46px;
  font-size: 14.5px;
}
.st-key-btn-storm button:hover { background: #8C2115; border-color: #8C2115; color: #FFFFFF; }

/* --- containers ----------------------------------------------------------- */

[data-testid="stVerticalBlockBorderWrapper"] {
  background: var(--fs-surface);
  border: 1px solid var(--fs-line);
  border-radius: var(--fs-radius);
  box-shadow: var(--fs-shadow);
}
[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stVerticalBlockBorderWrapper"] {
  box-shadow: none;
  background: var(--fs-canvas);
}

/* --- form controls -------------------------------------------------------- */

[data-testid="stTextInput"] input,
[data-testid="stNumberInput"] input,
[data-testid="stSelectbox"] div[data-baseweb="select"] > div {
  border-radius: 10px;
  border-color: var(--fs-line-strong);
  background: var(--fs-surface);
  font-size: 13.5px;
  color: var(--fs-ink);
}
[data-testid="stTextInput"] input:focus,
[data-testid="stSelectbox"] div[data-baseweb="select"] > div:focus-within {
  border-color: var(--fs-accent);
  box-shadow: 0 0 0 3px rgba(11, 110, 102, 0.14);
}
[data-testid="stWidgetLabel"] p {
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--fs-muted);
}
[data-testid="stCheckbox"] label p, [data-testid="stToggle"] label p { font-size: 13px; }

/* --- feedback ------------------------------------------------------------- */

[data-testid="stAlert"] {
  border-radius: 12px;
  border: 1px solid var(--fs-line);
  font-size: 13.5px;
  padding: 12px 16px;
}
[data-testid="stAlert"] p { font-size: 13.5px; margin: 0; }

[data-testid="stExpander"] {
  border: 1px solid var(--fs-line);
  border-radius: 12px;
  background: var(--fs-surface);
  box-shadow: none;
}
[data-testid="stExpander"] summary { font-size: 13px; font-weight: 600; }
[data-testid="stExpander"] summary:hover { color: var(--fs-accent); }

[data-testid="stCode"] { border-radius: 10px; }
[data-testid="stCode"] code { font-size: 12.5px; }

[data-testid="stDataFrame"] {
  border: 1px solid var(--fs-line);
  border-radius: 12px;
  overflow: hidden;
}

[data-testid="stDivider"] hr { border-color: var(--fs-line); }

[data-testid="stDialog"] div[role="dialog"] {
  border-radius: 18px;
  border: 1px solid var(--fs-line);
  box-shadow: 0 24px 60px rgba(12, 36, 48, 0.18);
  padding: 6px 4px 2px;
}
[data-testid="stDialog"] h2 { font-size: 19px; letter-spacing: -0.02em; }

[data-testid="stToast"] {
  border-radius: 12px;
  border: 1px solid var(--fs-line-strong);
  font-size: 13.5px;
}

[data-testid="stSpinner"] > div { border-top-color: var(--fs-accent) !important; }
[data-testid="stSpinner"] p { font-size: 13px; color: var(--fs-muted); }

/* --- data bars ------------------------------------------------------------ */

.fs-bars { display: flex; flex-direction: column; }
.fs-bar-row {
  display: grid;
  grid-template-columns: 88px minmax(60px, 1fr) 82px;
  align-items: center;
  gap: 12px;
  padding: 7px 0;
}
.fs-bar-row + .fs-bar-row { border-top: 1px solid var(--fs-line); }
.fs-bar-name {
  font-size: 12.5px;
  font-weight: 600;
  color: var(--fs-ink);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.fs-bar-track {
  position: relative;
  height: 8px;
  border-radius: 999px;
  background: var(--fs-sunk);
}
.fs-bar-fill {
  position: absolute;
  left: 0; top: 0;
  height: 8px;
  border-radius: 999px;
  background: var(--fs-accent);
  min-width: 3px;
}
.fs-bar-fill--low { background: var(--fs-amber); }
.fs-bar-marker {
  position: absolute;
  top: -4px;
  width: 2px;
  height: 16px;
  border-radius: 1px;
  background: var(--fs-ink);
  opacity: 0.5;
}
.fs-bar-value {
  font-size: 12.5px;
  font-weight: 600;
  font-variant-numeric: tabular-nums;
  color: var(--fs-ink);
  text-align: right;
}

/* --- reason chips --------------------------------------------------------- */

.fs-reasons { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 8px; }
.fs-reason {
  font-size: 12px;
  line-height: 1.45;
  color: var(--fs-ink-soft);
  background: var(--fs-sunk);
  border: 1px solid var(--fs-line);
  border-radius: 8px;
  padding: 4px 9px;
  font-variant-numeric: tabular-nums;
}

/* --- flow diagram --------------------------------------------------------- */

.fs-flow { display: flex; flex-wrap: wrap; gap: 8px; align-items: stretch; }
.fs-flow-step {
  flex: 1 1 132px;
  background: var(--fs-surface);
  border: 1px solid var(--fs-line);
  border-radius: 12px;
  padding: 11px 12px;
}
.fs-flow-step b { display: block; font-size: 12.5px; color: var(--fs-ink); font-weight: 650; }
.fs-flow-step span { display: block; font-size: 11.5px; color: var(--fs-muted); margin-top: 2px; line-height: 1.45; }
.fs-flow-index {
  font-family: 'IBM Plex Mono', monospace;
  font-size: 10.5px;
  color: var(--fs-accent);
  letter-spacing: 0.08em;
}

/* --- responsive ----------------------------------------------------------- */

@media (max-width: 900px) {
  [data-testid="stMainBlockContainer"], .block-container { padding: 1.4rem 1rem 3rem; }
  .fs-stat-value { font-size: 25px; }
  .fs-page-title { font-size: 29px; }
  .fs-hero-title { font-size: 40px; }
  .fs-auth-brand { min-height: auto; padding: 28px; }
}

@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after { animation: none !important; transition: none !important; }
}
"""


def apply() -> None:
    """Inject the stylesheet once per script run."""
    st.markdown(f"<style>{CSS}{WIDGET_CSS}</style>", unsafe_allow_html=True)
