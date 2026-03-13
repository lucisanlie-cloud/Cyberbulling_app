"""
ai_models.py
------------
AI model loading and management module for CyberShield AI.
Centralizes Hugging Face pipeline initialization with Streamlit caching.

Author: Luci Jabba
Copyright (c) 2026 Luci Jabba
"""

import streamlit as st
from transformers import pipeline

TOXICITY_MODEL_ID = "unitary/toxic-bert"

@st.cache_resource(show_spinner="Loading AI model…")
def load_toxicity_model():
    return pipeline("text-classification", model=TOXICITY_MODEL_ID)

def analyze_toxicity(model, text: str) -> dict:
    if not text or not text.strip():
        return {"score": 0, "label": "NON_TOXIC", "level": "safe"}
    raw = model(text[:512])
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
    results = []
    for text in texts:
        try:
            results.append(analyze_toxicity(model, text))
        except Exception as e:
            results.append({"score": 0, "label": "ERROR", "level": "safe", "error": str(e)})
    return results
