"""
app.py
------
Main entry point for CyberShield AI.
Dark purple/black gradient professional theme.

Author: Luci Jabba
Copyright (c) 2026 Luci Jabba
"""

import streamlit as st

from modules.database import get_connection, init_db, is_admin
from modules.auth import init_session_state, render_auth_screen, logout
from modules.ai_models import load_toxicity_model
from modules.views import (
    render_home,
    render_cyberbullying_detector,
    render_batch_analyzer,
    render_user_safety_score,
    render_fake_account_detector,
    render_emotion_analysis,
    render_statistics,
    render_ai_dashboard,
    render_anti_bullying_response,
    render_toxicity_map,
    render_report_incident,
    render_education,
    render_admin_panel,
    render_full_profile_analysis,
    render_analysis_history,
    render_privacy_policy,
)
import base64
with open("logo.png", "rb") as f:
    b64 = base64.b64encode(f.read()).decode()

pwa = (
    "<link rel=\"apple-touch-icon\" sizes=\"180x180\" "
    "href=\"data:image/png;base64," + b64 + "\">" + "\n"
    "<link rel=\"icon\" type=\"image/png\" "
    "href=\"data:image/png;base64," + b64 + "\">" + "\n"
    "<meta name=\"apple-mobile-web-app-capable\" content=\"yes\">\n"
    "<meta name=\"apple-mobile-web-app-title\" content=\"CyberShield AI\">\n"
)

with open("pwa_snippet.txt", "w") as f:
    f.write(pwa)
print("Listo! pwa_snippet.txt creado.")


# ─────────────────────────────────────────────
# PAGE CONFIGURATION
# ─────────────────────────────────────────────

st.set_page_config(
    page_title="CyberShield AI",
    page_icon="🛡️",
    layout="wide",
)

# ─────────────────────────────────────────────
# GLOBAL CSS — Dark Purple/Black Gradient Theme
# ─────────────────────────────────────────────

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:wght@300;400;500;600&display=swap');

/* ── ROOT VARIABLES ── */
:root {
    --bg-base:        #0a0510;
    --bg-mid:         #110a1f;
    --bg-card:        #1a1030;
    --bg-card-hover:  #221540;
    --accent:         #7c3aed;
    --accent-bright:  #a855f7;
    --accent-glow:    rgba(124, 58, 237, 0.35);
    --accent-soft:    rgba(168, 85, 247, 0.12);
    --text-primary:   #f0e8ff;
    --text-secondary: #a594c0;
    --text-muted:     #6b5e80;
    --border:         rgba(124, 58, 237, 0.25);
    --border-bright:  rgba(168, 85, 247, 0.5);
    --success:        #10b981;
    --warning:        #f59e0b;
    --danger:         #ef4444;
}

/* ── BACKGROUND ── */
html, body, .stApp {
    background: linear-gradient(135deg, #0a0510 0%, #0f0820 30%, #1a0a35 60%, #0a0510 100%) !important;
    background-attachment: fixed !important;
    font-family: 'DM Sans', sans-serif !important;
    color: var(--text-primary) !important;
}

/* Animated background mesh */
.stApp::before {
    content: '';
    position: fixed;
    top: -50%;
    left: -50%;
    width: 200%;
    height: 200%;
    background:
        radial-gradient(ellipse at 20% 20%, rgba(124,58,237,0.12) 0%, transparent 50%),
        radial-gradient(ellipse at 80% 80%, rgba(88,28,220,0.10) 0%, transparent 50%),
        radial-gradient(ellipse at 50% 0%, rgba(168,85,247,0.08) 0%, transparent 40%);
    pointer-events: none;
    z-index: 0;
}

/* ── MAIN CONTAINER ── */
.main .block-container {
    padding: 2rem 2.5rem !important;
    max-width: 1200px !important;
}

/* ── SIDEBAR ── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #110820 0%, #0d0618 100%) !important;
    border-right: 1px solid var(--border) !important;
    box-shadow: 4px 0 30px rgba(0,0,0,0.5) !important;
}

[data-testid="stSidebar"] .block-container {
    padding: 1.5rem 1rem !important;
}

/* Sidebar header */
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {
    color: var(--accent-bright) !important;
    font-family: 'Syne', sans-serif !important;
}

/* Sidebar radio buttons */
[data-testid="stSidebar"] .stRadio > label {
    color: var(--text-secondary) !important;
    font-size: 0.85rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
}

[data-testid="stSidebar"] .stRadio div[role="radiogroup"] label {
    background: transparent !important;
    border: 1px solid transparent !important;
    border-radius: 10px !important;
    padding: 0.5rem 0.8rem !important;
    margin: 2px 0 !important;
    color: var(--text-secondary) !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.88rem !important;
    transition: all 0.2s ease !important;
    cursor: pointer !important;
}

[data-testid="stSidebar"] .stRadio div[role="radiogroup"] label:hover {
    background: var(--accent-soft) !important;
    border-color: var(--border) !important;
    color: var(--text-primary) !important;
}

[data-testid="stSidebar"] .stRadio div[role="radiogroup"] label[data-checked="true"] {
    background: linear-gradient(135deg, rgba(124,58,237,0.25), rgba(88,28,220,0.15)) !important;
    border-color: var(--border-bright) !important;
    color: var(--accent-bright) !important;
    box-shadow: 0 0 12px var(--accent-glow) !important;
}

/* ── HEADINGS ── */
h1 {
    font-family: 'Syne', sans-serif !important;
    font-weight: 800 !important;
    font-size: 2.2rem !important;
    background: linear-gradient(135deg, #f0e8ff 0%, #a855f7 50%, #7c3aed 100%) !important;
    -webkit-background-clip: text !important;
    -webkit-text-fill-color: transparent !important;
    background-clip: text !important;
    letter-spacing: -0.02em !important;
    margin-bottom: 0.3rem !important;
}

h2 {
    font-family: 'Syne', sans-serif !important;
    font-weight: 700 !important;
    color: var(--text-primary) !important;
    font-size: 1.5rem !important;
}

h3 {
    font-family: 'Syne', sans-serif !important;
    font-weight: 600 !important;
    color: var(--accent-bright) !important;
    font-size: 1.15rem !important;
}

/* ── METRIC CARDS ── */
[data-testid="stMetric"] {
    background: linear-gradient(135deg, var(--bg-card), #1e1240) !important;
    border: 1px solid var(--border) !important;
    border-radius: 16px !important;
    padding: 1.2rem 1.4rem !important;
    box-shadow: 0 4px 20px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.05) !important;
    transition: transform 0.2s ease, box-shadow 0.2s ease !important;
}

[data-testid="stMetric"]:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 30px rgba(124,58,237,0.2), inset 0 1px 0 rgba(255,255,255,0.05) !important;
    border-color: var(--border-bright) !important;
}

[data-testid="stMetricLabel"] {
    color: var(--text-secondary) !important;
    font-size: 0.8rem !important;
    font-weight: 500 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.06em !important;
}

[data-testid="stMetricValue"] {
    color: var(--text-primary) !important;
    font-family: 'Syne', sans-serif !important;
    font-size: 2rem !important;
    font-weight: 800 !important;
}

/* ── BUTTONS ── */
.stButton > button {
    background: linear-gradient(135deg, #7c3aed, #5b21b6) !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 12px !important;
    padding: 0.6rem 1.8rem !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 600 !important;
    font-size: 0.9rem !important;
    letter-spacing: 0.03em !important;
    box-shadow: 0 4px 15px rgba(124,58,237,0.4) !important;
    transition: all 0.2s ease !important;
    cursor: pointer !important;
}

.stButton > button:hover {
    background: linear-gradient(135deg, #8b5cf6, #6d28d9) !important;
    box-shadow: 0 6px 25px rgba(124,58,237,0.6) !important;
    transform: translateY(-1px) !important;
}

.stButton > button:active {
    transform: translateY(0) !important;
}

/* Primary button */
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #a855f7, #7c3aed) !important;
    box-shadow: 0 4px 20px rgba(168,85,247,0.5) !important;
}

/* ── TEXT INPUTS ── */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea {
    background: rgba(26,16,48,0.8) !important;
    border: 1px solid var(--border) !important;
    border-radius: 12px !important;
    color: var(--text-primary) !important;
    font-family: 'DM Sans', sans-serif !important;
    padding: 0.7rem 1rem !important;
    transition: border-color 0.2s, box-shadow 0.2s !important;
}

.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: var(--accent-bright) !important;
    box-shadow: 0 0 0 3px var(--accent-glow) !important;
    outline: none !important;
}

.stTextInput > label,
.stTextArea > label {
    color: var(--text-secondary) !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.85rem !important;
    font-weight: 500 !important;
}

/* ── SELECTBOX / NUMBER INPUT ── */
.stSelectbox > div > div,
.stNumberInput > div > div > input {
    background: rgba(26,16,48,0.8) !important;
    border: 1px solid var(--border) !important;
    border-radius: 12px !important;
    color: var(--text-primary) !important;
}

/* ── DATAFRAME / TABLES ── */
[data-testid="stDataFrame"] {
    border: 1px solid var(--border) !important;
    border-radius: 14px !important;
    overflow: hidden !important;
    box-shadow: 0 4px 20px rgba(0,0,0,0.3) !important;
}

/* ── ALERTS ── */
.stSuccess {
    background: rgba(16,185,129,0.12) !important;
    border: 1px solid rgba(16,185,129,0.35) !important;
    border-radius: 12px !important;
    color: #6ee7b7 !important;
}

.stWarning {
    background: rgba(245,158,11,0.12) !important;
    border: 1px solid rgba(245,158,11,0.35) !important;
    border-radius: 12px !important;
    color: #fcd34d !important;
}

.stError {
    background: rgba(239,68,68,0.12) !important;
    border: 1px solid rgba(239,68,68,0.35) !important;
    border-radius: 12px !important;
    color: #fca5a5 !important;
}

.stInfo {
    background: rgba(124,58,237,0.12) !important;
    border: 1px solid var(--border) !important;
    border-radius: 12px !important;
    color: var(--text-secondary) !important;
}

/* ── TABS ── */
.stTabs [data-baseweb="tab-list"] {
    background: rgba(17,8,32,0.6) !important;
    border-radius: 14px !important;
    padding: 4px !important;
    gap: 4px !important;
    border: 1px solid var(--border) !important;
}

.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    color: var(--text-secondary) !important;
    border-radius: 10px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 500 !important;
    border: none !important;
    padding: 0.5rem 1.2rem !important;
    transition: all 0.2s !important;
}

.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, rgba(124,58,237,0.4), rgba(88,28,220,0.3)) !important;
    color: var(--text-primary) !important;
    box-shadow: 0 2px 10px var(--accent-glow) !important;
}

/* ── DIVIDER ── */
hr {
    border: none !important;
    height: 1px !important;
    background: linear-gradient(90deg, transparent, var(--border-bright), transparent) !important;
    margin: 1.5rem 0 !important;
}

/* ── SPINNER ── */
.stSpinner > div {
    border-top-color: var(--accent-bright) !important;
}

/* ── MARKDOWN TEXT ── */
.stMarkdown p {
    color: var(--text-secondary) !important;
    line-height: 1.7 !important;
}

/* ── PLOTLY CHARTS (dark background) ── */
.js-plotly-plot .plotly {
    background: transparent !important;
}

/* ── SCROLLBAR ── */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: var(--bg-base); }
::-webkit-scrollbar-thumb { background: var(--accent); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--accent-bright); }

/* ── SIDEBAR USER BADGE ── */
.user-badge {
    background: linear-gradient(135deg, rgba(124,58,237,0.2), rgba(88,28,220,0.1));
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 0.7rem 1rem;
    margin-bottom: 1rem;
    font-family: 'DM Sans', sans-serif;
    color: var(--text-secondary);
    font-size: 0.85rem;
}

.user-badge strong {
    color: var(--accent-bright);
}

/* ── LOGO / TITLE AREA ── */
.app-header {
    display: flex;
    align-items: center;
    gap: 0.8rem;
    margin-bottom: 0.5rem;
}

.shield-icon {
    font-size: 2.5rem;
    filter: drop-shadow(0 0 12px rgba(168,85,247,0.7));
}

/* ── NUMBER INPUT ── */
[data-testid="stNumberInput"] input {
    background: rgba(26,16,48,0.8) !important;
    border: 1px solid var(--border) !important;
    color: var(--text-primary) !important;
    border-radius: 12px !important;
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# INITIALIZATION
# ─────────────────────────────────────────────

conn = get_connection()
init_db(conn)
init_session_state()

# ─────────────────────────────────────────────
# AUTHENTICATION
# ─────────────────────────────────────────────

if not st.session_state.logged_in:
    render_auth_screen(conn)
    st.stop()

# ─────────────────────────────────────────────
# MAIN APP HEADER
# ─────────────────────────────────────────────

st.markdown("""
<div class="app-header">
    <span class="shield-icon">🛡</span>
    <div>
        <h1 style="margin:0; padding:0;">CyberShield AI</h1>
        <p style="margin:0; color:#a594c0; font-size:0.9rem; font-family:'DM Sans',sans-serif;">
            AI-Powered Cyberbullying Detection Platform
        </p>
    </div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────

st.sidebar.markdown(f"""
<div class="user-badge">
    👤 Signed in as <strong>{st.session_state.username}</strong>
</div>
""", unsafe_allow_html=True)

if st.sidebar.button("🚪 Log out", use_container_width=True):
    logout()

st.sidebar.markdown("---")

model = load_toxicity_model()

MENU_OPTIONS = [
    "🏠 Home",
    "🔎 Full Profile Analysis",
    "🤖 Cyberbullying Detector",
    "💬 Batch Analyzer",
    "🛡 Safety Score",
    "🕵 Fake Account Detector",
    "🧠 Emotion Analysis",
    "📊 Statistics",
    "📊 AI Dashboard",
    "🤖 Anti-Bullying Response",
    "🌍 Toxicity Map",
    "🚨 Report Incident",
    "🕒 My History",
    "📚 Education",
    "🔒 Privacy Policy",
]

if is_admin(conn, st.session_state.username):
    MENU_OPTIONS.append("⚙ Admin Panel")

menu = st.sidebar.radio("Navigation", MENU_OPTIONS)

# ─────────────────────────────────────────────
# ROUTING
# ─────────────────────────────────────────────

ROUTES = {
    "🏠 Home":                      lambda: render_home(conn, st.session_state.username),
    "🔎 Full Profile Analysis":     lambda: render_full_profile_analysis(model, conn, st.session_state.username),
    "🤖 Cyberbullying Detector":    lambda: render_cyberbullying_detector(model, conn, st.session_state.username),
    "💬 Batch Analyzer":            lambda: render_batch_analyzer(model, conn, st.session_state.username),
    "🛡 Safety Score":              lambda: render_user_safety_score(model, conn, st.session_state.username),
    "🕵 Fake Account Detector":     lambda: render_fake_account_detector(conn, st.session_state.username),
    "🧠 Emotion Analysis":          lambda: render_emotion_analysis(model),
    "📊 Statistics":                lambda: render_statistics(conn),
    "📊 AI Dashboard":              lambda: render_ai_dashboard(conn),
    "🤖 Anti-Bullying Response":    lambda: render_anti_bullying_response(),
    "🌍 Toxicity Map":              lambda: render_toxicity_map(),
    "🚨 Report Incident":           lambda: render_report_incident(conn, st.session_state.username),
    "🕒 My History":                lambda: render_analysis_history(conn, st.session_state.username),
    "📚 Education":                 lambda: render_education(),
    "🔒 Privacy Policy":            lambda: render_privacy_policy(),
    "⚙ Admin Panel":               lambda: render_admin_panel(conn, st.session_state.username),
}

view_fn = ROUTES.get(menu)
if view_fn:
    view_fn()
else:
    st.error(f"View '{menu}' not found.")
