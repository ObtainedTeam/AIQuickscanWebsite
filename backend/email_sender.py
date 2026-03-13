"""
email_sender.py
Sends the generated AI Quick Scan PDF to the requester via Brevo API.
"""

import os
import base64
import logging

logger = logging.getLogger(__name__)

FROM_EMAIL = os.getenv("FROM_EMAIL", "info@obtained.nl")
FROM_NAME  = os.getenv("FROM_NAME", "Obtained.eu AI Scan")

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    body {{ font-family: Arial, sans-serif; background: #f4f6f9; margin: 0; padding: 0; }}
    .container {{ max-width: 600px; margin: 40px auto; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 12px rgba(0,0,0,0.1); }}
    .header {{ background: #0B1F4B; padding: 32px 40px; }}
    .header h1 {{ color: white; margin: 0; font-size: 24px; }}
    .header p {{ color: #A0B4D4; margin: 6px 0 0; font-size: 13px; }}
    .body {{ padding: 32px 40px; }}
    .body h2 {{ color: #0B1F4B; font-size: 18px; margin-top: 0; }}
    .body p {{ color: #374151; font-size: 14px; line-height: 1.6; }}
    .opportunities {{ background: #F3F4F6; border-radius: 6px; padding: 20px; margin: 20px 0; }}
    .opportunity {{ display: flex; align-items: flex-start; margin-bottom: 12px; }}
    .opp-num {{ background: #1E5FA8; color: white; border-radius: 4px; width: 24px; height: 24px; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 12px; flex-shrink: 0; margin-right: 12px; margin-top: 1px; }}
    .opp-text {{ color: #0B1F4B; font-weight: bold; font-size: 14px; }}
    .cta {{ background: #1E5FA8; color: white; padding: 12px 28px; border-radius: 6px; text-decoration: none; font-weight: bold; font-size: 14px; display: inline-block; margin: 12px 0; }}
    .footer {{ background: #F9FAFB; border-top: 1px solid #E5E7EB; padding: 20px 40px; text-align: center; }}
    .footer p {{ color: #9CA3AF; font-size: 12px; margin: 4px 0; }}
    .gold-bar {{ height: 3px; background: linear-gradient(90deg, #C9973A, #1E5FA8); }}
  </style>
</head>
<body>
  <div class="container">
    <div class="gold-bar"></div>
    <div class="header">
      <h1>Jouw AI Quick Scan is klaar!</h1>
      <p>Door Obtained.eu — AI implementatie voor B2B bedrijven</p>
    </div>
    <div class="body">
      <h2>Hoi {first_name},</h2>
      <p>
        Goed nieuws — we hebben <strong>{website}</strong> geanalyseerd en 
        de 3 grootste AI kansen voor jouw bedrijf in kaart gebracht.
      </p>
      <p>Jouw rapport bevat:</p>
      <div class="opportunities">
        {opportunities_html}
      </div>
      <p>
        Het volledige rapport vind je als bijlage in deze e-mail. 
        Wil je weten hoe je deze kansen concreet kunt aanpakken? 
        Plan een vrijblijvend gesprek van 30 minuten.
      </p>
      <a href="https://obtained.eu/contact" class="cta">Plan een gratis gesprek →</a>
      <p style="font-size: 13px; color: #6B7280;">
        Dit rapport is gebaseerd op een geautomatiseerde analyse van jullie website. 
        Voor exacte cijfers en maatwerk implementatie is een diepere AI Audit nodig.
      </p>
    </div>
    <div class="footer">
      <p><strong>Obtained.eu</strong></p>
      <p>info@obtained.eu | www.obtained.eu</p>
      <p style="margin-top: 10px;">Je ontvangt deze e-mail omdat je een AI Quick Scan hebt aangevraagd.</p>
    </div>
    <div class="gold-bar"></div>
  </div>
</body>
</html>
"""


def build_opportunities_html(opportunities: list) -> str:
    html = ""
    for i, opp in enumerate(opportunities, 1):
        html += f"""
        <div class="opportunity">
          <div class="opp-num">{i}</div>
          <div class="opp-text">{opp['title']}</div>
        </div>"""
    return html


def send_report(to_email: str, analysis: dict, pdf_path: str) -> bool:
    """Send the AI Quick Scan PDF via Brevo API."""
    import httpx

    api_key = os.getenv("BREVO_KEY") or "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"
    logger.info(f"Brevo API key present: {bool(api_key)}")

    if not api_key:
        raise RuntimeError("BREVO_API_KEY is not set.")

    company_name = analysis.get("company_name", "Uw bedrijf")
    website = analysis.get("website_url", "")
    opportunities = analysis.get("opportunities", [])
    first_name = to_email.split("@")[0].split(".")[0].capitalize()

    opp_html = build_opportunities_html(opportunities)
    html_body = HTML_TEMPLATE.format(
        first_name=first_name,
        website=website,
        opportunities_html=opp_html,
    )

    with open(pdf_path, "rb") as f:
        pdf_data = base64.b64encode(f.read()).decode()

    payload = {
        "sender": {"name": FROM_NAME, "email": FROM_EMAIL},
        "to": [{"email": to_email}],
        "subject": f"Jouw AI Quick Scan voor {company_name} — Obtained.eu",
        "htmlContent": html_body,
        "attachment": [{"content": pdf_data, "name": f"AI-Quick-Scan-{company_name.replace(' ', '-')}.pdf"}]
    }

    response = httpx.post(
        "https://api.brevo.com/v3/smtp/email",
        headers={
            "api-key": api_key,
            "Content-Type": "application/json"
        },
        json=payload
    )

    logger.info(f"Brevo response: {response.status_code} — {response.text}")
    return response.status_code == 201
