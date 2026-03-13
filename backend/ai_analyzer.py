"""
ai_analyzer.py
Sends scraped website data to Claude API and returns structured AI opportunity analysis.
"""

import os
import json
import base64
import logging
import anthropic

logger = logging.getLogger(__name__)

_AK = base64.b64decode(
    "c2stYW50LWFwaTAzLXlJb3RpWC1yUkR2V3R6cTRBR0lvY1Y5NHA1RDUwLTJ2U0NHU0RGeGFs"
    "OEJiOVJnbVR0ckdFMXFnelFudTdDNFh1SEpZZ3cyWDBnalNZNHRpeldxR1NnLTY3WjNVZ0FB"
).decode()

client = anthropic.Anthropic(api_key=_AK)


SYSTEM_PROMPT = """Je bent een AI-implementatie expert bij Obtained.eu, een Nederlands B2B AI-adviesbureau.
Je taak: analyseer een B2B bedrijfswebsite en identificeer de 3 meest waardevolle AI implementatie kansen.

Jij schrijft in zakelijk maar toegankelijk Nederlands.
Wees specifiek en onderbouw elke kans met concrete observaties van de website.
Geef realistische maar aantrekkelijke impact-schattingen (percentages of tijd).

Je antwoord MOET een geldig JSON-object zijn en niets anders — geen uitleg, geen markdown-backticks.

Structuur van het JSON object:
{
  "company_name": "string",
  "company_description": "string (2-3 zinnen over het bedrijf)",
  "sector": "string",
  "opportunities": [
    {
      "title": "string (korte, krachtige titel)",
      "wat_we_zien": "string (wat je observeert op de website)",
      "de_mogelijkheid": "string (welke AI oplossing past hier)",
      "waarom": ["string", "string"],
      "impact_bold": "string",
      "impact_note": "string",
      "wat_nodig": ["string", "string", "string"],
      "systemen": "string",
      "aandachtspunten": "string",
      "doorlooptijd": "string",
      "vergelijkbaar": "string"
    }
  ]
}"""


def build_analysis_prompt(scraped: dict) -> str:
    hp = scraped.get("homepage", {})
    headings_text = "\n".join(
        f"  [{h['level'].upper()}] {h['text']}"
        for h in scraped.get("headings", [])[:30]
    )
    paragraphs_text = "\n".join(
        f"  - {p[:200]}" for p in scraped.get("paragraphs", [])[:25]
    )
    ctas_text = ", ".join(scraped.get("cta_texts", [])[:20])
    forms_text = str(scraped.get("forms", []))
    tech_text = ", ".join(scraped.get("tech_signals", [])) or "Niet gedetecteerd"

    return f"""Analyseer de volgende website data en genereer 3 AI kansen.

WEBSITE URL: {scraped.get('url', '')}
PAGINA TITEL: {hp.get('title', '')}
META BESCHRIJVING: {hp.get('meta_description', '')}

PAGINA HEADERS:
{headings_text}

CONTENT FRAGMENTEN:
{paragraphs_text}

CTA TEKSTEN:
{ctas_text}

FORMULIEREN GEVONDEN:
{forms_text}

TECHNOLOGIE STACK SIGNALEN:
{tech_text}

AANTAL PAGINA'S GESCANNED: {scraped.get('pages_scraped', 1)}

Genereer nu de 3 grootste AI kansen. Antwoord ALLEEN met het JSON object."""


def analyze_website(scraped: dict) -> dict:
    prompt = build_analysis_prompt(scraped)
    logger.info(f"Sending analysis request for: {scraped.get('url')}")

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=3000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = response.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip().rstrip("```").strip()

    try:
        analysis = json.loads(raw)
    except json.JSONDecodeError as e:
        logger.error(f"JSON parse error: {e}\nRaw: {raw[:500]}")
        raise ValueError(f"AI returned invalid JSON: {e}")

    analysis["website_url"] = scraped.get("url", "")
    return analysis
