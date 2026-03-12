"""
email_alerts.py
---------------
Módulo de notificaciones por email para CyberShield AI.
Envía alertas cuando se detecta un incidente de alta toxicidad.

Configuración necesaria en .env:
    EMAIL_SENDER=tu_correo@gmail.com
    EMAIL_PASSWORD=tu_contraseña_de_aplicacion   ← NO tu contraseña normal
    EMAIL_RECEIVER=correo_donde_recibes_alertas@gmail.com

Para Gmail: activa "Contraseñas de aplicación" en tu cuenta Google.

Author: Luci Jabba
Copyright (c) 2026 Luci Jabba
"""

import os
import smtplib
import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ─────────────────────────────────────────────
# CONFIGURACIÓN
# ─────────────────────────────────────────────

EMAIL_SENDER   = os.getenv("EMAIL_SENDER",   "")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")
EMAIL_RECEIVER = os.getenv("EMAIL_RECEIVER", "")

# Solo enviar alertas si la toxicidad supera este umbral
ALERT_THRESHOLD = 70


# ─────────────────────────────────────────────
# ENVÍO DE EMAIL
# ─────────────────────────────────────────────

def send_alert_email(reporter: str, aggressor: str, message: str, score: int) -> bool:
    """
    Envía un email de alerta cuando se reporta un incidente de alta toxicidad.

    Args:
        reporter  : Usuario que reportó el incidente.
        aggressor : Usuario agresor identificado.
        message   : Descripción del incidente.
        score     : Puntuación de toxicidad (0-100).

    Returns:
        bool: True si el email se envió correctamente, False si falló.
    """
    if not all([EMAIL_SENDER, EMAIL_PASSWORD, EMAIL_RECEIVER]):
        return False  # Credenciales no configuradas, ignorar silenciosamente

    if score < ALERT_THRESHOLD:
        return False  # No alcanza el umbral de alerta

    try:
        fecha = datetime.datetime.now().strftime("%d/%m/%Y a las %H:%M")

        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"🚨 CyberShield AI — Alerta de incidente (Toxicidad: {score}%)"
        msg["From"]    = EMAIL_SENDER
        msg["To"]      = EMAIL_RECEIVER

        html = f"""
        <html><body style="font-family: Arial, sans-serif; background: #f4f4f4; padding: 20px;">
          <div style="max-width: 600px; margin: auto; background: white; border-radius: 12px;
                      overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">

            <!-- Header -->
            <div style="background: #6B21A8; padding: 24px; text-align: center;">
              <h1 style="color: white; margin: 0; font-size: 22px;">🛡 CyberShield AI</h1>
              <p style="color: #DDD6FE; margin: 4px 0 0;">Alerta de Incidente Detectado</p>
            </div>

            <!-- Body -->
            <div style="padding: 24px;">
              <div style="background: #FEF2F2; border-left: 4px solid #DC2626;
                          padding: 12px 16px; border-radius: 4px; margin-bottom: 20px;">
                <strong style="color: #DC2626;">⚠️ Nivel de toxicidad: {score}/100</strong>
              </div>

              <table style="width: 100%; border-collapse: collapse;">
                <tr style="border-bottom: 1px solid #E5E7EB;">
                  <td style="padding: 10px; color: #6B7280; width: 40%;">Reportado por</td>
                  <td style="padding: 10px; font-weight: bold;">{reporter}</td>
                </tr>
                <tr style="border-bottom: 1px solid #E5E7EB;">
                  <td style="padding: 10px; color: #6B7280;">Agresor identificado</td>
                  <td style="padding: 10px; font-weight: bold; color: #DC2626;">{aggressor}</td>
                </tr>
                <tr style="border-bottom: 1px solid #E5E7EB;">
                  <td style="padding: 10px; color: #6B7280;">Fecha</td>
                  <td style="padding: 10px;">{fecha}</td>
                </tr>
                <tr>
                  <td style="padding: 10px; color: #6B7280; vertical-align: top;">Descripción</td>
                  <td style="padding: 10px;">{message}</td>
                </tr>
              </table>
            </div>

            <!-- Footer -->
            <div style="background: #F9FAFB; padding: 16px; text-align: center;
                        border-top: 1px solid #E5E7EB;">
              <p style="color: #9CA3AF; font-size: 12px; margin: 0;">
                CyberShield AI — Plataforma de IA Contra el Ciberacoso<br>
                Copyright © 2026 Luci Jabba
              </p>
            </div>
          </div>
        </body></html>
        """

        msg.attach(MIMEText(html, "html"))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.sendmail(EMAIL_SENDER, EMAIL_RECEIVER, msg.as_string())

        return True

    except Exception:
        return False  # Fallar silenciosamente para no interrumpir la app


def is_email_configured() -> bool:
    """Retorna True si las credenciales de email están configuradas."""
    return all([EMAIL_SENDER, EMAIL_PASSWORD, EMAIL_RECEIVER])
