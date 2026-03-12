"""
instagram.py
------------
Módulo de integración con Instagram para CyberShield AI.
Usa Instagram Scraper 2025 via RapidAPI.

Author: Luci Jabba
Copyright (c) 2026 Luci Jabba
"""

import os
import requests
import streamlit as st

# ─────────────────────────────────────────────
# CONFIGURACIÓN RAPIDAPI
# ─────────────────────────────────────────────
# Pega tu API Key aquí directamente:

RAPIDAPI_KEY  = "649994126dmshc36d7a916e30b26p1ebab5jsn52dd30849635"
RAPIDAPI_HOST = "instagram-scraper-20251.p.rapidapi.com"

HEADERS = {
    "x-rapidapi-key":  RAPIDAPI_KEY,
    "x-rapidapi-host": RAPIDAPI_HOST,
}

BASE_URL = f"https://{RAPIDAPI_HOST}"


# ─────────────────────────────────────────────
# OBTENER DATOS DE PERFIL
# ─────────────────────────────────────────────

def get_profile_info(username: str) -> dict | None:
    """
    Obtiene información pública de un perfil de Instagram via RapidAPI.

    Args:
        username (str): Nombre de usuario de Instagram (sin @).

    Returns:
        dict con datos del perfil, o None si falla.
    """
    url = f"{BASE_URL}/userinfo/"
    params = {"username_or_id": username}

    try:
        response = requests.get(url, headers=HEADERS, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        # Extraer datos del perfil
        user = data.get("data", data)

        followers = user.get("follower_count", user.get("followers", 0))
        following = user.get("following_count", user.get("following", 0))

        return {
            "username":    user.get("username", username),
            "full_name":   user.get("full_name", ""),
            "followers":   followers,
            "following":   following,
            "posts":       user.get("media_count", user.get("posts", 0)),
            "is_private":  user.get("is_private", False),
            "biography":   user.get("biography", ""),
            "is_verified": user.get("is_verified", False),
            "ratio": round(following / followers, 2) if followers > 0 else 999,
        }

    except requests.exceptions.Timeout:
        st.error("⏱️ La consulta tardó demasiado. Intenta de nuevo.")
        return None
    except requests.exceptions.HTTPError as e:
        if response.status_code == 429:
            st.error("⚠️ Límite de requests alcanzado. Espera un momento.")
        else:
            st.error(f"❌ Error al consultar Instagram: {e}")
        return None
    except Exception as e:
        st.error(f"❌ Error inesperado: {e}")
        return None


# ─────────────────────────────────────────────
# OBTENER POSTS RECIENTES
# ─────────────────────────────────────────────

def get_recent_comments(username: str, max_posts: int = 2, max_comments: int = 20) -> list[str]:
    """
    Obtiene los captions (textos) de los posts más recientes del perfil.
    RapidAPI no siempre expone comentarios públicos, así que analizamos
    los captions de los posts como texto representativo.

    Args:
        username     (str): Nombre de usuario de Instagram.
        max_posts    (int): Número máximo de posts a retornar.
        max_comments (int): No usado directamente, mantenido por compatibilidad.

    Returns:
        list[str]: Lista de captions/textos de posts.
    """
    url = f"{BASE_URL}/userposts/"
    params = {"username_or_id": username, "count": max_posts}

    try:
        response = requests.get(url, headers=HEADERS, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        posts = data.get("data", {}).get("items", data.get("items", []))
        captions = []

        for post in posts[:max_posts]:
            caption = post.get("caption", {})
            if isinstance(caption, dict):
                text = caption.get("text", "")
            else:
                text = str(caption) if caption else ""
            if text:
                captions.append(text)

        return captions

    except requests.exceptions.Timeout:
        st.warning("⏱️ No se pudieron cargar los posts. Intenta de nuevo.")
        return []
    except Exception as e:
        st.warning(f"⚠️ No se pudieron cargar posts: {e}")
        return []


# ─────────────────────────────────────────────
# ANÁLISIS DE CUENTA FALSA
# ─────────────────────────────────────────────

def analyze_fake_account(profile_data: dict) -> dict:
    """
    Evalúa la probabilidad de que una cuenta sea falsa usando heurísticas.

    Args:
        profile_data (dict): Resultado de get_profile_info().

    Returns:
        dict con risk_score (0-100), level ('low'/'medium'/'high'), indicators.
    """
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
