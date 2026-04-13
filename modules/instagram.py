"""
instagram.py
------------
Módulo de integración con Instagram para CyberShield AI.
Usa Instaloader (gratuito, sin API key).

Author: Luci Jabba
Copyright (c) 2026 Luci Jabba
"""

import streamlit as st

try:
    import instaloader
    INSTALOADER_AVAILABLE = True
except ImportError:
    INSTALOADER_AVAILABLE = False


# ─────────────────────────────────────────────
# OBTENER DATOS DE PERFIL
# ─────────────────────────────────────────────

def get_profile_info(username: str) -> dict | None:
    if not INSTALOADER_AVAILABLE:
        st.error("❌ Instaloader no está instalado. Ejecuta: pip install instaloader")
        return None

    try:
        L = instaloader.Instaloader()
        profile = instaloader.Profile.from_username(L.context, username)

        followers = profile.followers
        following = profile.followees

        return {
            "username":    profile.username,
            "full_name":   profile.full_name,
            "followers":   followers,
            "following":   following,
            "posts":       profile.mediacount,
            "is_private":  profile.is_private,
            "biography":   profile.biography,
            "is_verified": profile.is_verified,
            "ratio": round(following / followers, 2) if followers > 0 else 999,
        }

    except instaloader.exceptions.ProfileNotExistsException:
        st.error("❌ Perfil no encontrado. Verifica el nombre de usuario.")
        return None
    except instaloader.exceptions.ConnectionException:
        st.error("⚠️ Instagram bloqueó la consulta temporalmente. Espera unos minutos e intenta de nuevo.")
        return None
    except Exception as e:
        st.error(f"❌ Error inesperado: {e}")
        return None


# ─────────────────────────────────────────────
# OBTENER POSTS RECIENTES
# ─────────────────────────────────────────────

def get_recent_comments(username: str, max_posts: int = 2, max_comments: int = 20) -> list[str]:
    if not INSTALOADER_AVAILABLE:
        return []

    try:
        L = instaloader.Instaloader()
        profile = instaloader.Profile.from_username(L.context, username)

        if profile.is_private:
            st.warning("🔒 Perfil privado. No se pueden obtener posts.")
            return []

        captions = []
        for post in profile.get_posts():
            if len(captions) >= max_posts:
                break
            if post.caption:
                captions.append(post.caption)

        return captions

    except Exception as e:
        st.warning(f"⚠️ No se pudieron cargar posts: {e}")
        return []


# ─────────────────────────────────────────────
# ANÁLISIS DE CUENTA FALSA
# ─────────────────────────────────────────────

def analyze_fake_account(profile_data: dict) -> dict:
    risk_score = 0
    indicators = []

    if profile_data["posts"] == 0:
        risk_score += 25
        indicators.append("⚠️ Sin publicaciones")

    if profile_data["ratio"] > 10:
        risk_score += 30
        indicators.append(f"⚠️ Sigue a muchos más de los que le siguen (ratio {profile_data['ratio']})")

    if not profile_data.get("biography"):
        risk_score += 15
        indicators.append("⚠️ Sin biografía")

    if not profile_data.get("full_name"):
        risk_score += 10
        indicators.append("⚠️ Sin nombre completo")

    if profile_data["followers"] > 10000 and not profile_data["is_verified"]:
        risk_score += 10
        indicators.append("ℹ️ Muchos seguidores sin verificación oficial")

    if profile_data["followers"] < 10 and profile_data["following"] > 200:
        risk_score += 20
        indicators.append("⚠️ Casi sin seguidores pero sigue a muchos")

    risk_score = min(risk_score, 100)
    level = "low" if risk_score < 30 else "medium" if risk_score < 60 else "high"

    return {
        "risk_score": risk_score,
        "level":      level,
        "indicators": indicators if indicators else ["✅ Sin señales sospechosas detectadas"],
    }
