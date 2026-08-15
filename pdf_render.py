# -*- coding: utf-8 -*-
"""
Shared PDF building blocks (branding, fonts, tables) for the
SIMON ORIGIN TRANSFORMATION blueprint generator.
"""
import os
import re
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FONT_DIR = os.path.join(BASE_DIR, "fonts")

# ---- Brand palette ----
INK = colors.HexColor("#1A1A1A")
GOLD = colors.HexColor("#B8860B")
LIGHT_GOLD = colors.HexColor("#F4E9CF")
BAND = colors.HexColor("#F5F5F5")
WHITE = colors.white
GREY_TEXT = colors.HexColor("#555555")

_FONTS_REGISTERED = False

_ETHIOPIC_RE = re.compile(r"[\u1200-\u139F\u2D80-\u2DDF\uAB00-\uAB2F]+")


def _xml_escape(s: str) -> str:
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def mixed_font(text: str, bold: bool = False) -> str:
    """
    Returns ReportLab mini-markup where Ethiopic-script substrings are
    wrapped in the NotoEthiopic font and everything else (Latin letters,
    digits, punctuation) is left for the surrounding paragraph's base font.
    """
    font_name = "NotoEthiopic-Bold" if bold else "NotoEthiopic"
    text = str(text)
    parts = []
    last = 0
    for m in _ETHIOPIC_RE.finditer(text):
        if m.start() > last:
            parts.append(_xml_escape(text[last:m.start()]))
        parts.append(f'<font name="{font_name}">{_xml_escape(m.group())}</font>')
        last = m.end()
    if last < len(text):
        parts.append(_xml_escape(text[last:]))
    return "".join(parts)


def register_fonts():
    global _FONTS_REGISTERED
    if _FONTS_REGISTERED:
        return
    pdfmetrics.registerFont(TTFont("NotoEthiopic", os.path.join(FONT_DIR, "NotoSansEthiopic-Regular.ttf")))
    pdfmetrics.registerFont(TTFont("NotoEthiopic-Bold", os.path.join(FONT_DIR, "NotoSansEthiopic-Bold.ttf")))
    _FONTS_REGISTERED = True


def get_styles():
    register_fonts()
    ss = getSampleStyleSheet()
    styles = {
        "brand": ParagraphStyle("brand", parent=ss["Normal"], fontName="Helvetica-Bold",
                                 fontSize=17, textColor=WHITE, alignment=TA_CENTER, leading=20),
        "doctitle": ParagraphStyle("doctitle", parent=ss["Normal"], fontName="Helvetica-Bold",
                                    fontSize=13, textColor=GOLD, alignment=TA_CENTER, leading=16),
        "doctitle_am": ParagraphStyle("doctitle_am", parent=ss["Normal"], fontName="Helvetica",
                                       fontSize=10, textColor=LIGHT_GOLD, alignment=TA_CENTER, leading=14),
        "meta": ParagraphStyle("meta", parent=ss["Normal"], fontName="Helvetica",
                                fontSize=9, textColor=GREY_TEXT, alignment=TA_LEFT, leading=12),
        "section_en": ParagraphStyle("section_en", parent=ss["Normal"], fontName="Helvetica-Bold",
                                      fontSize=12.5, textColor=INK, spaceBefore=14, spaceAfter=1),
        "section_am": ParagraphStyle("section_am", parent=ss["Normal"], fontName="Helvetica-Oblique",
                                      fontSize=9.5, textColor=GREY_TEXT, spaceAfter=6),
        "body": ParagraphStyle("body", parent=ss["Normal"], fontName="Helvetica",
                                fontSize=9, textColor=INK, leading=12),
        "cell_en": ParagraphStyle("cell_en", parent=ss["Normal"], fontName="Helvetica",
                                   fontSize=8.3, textColor=INK, leading=10.5),
        "cell_en_bold": ParagraphStyle("cell_en_bold", parent=ss["Normal"], fontName="Helvetica-Bold",
                                        fontSize=8.5, textColor=INK, leading=10.5),
        "cell_am": ParagraphStyle("cell_am", parent=ss["Normal"], fontName="Helvetica",
                                   fontSize=8, textColor=GREY_TEXT, leading=11),
        "header_cell": ParagraphStyle("header_cell", parent=ss["Normal"], fontName="Helvetica-Bold",
                                       fontSize=8.5, textColor=WHITE, leading=10.5),
        "footer": ParagraphStyle("footer", parent=ss["Normal"], fontName="Helvetica-Oblique",
                                  fontSize=8, textColor=GREY_TEXT, alignment=TA_CENTER),
        "footer_am": ParagraphStyle("footer_am", parent=ss["Normal"], fontName="Helvetica-Oblique",
                                     fontSize=7.5, textColor=GREY_TEXT, alignment=TA_CENTER),
    }
    return styles


def build_header(styles, doc_title_en, doc_title_am, client_name, date_str, coach_handle="@Simonoriginbot"):
    flow = []
    header_tbl = Table(
        [[Paragraph("SIMON ORIGIN TRANSFORMATION", styles["brand"])],
         [Paragraph(doc_title_en, styles["doctitle"])],
         [Paragraph(mixed_font(doc_title_am), styles["doctitle_am"])]],
        colWidths=[170 * mm],
    )
    header_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), INK),
        ("TOPPADDING", (0, 0), (0, 0), 12),
        ("BOTTOMPADDING", (0, 0), (0, 0), 2),
        ("TOPPADDING", (0, 1), (0, 1), 4),
        ("BOTTOMPADDING", (0, 2), (0, 2), 12),
        ("LINEBELOW", (0, -1), (-1, -1), 2, GOLD),
    ]))
    flow.append(header_tbl)
    flow.append(Spacer(1, 8))
    meta_tbl = Table(
        [[Paragraph(f"<b>Prepared exclusively for:</b> {client_name}", styles["meta"]),
          Paragraph(f"<b>Date:</b> {date_str}", styles["meta"]),
          Paragraph(f"<b>Coach:</b> {coach_handle}", styles["meta"])]],
        colWidths=[70 * mm, 50 * mm, 50 * mm],
    )
    meta_tbl.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    flow.append(meta_tbl)
    flow.append(HRFlowable(width="100%", thickness=1, color=GOLD, spaceAfter=8))
    return flow


def build_snapshot_table(styles, rows):
    """rows: list of (label_en, label_am, value)"""
    data = []
    for label_en, label_am, value in rows:
        label_para = Paragraph(
            f'<font name="Helvetica-Bold">{_xml_escape(label_en)}</font><br/>'
            f'<font size="7.5" color="#777777">{mixed_font(label_am)}</font>',
            styles["cell_en"])
        data.append([label_para, Paragraph(mixed_font(value), styles["cell_en"])])

    tbl = Table(data, colWidths=[60 * mm, 110 * mm])
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), LIGHT_GOLD),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#DDDDDD")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#DDDDDD")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    return tbl


def section_title(styles, en, am):
    return [Paragraph(_xml_escape(en), styles["section_en"]),
            Paragraph(mixed_font(am), styles["section_am"])]


def footer_note(styles, coach_handle="@Simonoriginbot"):
    return [
        Spacer(1, 10),
        HRFlowable(width="100%", thickness=0.75, color=colors.HexColor("#DDDDDD"), spaceAfter=6),
        Paragraph(f"Questions about this plan? Message {coach_handle} on Telegram.", styles["footer"]),
        Paragraph(mixed_font(f"ስለዚህ ዕቅድ ጥያቄ ካለዎት {coach_handle} በቴሌግራም ያግኙን።"), styles["footer_am"]),
    ]


def make_doc(path):
    return SimpleDocTemplate(
        path, pagesize=A4,
        topMargin=14 * mm, bottomMargin=14 * mm,
        leftMargin=20 * mm, rightMargin=20 * mm,
        title="Simon Origin Transformation Blueprint",
    )


TABLE_HEADER_STYLE = [
    ("BACKGROUND", (0, 0), (-1, 0), INK),
    ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
    ("FONTSIZE", (0, 0), (-1, 0), 8.5),
    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#DDDDDD")),
    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, BAND]),
    ("TOPPADDING", (0, 0), (-1, -1), 4),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ("LEFTPADDING", (0, 0), (-1, -1), 5),
    ("RIGHTPADDING", (0, 0), (-1, -1), 5),
]
