"""
export_pdf.py
-------------
Módulo de exportación de reportes a PDF para CyberShield AI.
Genera un reporte profesional con todos los incidentes de la base de datos.

Author: Luci Jabba
Copyright (c) 2026 Luci Jabba
"""

import io
import datetime

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)


# ─────────────────────────────────────────────
# COLORES DE LA APP
# ─────────────────────────────────────────────

PURPLE      = colors.HexColor("#6B21A8")
LIGHT_PURPLE= colors.HexColor("#EDE9FE")
DARK_GRAY   = colors.HexColor("#1F2937")
MED_GRAY    = colors.HexColor("#6B7280")
RED         = colors.HexColor("#DC2626")
GREEN       = colors.HexColor("#16A34A")
YELLOW      = colors.HexColor("#D97706")


# ─────────────────────────────────────────────
# GENERADOR DE PDF
# ─────────────────────────────────────────────

def generate_reports_pdf(reports_df, total_users: int = 0) -> bytes:
    """
    Genera un PDF profesional con todos los reportes de incidentes.

    Args:
        reports_df  (pd.DataFrame): DataFrame con columnas id, reporter,
                                    aggressor, message, created_at.
        total_users (int): Total de usuarios registrados (para métricas).

    Returns:
        bytes: Contenido del PDF listo para descargar.
    """
    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=0.75 * inch,
        leftMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
    )

    styles = getSampleStyleSheet()
    story  = []

    # ── Estilos personalizados ────────────────
    title_style = ParagraphStyle(
        "CustomTitle",
        parent=styles["Title"],
        textColor=PURPLE,
        fontSize=22,
        spaceAfter=4,
    )
    subtitle_style = ParagraphStyle(
        "CustomSubtitle",
        parent=styles["Normal"],
        textColor=MED_GRAY,
        fontSize=11,
        spaceAfter=16,
    )
    section_style = ParagraphStyle(
        "SectionHeader",
        parent=styles["Heading2"],
        textColor=PURPLE,
        fontSize=13,
        spaceBefore=16,
        spaceAfter=8,
    )
    normal_style = ParagraphStyle(
        "CustomNormal",
        parent=styles["Normal"],
        textColor=DARK_GRAY,
        fontSize=10,
    )
    small_style = ParagraphStyle(
        "SmallGray",
        parent=styles["Normal"],
        textColor=MED_GRAY,
        fontSize=8,
    )

    # ── Encabezado ────────────────────────────
    story.append(Paragraph("🛡 CyberShield AI", title_style))
    story.append(Paragraph("Reporte de Incidentes de Ciberacoso", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=2, color=PURPLE))
    story.append(Spacer(1, 12))

    # ── Fecha y metadatos ─────────────────────
    fecha = datetime.datetime.now().strftime("%d/%m/%Y a las %H:%M")
    story.append(Paragraph(f"Generado el {fecha}", small_style))
    story.append(Spacer(1, 8))

    # ── Métricas resumen ──────────────────────
    story.append(Paragraph("Resumen Ejecutivo", section_style))

    total_reportes = len(reports_df)
    agresores_unicos = reports_df["aggressor"].nunique() if total_reportes > 0 else 0
    reporteros_unicos = reports_df["reporter"].nunique() if total_reportes > 0 else 0

    metrics_data = [
        ["Métrica", "Valor"],
        ["Total de incidentes reportados", str(total_reportes)],
        ["Agresores únicos identificados", str(agresores_unicos)],
        ["Usuarios que reportaron", str(reporteros_unicos)],
        ["Usuarios registrados en la plataforma", str(total_users)],
    ]

    metrics_table = Table(metrics_data, colWidths=[4 * inch, 2.5 * inch])
    metrics_table.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (-1, 0),  PURPLE),
        ("TEXTCOLOR",    (0, 0), (-1, 0),  colors.white),
        ("FONTNAME",     (0, 0), (-1, 0),  "Helvetica-Bold"),
        ("FONTSIZE",     (0, 0), (-1, 0),  10),
        ("BACKGROUND",   (0, 1), (-1, -1), LIGHT_PURPLE),
        ("ROWBACKGROUNDS",(0,1), (-1,-1),  [colors.white, LIGHT_PURPLE]),
        ("FONTNAME",     (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE",     (0, 1), (-1, -1), 10),
        ("TEXTCOLOR",    (0, 1), (-1, -1), DARK_GRAY),
        ("ALIGN",        (1, 0), (1, -1),  "CENTER"),
        ("GRID",         (0, 0), (-1, -1), 0.5, colors.HexColor("#D1D5DB")),
        ("ROWPADDING",   (0, 0), (-1, -1), 6),
    ]))
    story.append(metrics_table)
    story.append(Spacer(1, 16))

    # ── Tabla de reportes ─────────────────────
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#D1D5DB")))
    story.append(Paragraph("Detalle de Incidentes", section_style))

    if total_reportes == 0:
        story.append(Paragraph("No hay incidentes registrados en la base de datos.", normal_style))
    else:
        # Encabezado de tabla
        table_data = [["#", "Reportado por", "Agresor", "Descripción", "Fecha"]]

        for _, row in reports_df.iterrows():
            # Truncar mensaje largo para que entre en la celda
            mensaje = str(row["message"])
            if len(mensaje) > 80:
                mensaje = mensaje[:77] + "..."

            # Formatear fecha
            try:
                fecha_dt = datetime.datetime.fromisoformat(str(row["created_at"]))
                fecha_str = fecha_dt.strftime("%d/%m/%Y")
            except Exception:
                fecha_str = str(row["created_at"])[:10]

            table_data.append([
                str(row["id"]),
                Paragraph(str(row["reporter"]), small_style),
                Paragraph(str(row["aggressor"]), small_style),
                Paragraph(mensaje, small_style),
                fecha_str,
            ])

        col_widths = [0.4*inch, 1.2*inch, 1.2*inch, 3.2*inch, 0.9*inch]
        report_table = Table(table_data, colWidths=col_widths, repeatRows=1)
        report_table.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, 0),  PURPLE),
            ("TEXTCOLOR",     (0, 0), (-1, 0),  colors.white),
            ("FONTNAME",      (0, 0), (-1, 0),  "Helvetica-Bold"),
            ("FONTSIZE",      (0, 0), (-1, 0),  9),
            ("ROWBACKGROUNDS",(0, 1), (-1, -1), [colors.white, LIGHT_PURPLE]),
            ("FONTNAME",      (0, 1), (-1, -1), "Helvetica"),
            ("FONTSIZE",      (0, 1), (-1, -1), 8),
            ("TEXTCOLOR",     (0, 1), (-1, -1), DARK_GRAY),
            ("ALIGN",         (0, 0), (0, -1),  "CENTER"),
            ("ALIGN",         (4, 0), (4, -1),  "CENTER"),
            ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
            ("GRID",          (0, 0), (-1, -1), 0.3, colors.HexColor("#E5E7EB")),
            ("ROWPADDING",    (0, 0), (-1, -1), 5),
        ]))
        story.append(report_table)

    # ── Pie de página ─────────────────────────
    story.append(Spacer(1, 24))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#D1D5DB")))
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        "CyberShield AI — Plataforma de IA Contra el Ciberacoso | Copyright © 2026 Luci Jabba",
        small_style
    ))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()
