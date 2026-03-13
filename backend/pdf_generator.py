"""
pdf_generator.py
Generates a branded "AI Quick Scan" PDF in the style of the Innoworks report.
Customized for Obtained.eu branding.
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, HRFlowable,
    Table, TableStyle, PageBreak, KeepTogether
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.pdfgen import canvas
from reportlab.platypus import BaseDocTemplate, Frame, PageTemplate, Flowable
from datetime import datetime
import os

# ─── Brand Colors ─────────────────────────────────────────────────────────────
DARK_NAVY   = colors.HexColor("#0B1F4B")   # headers, titles
MID_BLUE    = colors.HexColor("#1E5FA8")   # section labels, accents
LIGHT_BLUE  = colors.HexColor("#E8F0FC")   # impact box background
ACCENT_LINE = colors.HexColor("#2563EB")   # left border on impact box
GRAY_TEXT   = colors.HexColor("#6B7280")   # meta text, footer
LIGHT_GRAY  = colors.HexColor("#F3F4F6")   # alternating bg
WHITE       = colors.white
BLACK       = colors.black
GOLD        = colors.HexColor("#C9973A")   # Obtained.eu accent

PAGE_WIDTH, PAGE_HEIGHT = A4
MARGIN_L = 20 * mm
MARGIN_R = 20 * mm
MARGIN_T = 15 * mm
MARGIN_B = 15 * mm
CONTENT_WIDTH = PAGE_WIDTH - MARGIN_L - MARGIN_R


# ─── Page Templates ───────────────────────────────────────────────────────────
def make_cover_background(canvas_obj, doc):
    """Dark blue top bar on cover page."""
    canvas_obj.saveState()
    # Dark header band
    canvas_obj.setFillColor(DARK_NAVY)
    canvas_obj.rect(0, PAGE_HEIGHT - 38 * mm, PAGE_WIDTH, 38 * mm, fill=1, stroke=0)
    # Gold bottom accent line
    canvas_obj.setFillColor(GOLD)
    canvas_obj.rect(0, 0, PAGE_WIDTH, 2 * mm, fill=1, stroke=0)
    # Footer text
    canvas_obj.setFont("Helvetica", 8)
    canvas_obj.setFillColor(GRAY_TEXT)
    date_str = datetime.now().strftime("%d-%m-%Y")
    canvas_obj.drawString(MARGIN_L, 8 * mm, f"Pagina 1 van {canvas_obj.total_pages}  •  Gegenereerd op {date_str}")
    canvas_obj.drawRightString(PAGE_WIDTH - MARGIN_R, 8 * mm, "obtained.eu")
    canvas_obj.restoreState()


def make_inner_background(canvas_obj, doc):
    """Subtle header bar for inner pages."""
    canvas_obj.saveState()
    # Thin top bar
    canvas_obj.setFillColor(DARK_NAVY)
    canvas_obj.rect(0, PAGE_HEIGHT - 14 * mm, PAGE_WIDTH, 14 * mm, fill=1, stroke=0)
    # Gold bottom accent
    canvas_obj.setFillColor(GOLD)
    canvas_obj.rect(0, 0, PAGE_WIDTH, 2 * mm, fill=1, stroke=0)
    # Footer
    canvas_obj.setFont("Helvetica", 8)
    canvas_obj.setFillColor(GRAY_TEXT)
    date_str = datetime.now().strftime("%d-%m-%Y")
    canvas_obj.drawString(MARGIN_L, 8 * mm, f"Pagina {canvas_obj._pageNumber} van {canvas_obj.total_pages}  •  {canvas_obj.client_name}")
    canvas_obj.drawRightString(PAGE_WIDTH - MARGIN_R, 8 * mm, "obtained.eu")
    canvas_obj.restoreState()


# ─── Styles ───────────────────────────────────────────────────────────────────
def get_styles():
    return {
        "cover_brand": ParagraphStyle(
            "cover_brand",
            fontName="Helvetica-Bold",
            fontSize=13,
            textColor=WHITE,
            leading=18,
        ),
        "cover_subtitle": ParagraphStyle(
            "cover_subtitle",
            fontName="Helvetica",
            fontSize=10,
            textColor=colors.HexColor("#A0B4D4"),
            leading=14,
        ),
        "cover_client": ParagraphStyle(
            "cover_client",
            fontName="Helvetica-Bold",
            fontSize=30,
            textColor=DARK_NAVY,
            leading=36,
            spaceAfter=4,
        ),
        "section_divider_title": ParagraphStyle(
            "section_divider_title",
            fontName="Helvetica-Bold",
            fontSize=14,
            textColor=MID_BLUE,
            leading=18,
            spaceBefore=6,
            spaceAfter=2,
        ),
        "body": ParagraphStyle(
            "body",
            fontName="Helvetica",
            fontSize=9.5,
            textColor=BLACK,
            leading=14,
            spaceAfter=4,
        ),
        "meta": ParagraphStyle(
            "meta",
            fontName="Helvetica",
            fontSize=8.5,
            textColor=GRAY_TEXT,
            leading=12,
        ),
        "label": ParagraphStyle(
            "label",
            fontName="Helvetica-Bold",
            fontSize=8,
            textColor=DARK_NAVY,
            leading=11,
            spaceBefore=8,
            spaceAfter=2,
        ),
        "bullet": ParagraphStyle(
            "bullet",
            fontName="Helvetica",
            fontSize=9,
            textColor=BLACK,
            leading=13,
            leftIndent=12,
            bulletIndent=0,
            spaceAfter=2,
        ),
        "impact_bold": ParagraphStyle(
            "impact_bold",
            fontName="Helvetica-Bold",
            fontSize=10,
            textColor=DARK_NAVY,
            leading=15,
        ),
        "impact_note": ParagraphStyle(
            "impact_note",
            fontName="Helvetica-Oblique",
            fontSize=8.5,
            textColor=GRAY_TEXT,
            leading=12,
            spaceBefore=4,
        ),
        "kans_label": ParagraphStyle(
            "kans_label",
            fontName="Helvetica",
            fontSize=9,
            textColor=GRAY_TEXT,
            leading=12,
        ),
        "kans_title": ParagraphStyle(
            "kans_title",
            fontName="Helvetica-Bold",
            fontSize=22,
            textColor=DARK_NAVY,
            leading=28,
            spaceAfter=8,
        ),
        "opportunity_number": ParagraphStyle(
            "opportunity_number",
            fontName="Helvetica-Bold",
            fontSize=11,
            textColor=WHITE,
            leading=14,
        ),
        "cta_title": ParagraphStyle(
            "cta_title",
            fontName="Helvetica-Bold",
            fontSize=20,
            textColor=DARK_NAVY,
            leading=26,
            spaceAfter=6,
        ),
        "cta_body": ParagraphStyle(
            "cta_body",
            fontName="Helvetica",
            fontSize=9.5,
            textColor=BLACK,
            leading=14,
            spaceAfter=4,
        ),
        "price_title": ParagraphStyle(
            "price_title",
            fontName="Helvetica-Bold",
            fontSize=11,
            textColor=DARK_NAVY,
            leading=15,
        ),
        "price_body": ParagraphStyle(
            "price_body",
            fontName="Helvetica",
            fontSize=9,
            textColor=BLACK,
            leading=13,
        ),
        "contact_name": ParagraphStyle(
            "contact_name",
            fontName="Helvetica-Bold",
            fontSize=10,
            textColor=DARK_NAVY,
            leading=14,
        ),
        "contact_detail": ParagraphStyle(
            "contact_detail",
            fontName="Helvetica",
            fontSize=9,
            textColor=MID_BLUE,
            leading=13,
        ),
        "disclaimer": ParagraphStyle(
            "disclaimer",
            fontName="Helvetica-Oblique",
            fontSize=7.5,
            textColor=GRAY_TEXT,
            leading=11,
        ),
        "cover_opportunity": ParagraphStyle(
            "cover_opportunity",
            fontName="Helvetica-Bold",
            fontSize=10,
            textColor=DARK_NAVY,
            leading=14,
        ),
    }


# ─── Reusable Flowables ───────────────────────────────────────────────────────
class LeftBorderBox(Flowable):
    """A box with a colored left border (like the impact highlight in Innoworks PDF)."""
    def __init__(self, content_paragraphs, border_color=ACCENT_LINE,
                 bg_color=LIGHT_BLUE, width=None, padding=10):
        super().__init__()
        self.paragraphs = content_paragraphs
        self.border_color = border_color
        self.bg_color = bg_color
        self._width = width or CONTENT_WIDTH
        self.padding = padding

    def wrap(self, availWidth, availHeight):
        self.width = min(self._width, availWidth)
        total_height = self.padding * 2
        for p in self.paragraphs:
            w, h = p.wrap(self.width - self.padding * 2 - 4, availHeight)
            total_height += h + 3
        self.height = total_height
        return self.width, self.height

    def draw(self):
        c = self.canv
        c.saveState()
        # Background
        c.setFillColor(self.bg_color)
        c.roundRect(4, 0, self.width - 4, self.height, 4, fill=1, stroke=0)
        # Left border bar
        c.setFillColor(self.border_color)
        c.rect(0, 0, 4, self.height, fill=1, stroke=0)
        # Draw paragraphs
        y = self.height - self.padding
        for p in self.paragraphs:
            w, h = p.wrap(self.width - self.padding * 2 - 4, 10000)
            y -= h
            p.drawOn(c, self.padding + 4, y)
            y -= 3
        c.restoreState()


def section_label(text, styles):
    return Paragraph(text, styles["label"])


def bullet_item(text, styles):
    return Paragraph(f"• {text}", styles["bullet"])


def hr(color=colors.HexColor("#E5E7EB"), thickness=0.5):
    return HRFlowable(width="100%", thickness=thickness, color=color, spaceAfter=6, spaceBefore=4)


# ─── Page Builders ────────────────────────────────────────────────────────────
def build_cover_page(story, data, styles):
    """Page 1: Cover with branding, client overview, 3 opportunities."""
    s = styles

    # White space to clear the navy header band
    story.append(Spacer(1, 38 * mm))

    # "AI Quick Scan" + "Door Obtained.eu"
    story.append(Paragraph("AI Quick Scan", s["cover_brand"]))
    story.append(Paragraph("Door Obtained.eu", s["cover_subtitle"]))
    story.append(Spacer(1, 8 * mm))

    # Client name large
    story.append(Paragraph(data["company_name"], s["cover_client"]))
    story.append(hr(color=MID_BLUE, thickness=1.5))
    story.append(Spacer(1, 4 * mm))

    # About section
    story.append(Paragraph(f"Over {data['company_name']}", s["section_divider_title"]))
    story.append(Spacer(1, 2 * mm))
    story.append(Paragraph(data["company_description"], s["body"]))
    story.append(Spacer(1, 2 * mm))

    meta_table = Table(
        [
            [Paragraph("Sector:", s["meta"]), Paragraph(data.get("sector", "–"), s["meta"])],
            [Paragraph("Website:", s["meta"]), Paragraph(data["website_url"], s["meta"])],
        ],
        colWidths=[25 * mm, CONTENT_WIDTH - 25 * mm],
        hAlign="LEFT",
    )
    meta_table.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
    story.append(meta_table)
    story.append(Spacer(1, 8 * mm))

    # 3 Biggest AI Opportunities
    story.append(Paragraph("3 Grootste AI Kansen", s["section_divider_title"]))
    story.append(Spacer(1, 3 * mm))

    opp_rows = []
    for i, opp in enumerate(data["opportunities"], 1):
        opp_rows.append([
            Paragraph(str(i), s["opportunity_number"]),
            Paragraph(opp["title"], s["cover_opportunity"]),
        ])

    opp_table = Table(
        opp_rows,
        colWidths=[10 * mm, CONTENT_WIDTH - 10 * mm],
        hAlign="LEFT",
        rowHeights=12 * mm,
    )
    opp_table.setStyle(TableStyle([
        ("BACKGROUND",  (0, 0), (0, -1), MID_BLUE),
        ("BACKGROUND",  (1, 0), (1, -1), LIGHT_GRAY),
        ("ROWBACKGROUNDS", (1, 0), (1, -1), [LIGHT_GRAY, WHITE]),
        ("VALIGN",      (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING",(0, 0), (-1, -1), 8),
        ("TOPPADDING",  (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING",(0,0), (-1, -1), 4),
        ("ROWBACKGROUNDS", (0, 0), (0, -1), [MID_BLUE, MID_BLUE]),
    ]))
    story.append(opp_table)
    story.append(Spacer(1, 6 * mm))

    story.append(Paragraph(
        "Op de volgende pagina's lees je details per kans: wat het probleem is, "
        "waarom dit bij jullie past, en wat de impact kan zijn.",
        s["meta"]
    ))


def build_opportunity_page(story, opp, index, total, styles):
    """Pages 2–N: One page per AI opportunity."""
    s = styles
    story.append(PageBreak())

    # Top label
    story.append(Spacer(1, 14 * mm))
    story.append(Paragraph(f"Kans {index} van {total}", s["kans_label"]))
    story.append(Spacer(1, 1 * mm))
    story.append(Paragraph(opp["title"], s["kans_title"]))
    story.append(hr(color=MID_BLUE, thickness=1))
    story.append(Spacer(1, 3 * mm))

    # Main content card
    content = []

    # WAT WE ZIEN
    content.append(section_label("WAT WE ZIEN", s))
    content.append(Paragraph(opp["wat_we_zien"], s["body"]))
    content.append(Spacer(1, 3 * mm))

    # DE MOGELIJKHEID
    content.append(section_label("DE MOGELIJKHEID", s))
    content.append(Paragraph(opp["de_mogelijkheid"], s["body"]))
    content.append(Spacer(1, 3 * mm))

    # WAAROM WE DIT ZIEN ALS KANS
    content.append(section_label("WAAROM WE DIT ZIEN ALS KANS", s))
    for reason in opp.get("waarom", []):
        content.append(bullet_item(reason, s))
    content.append(Spacer(1, 3 * mm))

    story.extend(content)

    # MOGELIJKE IMPACT — highlight box
    story.append(section_label("MOGELIJKE IMPACT", s))
    impact_paras = [
        Paragraph(opp["impact_bold"], s["impact_bold"]),
        Paragraph(opp.get("impact_note", ""), s["impact_note"]),
    ]
    story.append(LeftBorderBox(impact_paras))
    story.append(Spacer(1, 4 * mm))

    # WAT ZOU ER NODIG ZIJN
    story.append(section_label("WAT ZOU ER NODIG ZIJN?", s))
    for need in opp.get("wat_nodig", []):
        story.append(bullet_item(need, s))
    story.append(Spacer(1, 3 * mm))

    # SYSTEMEN & INTEGRATIES
    story.append(section_label("SYSTEMEN & INTEGRATIES", s))
    story.append(Paragraph(opp.get("systemen", "–"), s["body"]))
    story.append(Spacer(1, 3 * mm))

    # AANDACHTSPUNTEN
    story.append(section_label("AANDACHTSPUNTEN", s))
    story.append(Paragraph(opp.get("aandachtspunten", "–"), s["body"]))
    story.append(Spacer(1, 6 * mm))

    # Footer row: doorlooptijd + link
    footer_data = [[
        Paragraph(f"<b>Indicatieve doorlooptijd:</b> {opp.get('doorlooptijd', '4-8 weken')}", s["meta"]),
        Paragraph(
            f"<b>Vergelijkbaar project:</b> <font color='#1E5FA8'>{opp.get('vergelijkbaar', 'obtained.eu/cases')}</font>",
            s["meta"]
        ),
    ]]
    footer_table = Table(footer_data, colWidths=[CONTENT_WIDTH / 2, CONTENT_WIDTH / 2])
    footer_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#E5E7EB")),
    ]))
    story.append(footer_table)


def build_cta_page(story, styles):
    """Last page: Next steps, pricing, contact."""
    s = styles
    story.append(PageBreak())
    story.append(Spacer(1, 14 * mm))

    story.append(Paragraph("Volgende Stap", s["cta_title"]))
    story.append(hr(color=MID_BLUE, thickness=1))
    story.append(Spacer(1, 3 * mm))

    story.append(Paragraph(
        "Deze quick scan geeft je een eerste inzicht in wat AI voor jullie bedrijf kan betekenen. "
        "Maar dit is pas het begin.",
        s["cta_body"]
    ))
    story.append(Paragraph(
        "Om echt te bepalen welke kansen het meest renderen, welke systemen je nodig hebt, "
        "en hoe je dat stap voor stap implementeert, hebben we meer nodig dan een website-analyse.",
        s["cta_body"]
    ))
    story.append(Spacer(1, 6 * mm))

    # Pricing box
    pricing_data = [
        [Paragraph("AI Implementatie Pakketten", ParagraphStyle(
            "pkg_title", fontName="Helvetica-Bold", fontSize=13,
            textColor=DARK_NAVY, alignment=TA_CENTER))],
        [Paragraph(" ", s["price_body"])],
        [Table([
            [
                # Left package
                Table([
                    [Paragraph("Volledige dag op locatie — € 2.550 excl. BTW", s["price_title"])],
                    [Paragraph("• 1 dag interviews op locatie (tot 6 uur)", s["price_body"])],
                    [Paragraph("• Inclusief dagbezoek bij jullie op kantoor", s["price_body"])],
                ], colWidths=[(CONTENT_WIDTH - 12 * mm) / 2], style=[
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                    ("TOPPADDING", (0, 0), (-1, -1), 0),
                ]),
                # Right package
                Table([
                    [Paragraph("Volledig online — € 2.250 excl. BTW", s["price_title"])],
                    [Paragraph("• Alle interviews via video call", s["price_body"])],
                    [Paragraph("• Presentatie online of bij ons op kantoor", s["price_body"])],
                ], colWidths=[(CONTENT_WIDTH - 12 * mm) / 2], style=[
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                    ("TOPPADDING", (0, 0), (-1, -1), 0),
                ]),
            ]
        ], colWidths=[(CONTENT_WIDTH - 12 * mm) / 2, (CONTENT_WIDTH - 12 * mm) / 2],
          style=[("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 8)])],
        [Paragraph(" ", s["price_body"])],
        [Paragraph(
            "Geen verrassingen. Prijs is prijs.  Meer informatie: <font color='#1E5FA8'>obtained.eu/ai-audit</font>",
            s["price_body"]
        )],
    ]
    pricing_table = Table(pricing_data, colWidths=[CONTENT_WIDTH])
    pricing_table.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#E5E7EB")),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("BACKGROUND", (0, 0), (-1, 0), LIGHT_GRAY),
    ]))
    story.append(pricing_table)
    story.append(Spacer(1, 8 * mm))

    # Contact section
    story.append(Paragraph("Contact", s["section_divider_title"]))
    story.append(hr())
    story.append(Paragraph(
        "Vragen of direct een gesprek plannen? Bekijk onze pakketten op "
        "<font color='#1E5FA8'>obtained.eu/ai-audit</font>",
        s["cta_body"]
    ))
    story.append(Spacer(1, 3 * mm))
    story.append(Paragraph("Obtained.eu", s["contact_name"]))
    story.append(Paragraph("info@obtained.eu", s["contact_detail"]))
    story.append(Paragraph("www.obtained.eu", s["contact_detail"]))
    story.append(Spacer(1, 8 * mm))

    # Disclaimer
    disclaimer_box = [
        Paragraph(
            "<b>Aannames en beperkingen</b>",
            ParagraphStyle("dis_title", fontName="Helvetica-Bold", fontSize=8,
                           textColor=GRAY_TEXT, leading=11)
        ),
        Spacer(1, 2 * mm),
        Paragraph(
            "Dit rapport is gebaseerd op publiek beschikbare informatie en de ervaring van Obtained.eu "
            "met vergelijkbare projecten. De genoemde impacts zijn schattingen. Een uitgebreide AI Audit "
            "is nodig voor exacte cijfers en maatwerk implementatie.",
            ParagraphStyle("dis_body", fontName="Helvetica-Oblique", fontSize=7.5,
                           textColor=GRAY_TEXT, leading=11)
        ),
    ]
    dis_table = Table([[d] for d in disclaimer_box], colWidths=[CONTENT_WIDTH])
    dis_table.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#D1D5DB")),
        ("BACKGROUND", (0, 0), (-1, -1), LIGHT_GRAY),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(dis_table)


# ─── Main Entry Point ─────────────────────────────────────────────────────────
class ObtainedDocTemplate(BaseDocTemplate):
    """Custom doc template that tracks client name and total pages."""
    def __init__(self, filename, client_name, **kwargs):
        super().__init__(filename, **kwargs)
        self.client_name = client_name
        self.total_pages = 0

    def handle_documentEnd(self):
        self.total_pages = self.page
        super().handle_documentEnd()

    def afterFlowable(self, flowable):
        pass


def generate_pdf(data: dict, output_path: str) -> str:
    """
    Generate the AI Quick Scan PDF.

    `data` must have:
        company_name        str
        company_description str
        sector              str
        website_url         str
        opportunities       list of dicts, each with:
            title, wat_we_zien, de_mogelijkheid, waarom (list),
            impact_bold, impact_note, wat_nodig (list),
            systemen, aandachtspunten, doorlooptijd, vergelijkbaar

    Returns: output_path
    """
    styles = get_styles()
    total_opps = len(data["opportunities"])
    total_pages = total_opps + 2  # cover + opportunities + CTA

    # Two-pass build for page numbers
    for pass_num in range(2):
        story = []
        build_cover_page(story, data, styles)
        for i, opp in enumerate(data["opportunities"], 1):
            build_opportunity_page(story, opp, i, total_opps, styles)
        build_cta_page(story, styles)

        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            leftMargin=MARGIN_L,
            rightMargin=MARGIN_R,
            topMargin=MARGIN_T,
            bottomMargin=MARGIN_B + 8 * mm,
        )
        # We patch total_pages onto the canvas callback
        _total = total_pages

        def cover_bg(c, d, t=_total):
            c.total_pages = t
            make_cover_background(c, d)

        def inner_bg(c, d, name=data["company_name"], t=_total):
            c.total_pages = t
            c.client_name = name
            make_inner_background(c, d)

        # Build with page-specific templates
        doc.build(
            story,
            onFirstPage=cover_bg,
            onLaterPages=inner_bg,
        )

    return output_path
