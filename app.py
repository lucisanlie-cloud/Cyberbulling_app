"""
app.py
------
Punto de entrada principal de CyberShield AI.
Versión actualizada con nuevas vistas y menú dinámico.

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

# ─────────────────────────────────────────────
# CONFIGURACIÓN DE PÁGINA
# ─────────────────────────────────────────────

st.set_page_config(
    page_title="CyberShield AI",
    page_icon="🛡️",
    layout="wide",
)

# ─────────────────────────────────────────────
# INICIALIZACIÓN
# ─────────────────────────────────────────────

conn = get_connection()
init_db(conn)
init_session_state()

# ─────────────────────────────────────────────
# AUTENTICACIÓN
# ─────────────────────────────────────────────

if not st.session_state.logged_in:
    render_auth_screen(conn)
    st.stop()

# ─────────────────────────────────────────────
# APP PRINCIPAL
# ─────────────────────────────────────────────

st.title("🛡 CyberShield AI")
st.subheader("Plataforma de IA Contra el Ciberacoso")

# Sidebar
st.sidebar.markdown(f"👤 Sesión: **{st.session_state.username}**")
if st.sidebar.button("Cerrar sesión"):
    logout()

model = load_toxicity_model()

# Menú dinámico — el panel admin solo aparece si el usuario es admin
MENU_OPTIONS = [
    "🏠 Inicio",
    "🔎 Análisis de Perfil Completo",
    "🤖 Detector de Ciberacoso",
    "💬 Analizador por Lotes",
    "🛡 Puntaje de Seguridad",
    "🕵 Detector de Cuentas Falsas",
    "🧠 Análisis de Emociones",
    "📊 Estadísticas",
    "📊 Dashboard de IA",
    "🤖 Respuesta Anti-Bullying",
    "🌍 Mapa de Toxicidad",
    "🚨 Reportar Incidente",
    "🕒 Mi Historial",
    "📚 Educación",
    "🔒 Política de Privacidad",
]

if is_admin(conn, st.session_state.username):
    MENU_OPTIONS.append("⚙ Panel de Administración")

menu = st.sidebar.radio("Menú", MENU_OPTIONS)

# ─────────────────────────────────────────────
# ENRUTAMIENTO
# ─────────────────────────────────────────────

ROUTES = {
    "🏠 Inicio":                      lambda: render_home(conn, st.session_state.username),
    "🔎 Análisis de Perfil Completo": lambda: render_full_profile_analysis(model, conn, st.session_state.username),
    "🤖 Detector de Ciberacoso":      lambda: render_cyberbullying_detector(model, conn, st.session_state.username),
    "💬 Analizador por Lotes":        lambda: render_batch_analyzer(model, conn, st.session_state.username),
    "🛡 Puntaje de Seguridad":        lambda: render_user_safety_score(model, conn, st.session_state.username),
    "🕵 Detector de Cuentas Falsas":  lambda: render_fake_account_detector(conn, st.session_state.username),
    "🧠 Análisis de Emociones":       lambda: render_emotion_analysis(model),
    "📊 Estadísticas":                lambda: render_statistics(conn),
    "📊 Dashboard de IA":             lambda: render_ai_dashboard(conn),
    "🤖 Respuesta Anti-Bullying":     lambda: render_anti_bullying_response(),
    "🌍 Mapa de Toxicidad":           lambda: render_toxicity_map(),
    "🚨 Reportar Incidente":          lambda: render_report_incident(conn, st.session_state.username),
    "🕒 Mi Historial":                lambda: render_analysis_history(conn, st.session_state.username),
    "📚 Educación":                   lambda: render_education(),
    "🔒 Política de Privacidad":      lambda: render_privacy_policy(),
    "⚙ Panel de Administración":      lambda: render_admin_panel(conn, st.session_state.username),
}

view_fn = ROUTES.get(menu)
if view_fn:
    view_fn()
else:
    st.error(f"Vista '{menu}' no encontrada.")
