"""
main.py
FastAPI backend for the AI Quick Scan lead funnel.
Hosted separately, called by the Elementor widget on obtained.eu
"""

import os
import uuid
import logging
import asyncio
from pathlib import Path
from typing import Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from website_scraper import scrape_website
from ai_analyzer import analyze_website
from pdf_generator import generate_pdf
from email_sender import send_report

# ─── Setup ────────────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", "/tmp/ai-scan-reports"))
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(
    title="Obtained.eu AI Quick Scan API",
    version="1.0.0",
    description="Scrapes a B2B website, generates AI opportunities, emails a PDF report.",
)

# Allow obtained.eu + localhost for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://obtained.eu",
        "https://www.obtained.eu",
        "http://localhost",
        "http://localhost:3000",
        "http://127.0.0.1",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# ─── In-memory job tracking ───────────────────────────────────────────────────
jobs: dict[str, dict] = {}


# ─── Request/Response models ─────────────────────────────────────────────────
class ScanRequest(BaseModel):
    website_url: str
    email: str
    company_name: Optional[str] = None


class ScanResponse(BaseModel):
    job_id: str
    status: str
    message: str


class JobStatus(BaseModel):
    job_id: str
    status: str
    message: str
    created_at: str
    completed_at: Optional[str] = None
    error: Optional[str] = None


# ─── Background job ───────────────────────────────────────────────────────────
async def run_scan_job(job_id: str, website_url: str, email: str, company_name: Optional[str]):
    """Full pipeline: scrape → analyze → generate PDF → send email."""
    try:
        # 1. Scrape
        jobs[job_id]["status"] = "scraping"
        jobs[job_id]["message"] = "Website wordt gescand..."
        logger.info(f"[{job_id}] Scraping {website_url}")
        scraped = await asyncio.to_thread(scrape_website, website_url)

        # 2. Analyze
        jobs[job_id]["status"] = "analyzing"
        jobs[job_id]["message"] = "AI analyseert de kansen..."
        logger.info(f"[{job_id}] Analyzing with AI")
        analysis = await asyncio.to_thread(analyze_website, scraped)

        # Override company name if provided manually
        if company_name:
            analysis["company_name"] = company_name

        # 3. Generate PDF
        jobs[job_id]["status"] = "generating"
        jobs[job_id]["message"] = "Rapport wordt aangemaakt..."
        pdf_path = str(OUTPUT_DIR / f"scan_{job_id}.pdf")
        logger.info(f"[{job_id}] Generating PDF")
        await asyncio.to_thread(generate_pdf, analysis, pdf_path)

        # 4. Send email
        jobs[job_id]["status"] = "sending"
        jobs[job_id]["message"] = "Rapport wordt verstuurd..."
        logger.info(f"[{job_id}] Sending email to {email}")
        await asyncio.to_thread(send_report, email, analysis, pdf_path)

        # 5. Done
        jobs[job_id]["status"] = "done"
        jobs[job_id]["message"] = "Rapport verstuurd! Check je inbox."
        jobs[job_id]["completed_at"] = datetime.utcnow().isoformat()
        logger.info(f"[{job_id}] Done")

    except Exception as e:
        logger.error(f"[{job_id}] Error: {e}", exc_info=True)
        jobs[job_id]["status"] = "error"
        jobs[job_id]["message"] = "Er is iets misgegaan. Probeer het opnieuw."
        jobs[job_id]["error"] = str(e)
        jobs[job_id]["completed_at"] = datetime.utcnow().isoformat()


# ─── Endpoints ────────────────────────────────────────────────────────────────
@app.get("/health")
def health():
    return {"status": "ok", "service": "AI Quick Scan API"}


@app.post("/scan", response_model=ScanResponse)
async def start_scan(req: ScanRequest, background_tasks: BackgroundTasks):
    """Start an AI Quick Scan job."""
    url = req.website_url.strip()
    if not url.startswith("http"):
        url = "https://" + url

    job_id = str(uuid.uuid4())[:8]
    jobs[job_id] = {
        "job_id": job_id,
        "status": "pending",
        "message": "Scan gestart...",
        "created_at": datetime.utcnow().isoformat(),
        "completed_at": None,
        "error": None,
    }

    background_tasks.add_task(
        run_scan_job, job_id, url, req.email, req.company_name
    )

    return ScanResponse(
        job_id=job_id,
        status="pending",
        message="Scan gestart! Je ontvangt het rapport binnen 2-3 minuten.",
    )


@app.get("/scan/{job_id}", response_model=JobStatus)
def get_job_status(job_id: str):
    """Poll the status of a scan job."""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job niet gevonden")
    return JobStatus(**jobs[job_id])


@app.get("/")
def root():
    return {
        "service": "Obtained.eu AI Quick Scan",
        "docs": "/docs",
        "health": "/health",
    }
