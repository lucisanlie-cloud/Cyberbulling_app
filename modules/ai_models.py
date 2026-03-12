"""
ai_models.py
------------
Módulo de carga y gestión de modelos de inteligencia artificial para CyberShield AI.
Centraliza la inicialización de pipelines de Hugging Face con caché de Streamlit.

Author: Luci Jabba
Copyright (c) 2026 Luci Jabba
"""

import streamlit as st
from transformers import pipeline


# ─────────────────────────────────────────────
# MODELOS DISPONIBLES
# ─────────────────────────────────────────────

TOXICITY_MODEL_ID = "unitary/toxic-bert"


# ─────────────────────────────────────────────
# CARGA DE MODELOS (CON CACHÉ)
# ─────────────────────────────────────────────

@st.cache_resource(show_spinner="Cargando modelo de IA…")
def load_toxicity_model():
    """
    Carga y cachea el modelo de detección de toxicidad 'unitary/toxic-bert'.

    El decorador @st.cache_resource garantiza que el modelo se cargue
    solo una vez por sesión del servidor, optimizando el uso de memoria.

    Returns:
        transformers.Pipeline: Pipeline de clasificación de texto configurado
        con el modelo toxic-bert.

    Raises:
        OSError: Si el modelo no puede descargarse o encontrarse en caché local.
    """
    return pipeline("text-classification", model=TOXICITY_MODEL_ID)


# ─────────────────────────────────────────────
# ANÁLISIS DE TOXICIDAD
# ─────────────────────────────────────────────

def analyze_toxicity(model, text: str) -> dict:
    """
    Analiza el nivel de toxicidad de un texto dado.

    Args:
        model: Pipeline de clasificación cargado con load_toxicity_model().
        text  (str): Texto a analizar.

    Returns:
        dict: Diccionario con las claves:
            - 'score' (int): Puntuación de toxicidad de 0 a 100.
            - 'label' (str): Etiqueta del modelo ('TOXIC' o 'NON_TOXIC').
            - 'level'  (str): Nivel semántico ('safe', 'warning', 'danger').

    Example:
        >>> result = analyze_toxicity(model, "I hate you")
        >>> print(result)
        {'score': 87, 'label': 'TOXIC', 'level': 'danger'}
    """
    # BUG FIX: El código original no validaba si el texto estaba vacío,
    # lo que causaba un error en el modelo con strings vacíos.
    if not text or not text.strip():
        return {"score": 0, "label": "NON_TOXIC", "level": "safe"}

    raw = model(text[:512])  # Limitar a 512 tokens máximo del modelo BERT
    score = int(raw[0]["score"] * 100)
    label = raw[0]["label"]

    if score < 30:
        level = "safe"
    elif score < 60:
        level = "warning"
    else:
        level = "danger"

    return {"score": score, "label": label, "level": level}


def analyze_batch(model, texts: list) -> list:
    """
    Analiza una lista de textos y retorna sus niveles de toxicidad.

    Args:
        model: Pipeline de clasificación cargado.
        texts (list[str]): Lista de textos a analizar.

    Returns:
        list[dict]: Lista de resultados, cada uno con el formato de analyze_toxicity().
    """
    # BUG FIX: El código original del batch no tenía manejo de errores
    # por línea, haciendo que un solo texto inválido rompiera todo el análisis.
    results = []
    for text in texts:
        try:
            results.append(analyze_toxicity(model, text))
        except Exception as e:
            results.append({"score": 0, "label": "ERROR", "level": "safe", "error": str(e)})
    return results
