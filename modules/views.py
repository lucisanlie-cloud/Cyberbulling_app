"""
views.py
--------
Módulo de vistas para CyberShield AI.
Versión actualizada con métricas reales, historial, perfil completo e inicio mejorado.

Author: Luci Jabba
Copyright (c) 2026 Luci Jabba
"""

import random
import datetime

import pandas as pd
import plotly.express as px
import streamlit as st

from .ai_models import analyze_toxicity, analyze_batch
from .database import (
    save_report, get_all_reports, get_all_users, is_admin,
    save_analysis, get_user_history, get_all_history,
    count_users, count_reports, count_analyses, count_toxic_analyses,
    get_reports_by_day,
)
from .export_pdf import generate_reports_pdf
from .email_alerts import send_alert_email, is_email_configured

# Respuestas predefinidas anti-bullying
ANTI_BULLYING_RESPONSES = [
    "Por favor comunícate con respeto.",
    "Todos merecemos amabilidad en línea.",
    "Mantengamos conversaciones positivas.",
    "Las palabras pueden herir. Seamos respetuosos.",
    "El respeto es fundamental en cualquier comunidad digital.",
]

# Coordenadas para el mapa de toxicidad
TOXICITY_MAP_LOCATIONS = pd.DataFrame({
    "lat": [40.7128, 51.5074, 40.4168, 35.6762, 4.7110, -33.8688],
    "lon": [-74.0060, -0.1278, -3.7038, 139.6503, -74.0721, 151.2093],
    "ciudad": ["New York", "London", "Madrid", "Tokyo", "Bogotá", "Sydney"],
})


# ─────────────────────────────────────────────
# INICIO (MEJORADO CON MÉTRICAS REALES)
# ─────────────────────────────────────────────

def render_home(conn, username: str) -> None:
    """
    Página de inicio con métricas reales de la BD y bienvenida personalizada.
    """
    st.markdown(f"### 👋 Bienvenida, **{username}**")
    st.write("CyberShield AI detecta ciberacoso usando inteligencia artificial.")
    st.markdown("---")

    # ── Métricas reales ──────────────────────
    st.markdown("#### 📊 Estadísticas de la plataforma")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("👥 Usuarios registrados",  count_users(conn))
    col2.metric("🚨 Incidentes reportados", count_reports(conn))
    col3.metric("🔍 Análisis realizados",   count_analyses(conn))
    col4.metric("☠️ Alertas de peligro",    count_toxic_analyses(conn))

    st.markdown("---")

    # ── Gráfico de reportes recientes ────────
    st.markdown("#### 📈 Reportes de los últimos 30 días")
    df_days = get_reports_by_day(conn)
    if df_days.empty:
        st.info("Aún no hay reportes registrados.")
    else:
        fig = px.bar(
            df_days, x="fecha", y="total",
            color_discrete_sequence=["#6B21A8"],
            labels={"fecha": "Fecha", "total": "Reportes"},
        )
        fig.update_layout(showlegend=False, margin=dict(t=20, b=20))
        st.plotly_chart(fig, use_container_width=True)

    # ── Historial reciente del usuario ───────
    st.markdown("#### 🕒 Tus últimos análisis")
    history = get_user_history(conn, username)
    if history.empty:
        st.info("Aún no has realizado ningún análisis.")
    else:
        st.dataframe(history.head(5), use_container_width=True)


# ─────────────────────────────────────────────
# DETECTOR DE CIBERACOSO
# ─────────────────────────────────────────────

def render_cyberbullying_detector(model, conn, username: str) -> None:
    st.subheader("🤖 Detector de Ciberacoso")
    text = st.text_area("Ingresa el mensaje a analizar", height=150)

    if st.button("Analizar", key="analyze_single"):
        if not text.strip():
            st.warning("Por favor ingresa un mensaje.")
            return

        result = analyze_toxicity(model, text)
        score  = result["score"]

        st.metric("Puntuación de toxicidad", f"{score}/100")

        if result["level"] == "safe":
            st.success("✅ Mensaje seguro")
        elif result["level"] == "warning":
            st.warning("⚠️ Posible toxicidad — revisa el contenido")
        else:
            st.error("🚨 Riesgo de ciberacoso detectado")

        # Guardar en historial
        save_analysis(conn, username, "texto", text[:100], score, result["level"])


# ─────────────────────────────────────────────
# ANALIZADOR POR LOTES
# ─────────────────────────────────────────────

def render_batch_analyzer(model, conn, username: str) -> None:
    st.subheader("💬 Analizador de Comentarios por Lote")
    st.info("Ingresa un comentario por línea.")
    raw_text = st.text_area("Comentarios", height=200)

    if st.button("Analizar lote", key="analyze_batch"):
        lines = [l.strip() for l in raw_text.splitlines() if l.strip()]
        if not lines:
            st.warning("Por favor ingresa al menos un comentario.")
            return

        with st.spinner(f"Analizando {len(lines)} comentarios…"):
            results = analyze_batch(model, lines)

        df = pd.DataFrame({
            "Comentario":  lines,
            "Puntuación":  [r["score"] for r in results],
            "Nivel":       [r["level"] for r in results],
        })
        st.dataframe(df, use_container_width=True)

        # Guardar resumen en historial
        avg = sum(r["score"] for r in results) // len(results)
        level = "danger" if avg >= 60 else "warning" if avg >= 30 else "safe"
        save_analysis(conn, username, "lote", f"{len(lines)} comentarios", avg, level)


# ─────────────────────────────────────────────
# PUNTAJE DE SEGURIDAD
# ─────────────────────────────────────────────

def render_user_safety_score(model, conn, username: str) -> None:
    st.subheader("🛡 Puntaje de Seguridad de Usuario")
    st.info("Analiza los comentarios reales que recibe un perfil público de Instagram.")

    col1, col2 = st.columns([3, 1])
    with col1:
        ig_username = st.text_input("Usuario de Instagram a evaluar (sin @)")
    with col2:
        max_posts = st.number_input("Posts a revisar", min_value=1, max_value=10, value=3)

    if st.button("Calcular puntaje"):
        if not ig_username:
            st.warning("Ingresa un nombre de usuario.")
            return

        from .instagram import get_recent_comments
        with st.spinner(f"Obteniendo comentarios de @{ig_username}…"):
            comments = get_recent_comments(ig_username, max_posts=max_posts)

        if not comments:
            st.warning("No se encontraron comentarios.")
            return

        with st.spinner("Analizando toxicidad con IA…"):
            results = analyze_batch(model, comments)

        avg_score = sum(r["score"] for r in results) // len(results)
        safety    = 100 - avg_score
        level     = "danger" if avg_score >= 60 else "warning" if avg_score >= 30 else "safe"

        st.metric(f"Puntaje de seguridad de @{ig_username}", f"{safety}/100")

        if safety >= 70:
            st.success("✅ El perfil recibe comentarios mayormente seguros.")
        elif safety >= 40:
            st.warning("⚠️ El perfil recibe comentarios con toxicidad moderada.")
        else:
            st.error("🚨 El perfil está recibiendo comentarios altamente tóxicos.")

        df = pd.DataFrame({
            "Comentario":      comments,
            "Puntuación tóxica": [r["score"] for r in results],
            "Nivel":           [r["level"] for r in results],
        })
        st.dataframe(df, use_container_width=True)
        save_analysis(conn, username, "instagram", f"@{ig_username}", avg_score, level)


# ─────────────────────────────────────────────
# DETECTOR DE CUENTAS FALSAS
# ─────────────────────────────────────────────

def render_fake_account_detector(conn, username: str) -> None:
    st.subheader("🕵 Detector de Cuentas Falsas")
    st.info("Ingresa un usuario público de Instagram para analizarlo automáticamente.")
    ig_username = st.text_input("Username de Instagram (sin @)")

    if st.button("Analizar cuenta"):
        if not ig_username:
            st.warning("Ingresa un nombre de usuario.")
            return

        from .instagram import get_profile_info, analyze_fake_account
        with st.spinner(f"Consultando perfil @{ig_username}…"):
            profile = get_profile_info(ig_username)

        if profile is None:
            st.error("No se encontró el perfil.")
            return

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Seguidores",    f"{profile['followers']:,}")
        col2.metric("Seguidos",      f"{profile['following']:,}")
        col3.metric("Publicaciones", f"{profile['posts']:,}")
        col4.metric("Ratio",         profile["ratio"])

        if profile["is_verified"]:
            st.success("✅ Cuenta verificada")
        if profile["is_private"]:
            st.warning("🔒 Cuenta privada")
        if profile["biography"]:
            st.caption(f"**Bio:** {profile['biography']}")

        result = analyze_fake_account(profile)
        st.metric("Probabilidad de cuenta falsa", f"{result['risk_score']}%")
        for indicator in result["indicators"]:
            st.write(indicator)

        if result["level"] == "low":
            st.success("✅ Cuenta con indicadores normales.")
        elif result["level"] == "medium":
            st.warning("⚠️ Cuenta con indicadores sospechosos.")
        else:
            st.error("🚨 Alta probabilidad de cuenta falsa.")

        save_analysis(conn, username, "cuenta_falsa", f"@{ig_username}",
                      result["risk_score"],
                      "danger" if result["level"] == "high" else result["level"])


# ─────────────────────────────────────────────
# ANÁLISIS DE PERFIL COMPLETO (NUEVO)
# ─────────────────────────────────────────────

def render_full_profile_analysis(model, conn, username: str) -> None:
    """
    Vista nueva que combina en un solo lugar:
    datos de Instagram + toxicidad de comentarios + detector de cuenta falsa.
    """
    st.subheader("🔎 Análisis de Perfil Completo")
    st.info("Análisis integral: datos del perfil + toxicidad + autenticidad.")
    ig_username = st.text_input("Usuario de Instagram (sin @)", key="full_profile")

    if st.button("Analizar perfil completo", type="primary"):
        if not ig_username:
            st.warning("Ingresa un nombre de usuario.")
            return

        from .instagram import get_profile_info, get_recent_comments, analyze_fake_account

        # ── 1. Datos del perfil ──────────────
        with st.spinner("Consultando perfil…"):
            profile = get_profile_info(ig_username)

        if not profile:
            st.error("No se encontró el perfil.")
            return

        st.markdown("### 👤 Información del perfil")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Seguidores",    f"{profile['followers']:,}")
        col2.metric("Seguidos",      f"{profile['following']:,}")
        col3.metric("Publicaciones", f"{profile['posts']:,}")
        col4.metric("Ratio",         profile["ratio"])

        if profile["full_name"]:
            st.caption(f"**Nombre:** {profile['full_name']}")
        if profile["biography"]:
            st.caption(f"**Bio:** {profile['biography']}")
        if profile["is_verified"]:
            st.success("✅ Cuenta verificada")
        if profile["is_private"]:
            st.warning("🔒 Cuenta privada — análisis de comentarios limitado")

        st.markdown("---")

        # ── 2. Autenticidad ──────────────────
        st.markdown("### 🕵 Evaluación de autenticidad")
        fake = analyze_fake_account(profile)
        st.metric("Probabilidad de cuenta falsa", f"{fake['risk_score']}%")
        for ind in fake["indicators"]:
            st.write(ind)

        st.markdown("---")

        # ── 3. Toxicidad de comentarios ──────
        st.markdown("### ☠️ Análisis de toxicidad en comentarios")
        if profile["is_private"]:
            st.warning("Cuenta privada — no se pueden obtener comentarios.")
        else:
            with st.spinner("Obteniendo comentarios…"):
                comments = get_recent_comments(ig_username, max_posts=2)

            if comments:
                with st.spinner("Analizando toxicidad…"):
                    results = analyze_batch(model, comments)

                avg_score = sum(r["score"] for r in results) // len(results)
                safety    = 100 - avg_score

                col1, col2 = st.columns(2)
                col1.metric("Puntaje de seguridad", f"{safety}/100")
                col2.metric("Toxicidad promedio",   f"{avg_score}/100")

                df = pd.DataFrame({
                    "Comentario":  comments,
                    "Toxicidad":   [r["score"] for r in results],
                    "Nivel":       [r["level"] for r in results],
                })
                st.dataframe(df, use_container_width=True)

                # Gráfico
                fig = px.histogram(
                    df, x="Nivel", color="Nivel",
                    color_discrete_map={"safe": "#16A34A", "warning": "#D97706", "danger": "#DC2626"},
                    title="Distribución de niveles de toxicidad",
                )
                st.plotly_chart(fig, use_container_width=True)

                level = "danger" if avg_score >= 60 else "warning" if avg_score >= 30 else "safe"
                save_analysis(conn, username, "perfil_completo", f"@{ig_username}", avg_score, level)
            else:
                st.info("No se encontraron comentarios públicos.")


# ─────────────────────────────────────────────
# HISTORIAL DE ANÁLISIS (NUEVO)
# ─────────────────────────────────────────────

def render_analysis_history(conn, username: str) -> None:
    """Vista del historial personal de análisis del usuario."""
    st.subheader("🕒 Mi Historial de Análisis")

    history = get_user_history(conn, username)

    if history.empty:
        st.info("Aún no has realizado ningún análisis.")
        return

    # Métricas rápidas
    col1, col2, col3 = st.columns(3)
    col1.metric("Total análisis", len(history))
    col2.metric("Peligrosos",     len(history[history["level"] == "danger"]))
    col3.metric("Seguros",        len(history[history["level"] == "safe"]))

    # Filtro por tipo
    tipos = ["Todos"] + history["type"].unique().tolist()
    filtro = st.selectbox("Filtrar por tipo", tipos)
    if filtro != "Todos":
        history = history[history["type"] == filtro]

    # Colorear nivel
    def color_level(val):
        colors = {"safe": "background-color: #DCFCE7", "warning": "background-color: #FEF9C3", "danger": "background-color: #FEE2E2"}
        return colors.get(val, "")

    st.dataframe(
        history.style.applymap(color_level, subset=["level"]),
        use_container_width=True
    )


# ─────────────────────────────────────────────
# ANÁLISIS DE EMOCIONES
# ─────────────────────────────────────────────

def render_emotion_analysis(model) -> None:
    st.subheader("🧠 Análisis de Emociones")
    text = st.text_area("Texto a analizar emocionalmente", height=120)

    if st.button("Analizar emociones"):
        if not text.strip():
            st.warning("Ingresa un texto.")
            return

        result = analyze_toxicity(model, text)
        score  = result["score"]

        emotions_data = pd.DataFrame({
            "Emoción":    ["Ira", "Tristeza", "Miedo", "Neutral"],
            "Intensidad": [max(0, score - 10), max(0, score // 2), max(0, score // 3), max(0, 100 - score)],
        })
        fig = px.bar(emotions_data, x="Emoción", y="Intensidad",
                     color="Emoción", title="Distribución Emocional")
        st.plotly_chart(fig, use_container_width=True)


# ─────────────────────────────────────────────
# ESTADÍSTICAS (CON DATOS REALES)
# ─────────────────────────────────────────────

def render_statistics(conn) -> None:
    st.subheader("📊 Estadísticas Generales")

    reports_df = get_all_reports(conn)
    history_df = get_all_history(conn)

    if reports_df.empty and history_df.empty:
        st.info("Aún no hay suficientes datos para mostrar estadísticas.")
        return

    col1, col2 = st.columns(2)

    with col1:
        if not reports_df.empty:
            # Reportes por agresor
            top_agresores = reports_df["aggressor"].value_counts().head(5).reset_index()
            top_agresores.columns = ["Agresor", "Reportes"]
            fig = px.bar(top_agresores, x="Agresor", y="Reportes",
                         title="Top agresores reportados",
                         color_discrete_sequence=["#6B21A8"])
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        if not history_df.empty:
            # Distribución de niveles
            nivel_counts = history_df["level"].value_counts().reset_index()
            nivel_counts.columns = ["Nivel", "Total"]
            fig = px.pie(nivel_counts, names="Nivel", values="Total",
                         title="Distribución de niveles de toxicidad",
                         color="Nivel",
                         color_discrete_map={"safe": "#16A34A", "warning": "#D97706", "danger": "#DC2626"})
            st.plotly_chart(fig, use_container_width=True)

    # Evolución de reportes
    df_days = get_reports_by_day(conn)
    if not df_days.empty:
        fig = px.line(df_days, x="fecha", y="total",
                      title="Evolución de reportes (últimos 30 días)",
                      color_discrete_sequence=["#6B21A8"])
        st.plotly_chart(fig, use_container_width=True)


# ─────────────────────────────────────────────
# DASHBOARD DE IA
# ─────────────────────────────────────────────

def render_ai_dashboard(conn) -> None:
    st.subheader("📊 Dashboard de Inteligencia Artificial")

    history_df = get_all_history(conn)
    if history_df.empty:
        st.info("Aún no hay análisis para mostrar en el dashboard.")
        return

    col1, col2 = st.columns(2)
    with col1:
        # Análisis por tipo
        type_counts = history_df["type"].value_counts().reset_index()
        type_counts.columns = ["Tipo", "Total"]
        fig = px.bar(type_counts, x="Tipo", y="Total",
                     color="Total", color_continuous_scale="Purples",
                     title="Análisis realizados por tipo")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Score promedio por tipo
        avg_by_type = history_df.groupby("type")["score"].mean().reset_index()
        avg_by_type.columns = ["Tipo", "Score promedio"]
        fig = px.bar(avg_by_type, x="Tipo", y="Score promedio",
                     color="Score promedio", color_continuous_scale="Reds",
                     title="Toxicidad promedio por tipo de análisis")
        st.plotly_chart(fig, use_container_width=True)


# ─────────────────────────────────────────────
# RESPUESTAS ANTI-BULLYING
# ─────────────────────────────────────────────

def render_anti_bullying_response() -> None:
    st.subheader("🤖 Generador de Respuestas Anti-Bullying")
    toxic_msg = st.text_area("Mensaje tóxico recibido", height=120)

    if st.button("Generar respuesta"):
        if not toxic_msg.strip():
            st.warning("Ingresa el mensaje tóxico.")
            return
        response = random.choice(ANTI_BULLYING_RESPONSES)
        st.success(f"**Respuesta sugerida:** {response}")


# ─────────────────────────────────────────────
# MAPA DE TOXICIDAD
# ─────────────────────────────────────────────

def render_toxicity_map() -> None:
    st.subheader("🌍 Mapa de Toxicidad Global")
    st.info("Ubicaciones con mayor incidencia de reportes (datos de demostración).")
    st.map(TOXICITY_MAP_LOCATIONS[["lat", "lon"]])
    st.dataframe(TOXICITY_MAP_LOCATIONS, use_container_width=True)


# ─────────────────────────────────────────────
# REPORTE DE INCIDENTES
# ─────────────────────────────────────────────

def render_report_incident(conn, username: str) -> None:
    st.subheader("🚨 Reportar Incidente")

    aggressor = st.text_input("Usuario agresor")
    message   = st.text_area("Descripción del incidente", height=150)

    if st.button("Enviar reporte"):
        if not aggressor or not message.strip():
            st.warning("Por favor completa todos los campos.")
            return

        save_report(conn, reporter=username, aggressor=aggressor, message=message)
        st.success("✅ Reporte enviado correctamente.")

        # Analizar toxicidad del mensaje y enviar email si es grave
        # (importamos aquí para evitar carga innecesaria)
        try:
            from .ai_models import load_toxicity_model
            model = load_toxicity_model()
            result = analyze_toxicity(model, message)
            if result["level"] == "danger":
                sent = send_alert_email(username, aggressor, message, result["score"])
                if sent:
                    st.info("📧 Se envió una alerta por email al administrador.")
        except Exception:
            pass  # No interrumpir si el email falla


# ─────────────────────────────────────────────
# EDUCACIÓN
# ─────────────────────────────────────────────

def render_education() -> None:
    st.subheader("📚 Educación sobre Ciberacoso")
    st.markdown("""
    ### ¿Qué es el ciberacoso?
    El ciberacoso es el uso de tecnologías digitales para acosar, amenazar,
    humillar o atacar a otras personas.

    ### Tipos de ciberacoso
    - **Acoso directo**: mensajes ofensivos enviados directamente a la víctima.
    - **Exclusión**: excluir deliberadamente a alguien de grupos o actividades online.
    - **Doxing**: publicar información privada de alguien sin su consentimiento.
    - **Suplantación**: hacerse pasar por otra persona para dañar su reputación.

    ### ¿Qué hacer si eres víctima?
    1. No respondas a los mensajes agresivos.
    2. Guarda evidencia (capturas de pantalla).
    3. Bloquea al agresor.
    4. Reporta en la plataforma correspondiente.
    5. Busca apoyo de un adulto de confianza o autoridad.
    """)


# ─────────────────────────────────────────────
# PANEL DE ADMINISTRACIÓN
# ─────────────────────────────────────────────

def render_admin_panel(conn, username: str) -> None:
    if not is_admin(conn, username):
        st.error("🚫 Acceso denegado.")
        return

    st.subheader("⚙ Panel de Administración")
    st.success(f"✅ Sesión de administrador activa: **{username}**")

    tab1, tab2, tab3 = st.tabs(["👥 Usuarios", "🚨 Reportes", "🔍 Historial de análisis"])

    with tab1:
        users_df = get_all_users(conn)
        st.dataframe(users_df, use_container_width=True)

    with tab2:
        reports_df = get_all_reports(conn)
        if reports_df.empty:
            st.info("No hay reportes registrados aún.")
        else:
            st.dataframe(reports_df, use_container_width=True)
            if st.button("📥 Descargar reporte en PDF", type="primary"):
                with st.spinner("Generando PDF…"):
                    try:
                        pdf_bytes = generate_reports_pdf(reports_df, total_users=len(users_df))
                        st.download_button(
                            label="⬇️ Haz click aquí para descargar",
                            data=pdf_bytes,
                            file_name=f"cybershield_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                            mime="application/pdf",
                        )
                        st.success("✅ PDF generado.")
                    except Exception as e:
                        st.error(f"❌ Error: {e}")

    with tab3:
        history_df = get_all_history(conn)
        if history_df.empty:
            st.info("No hay análisis registrados aún.")
        else:
            st.dataframe(history_df, use_container_width=True)

    # Estado del email
    st.markdown("---")
    st.markdown("#### 📧 Estado de alertas por email")
    if is_email_configured():
        st.success("✅ Notificaciones por email configuradas.")
    else:
        st.warning("⚠️ Email no configurado. Añade EMAIL_SENDER, EMAIL_PASSWORD y EMAIL_RECEIVER como variables de entorno.")


def render_privacy_policy():
    st.title("🔒 Política de Privacidad")
    st.markdown("**Última actualización: 09/03/2026**")
    st.divider()
    st.markdown("""
## Cyberbullying App

Cyberbullying App es una herramienta diseñada para ayudar a identificar y analizar comentarios 
potencialmente dañinos o abusivos en plataformas de redes sociales. El objetivo es promover 
entornos en línea más seguros detectando posibles patrones de ciberacoso.

---

### Introducción
Cyberbullying App respeta la privacidad de sus usuarios. Esta Política de Privacidad explica cómo 
recopilamos, usamos y protegemos la información cuando se utiliza nuestra aplicación.

---

### Información que Recopilamos
- Datos públicos de redes sociales que los usuarios elijan analizar.
- Información técnica básica como tipo de dispositivo o sistema operativo.
- Contenido proporcionado por el usuario para la detección de ciberacoso.

**No recopilamos información personal sensible sin el consentimiento del usuario.**

---

### Cómo Usamos la Información
- Analizar textos y comentarios para detectar ciberacoso.
- Mejorar la funcionalidad y seguridad de la aplicación.
- Mejorar la experiencia del usuario.

---

### Compartir Información
**No vendemos, intercambiamos ni compartimos la información personal de los usuarios con terceros.**

---

### Seguridad de los Datos
Tomamos medidas razonables para proteger la información del usuario contra acceso o divulgación no autorizados.

---

### Servicios de Terceros
Nuestra aplicación puede interactuar con servicios de terceros como plataformas de redes sociales. 
Sus propias políticas de privacidad pueden aplicarse.

---

### Cambios en esta Política
Podemos actualizar esta Política de Privacidad ocasionalmente. Las actualizaciones se publicarán en esta página.

---

### Eliminación de Datos de Usuario
Si deseas solicitar la eliminación de tus datos, sigue estos pasos:
1. Envía un correo a: **lujabbali@gmail.com**
2. Asunto: **"Data Deletion Request"**
3. Incluye tu nombre de usuario o identificador de cuenta.

Eliminaremos tus datos en un plazo razonable tras recibir tu solicitud.

---

### Contacto
📧 **lujabbali@gmail.com**
    """)
