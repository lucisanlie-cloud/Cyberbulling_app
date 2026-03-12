"""
app.py
------
Punto de entrada principal de CyberShield AI.
Orquesta la autenticación, el menú lateral y el enrutamiento de vistas.

Ejecución:
    streamlit run app.py

Author: Luci Jabba
Copyright (c) 2026 Luci Jabba
"""

import streamlit as st

from .database import get_connection, init_db
from .auth import init_session_state, render_auth_screen, logout
from .ai_models import load_toxicity_model
from .views import (
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
# FLUJO DE AUTENTICACIÓN
# ─────────────────────────────────────────────

if not st.session_state.logged_in:
    render_auth_screen(conn)
    st.stop()

# ─────────────────────────────────────────────
# APLICACIÓN PRINCIPAL (usuario autenticado)
# ─────────────────────────────────────────────

st.title("🛡 CyberShield AI")
st.subheader("Plataforma de IA Contra el Ciberacoso")

# Sidebar
st.sidebar.markdown(f"👤 Sesión: **{st.session_state.username}**")
if st.sidebar.button("Cerrar sesión"):
    logout()

# Carga del modelo (singleton cacheado)
model = load_toxicity_model()

# Menú de navegación
MENU_OPTIONS = [
    "🏠 Inicio",
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
    "📚 Educación",
    "⚙ Panel de Administración",
]

menu = st.sidebar.radio("Menú", MENU_OPTIONS)

# ─────────────────────────────────────────────
# ENRUTAMIENTO DE VISTAS
# ─────────────────────────────────────────────

ROUTES = {
    "🏠 Inicio":                    lambda: render_home(),
    "🤖 Detector de Ciberacoso":    lambda: render_cyberbullying_detector(model),
    "💬 Analizador por Lotes":      lambda: render_batch_analyzer(model),
    "🛡 Puntaje de Seguridad":      lambda: render_user_safety_score(model),
    "🕵 Detector de Cuentas Falsas":lambda: render_fake_account_detector(),
    "🧠 Análisis de Emociones":     lambda: render_emotion_analysis(model),
    "📊 Estadísticas":              lambda: render_statistics(),
    "📊 Dashboard de IA":           lambda: render_ai_dashboard(),
    "🤖 Respuesta Anti-Bullying":   lambda: render_anti_bullying_response(),
    "🌍 Mapa de Toxicidad":         lambda: render_toxicity_map(),
    "🚨 Reportar Incidente":        lambda: render_report_incident(conn, st.session_state.username),
    "📚 Educación":                 lambda: render_education(),
    "⚙ Panel de Administración":    lambda: render_admin_panel(conn, st.session_state.username),
}

# BUG FIX: El original usaba una cadena de elif sin fallback.
# Ahora se usa un diccionario de rutas con manejo de opción inválida.
view_fn = ROUTES.get(menu)
if view_fn:
    view_fn()
else:
    st.error(f"Vista '{menu}' no encontrada.")
