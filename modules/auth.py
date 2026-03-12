"""
auth.py
-------
Módulo de autenticación para CyberShield AI.
Gestiona las pantallas de login y registro de usuarios con Streamlit.

Author: Luci Jabba
Copyright (c) 2026 Luci Jabba
"""

import streamlit as st
from modules.database import create_user, login_user


# ─────────────────────────────────────────────
# ESTADO DE SESIÓN
# ─────────────────────────────────────────────

def init_session_state() -> None:
    """
    Inicializa las variables de estado de sesión necesarias para la app.
    Solo establece valores si no existen previamente (idempotente).
    """
    defaults = {
        "logged_in": False,
        "username": "",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def logout() -> None:
    """
    Cierra la sesión del usuario actual y reinicia los valores de sesión.
    """
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.rerun()


# ─────────────────────────────────────────────
# PANTALLA DE AUTENTICACIÓN
# ─────────────────────────────────────────────

def render_auth_screen(conn) -> None:
    """
    Renderiza la pantalla de autenticación con pestañas de Login y Registro.

    Muestra dos tabs:
        - Login: formulario para usuarios existentes.
        - Sign Up: formulario de registro de nuevos usuarios.

    Si el login/registro es exitoso, actualiza st.session_state y
    llama st.rerun() para redirigir al usuario a la app principal.

    Args:
        conn (sqlite3.Connection): Conexión activa a la base de datos.
    """
    st.title("🛡 CyberShield AI")
    st.subheader("Inicia sesión para continuar")

    tab_login, tab_signup = st.tabs(["Iniciar sesión", "Crear cuenta"])

    # ── LOGIN ────────────────────────────────
    with tab_login:
        username = st.text_input("Usuario", key="login_user")
        password = st.text_input("Contraseña", type="password", key="login_pass")

        if st.button("Entrar"):
            # BUG FIX: El original no validaba campos vacíos antes de consultar la BD.
            if not username or not password:
                st.warning("Por favor completa todos los campos.")
                return

            if login_user(conn, username, password):
                st.session_state.logged_in = True
                st.session_state.username = username
                st.success("Sesión iniciada correctamente.")
                st.rerun()
            else:
                st.error("Usuario o contraseña incorrectos.")

    # ── REGISTRO ─────────────────────────────
    with tab_signup:
        new_user = st.text_input("Nuevo usuario", key="signup_user")
        new_pass = st.text_input("Nueva contraseña", type="password", key="signup_pass")
        confirm_pass = st.text_input("Confirmar contraseña", type="password", key="signup_confirm")

        if st.button("Crear cuenta"):
            # BUG FIX: El original no verificaba que las contraseñas coincidieran
            # ni que los campos estuvieran completos antes de insertar en la BD.
            if not new_user or not new_pass:
                st.warning("Por favor completa todos los campos.")
                return

            if new_pass != confirm_pass:
                st.error("Las contraseñas no coinciden.")
                return

            if len(new_pass) < 6:
                st.warning("La contraseña debe tener al menos 6 caracteres.")
                return

            success = create_user(conn, new_user, new_pass)
            if success:
                st.success("Cuenta creada exitosamente. Ahora puedes iniciar sesión.")
            else:
                st.error("El nombre de usuario ya existe. Elige otro.")
