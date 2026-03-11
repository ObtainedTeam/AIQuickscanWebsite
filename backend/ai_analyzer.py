"""
ai_analyzer.py
Sends scraped website data to Claude API and returns structured AI opportunity analysis.
"""

import json
import logging
import anthropic

logger = logging.getLogger(__name__)

client = anthropic.Anthropic()  # Uses ANTHROPIC_API_KEY env var


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
      "waarom": ["string", "string"] (2-3 concrete redenen gebaseerd op website observaties),
      "impact_bold": "string (1 zin met concrete impact schatting, bijv: '25-40% tijdsbesparing...')",
      "impact_note": "string (korte onderbouwing van de schatting)",
      "wat_nodig": ["string", "string", "string"] (3 praktische requirements),
      "systemen": "string (komma-gescheiden lijst van relevante tools/systemen)",
      "aandachtspunten": "string (1 risico + mitigatie)",
      "doorlooptijd": "string (bijv: '4-8 weken')",
      "vergelijkbaar": "string (URL placeholder: obtained.eu/cases/[slug])"
    }
  ]
}"""


def build_analysis_prompt(scraped: dict) -> str:
    """Build the user prompt from scraped website data."""
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

PAGINA HEADERS (structuur van de website):
{headings_text}

CONTENT FRAGMENTEN:
{paragraphs_text}

CTA TEKSTEN (knoppen/links):
{ctas_text}

FORMULIEREN GEVONDEN:
{forms_text}

TECHNOLOGIE STACK SIGNALEN:
{tech_text}

AANTAL PAGINA'S GESCANNED: {scraped.get('pages_scraped', 1)}

Genereer nu de 3 grootste AI kansen voor dit bedrijf. 
Zorg dat elke kans:
1. Concreet gebaseerd is op wat je ziet in de website data
2. Relevant is voor B2B bedrijfsprocessen
3. Realistisch implementeerbaar is
4. Een meetbare impact heeft

Antwoord ALLEEN met het JSON object."""


def analyze_website(scraped: dict) -> dict:
    """
    Call Claude API with scraped website data.
    Returns structured analysis dict.
    """
    prompt = build_analysis_prompt(scraped)

    logger.info(f"Sending analysis request for: {scraped.get('url')}")

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=3000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = response.content[0].text.strip()

    # Clean potential markdown fences
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

    # Inject website URL
    analysis["website_url"] = scraped.get("url", "")

    return analysis
