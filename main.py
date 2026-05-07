"""
FastAPI entrypoint for the PFE Agent service.
New endpoints:
  POST /extract-docs         — Extract info from uploaded documents
  POST /generate             — Full generation (with confirmed techs + logos)
  GET  /jobs/{id}            — Poll job status
  GET  /jobs/{id}/zip        — Download ZIP of LaTeX project
  GET  /jobs/{id}/tex        — Get single .tex (for MCP compile preview)
"""

import logging
import base64
import uuid
import asyncio
import io
from typing import Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel

from agent.orchestrator import PFEOrchestrator
from agent.doc_extractor import DocExtractor

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="PFE Report AI Agent", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory stores
jobs: dict[str, dict] = {}
extracted_cache: dict[str, dict] = {}  # session_id -> extracted info


# ── Models ────────────────────────────────────────────────────────────────────
class TechConfirmation(BaseModel):
    name: str
    version: Optional[str] = None
    category: str
    description: str
    justification: str
    logo_filename: Optional[str] = None  # filename in images/ folder


class GenerateRequest(BaseModel):
    # Identification
    student_name: str
    students: Optional[list[str]] = None
    supervisor_company: str
    supervisor_school: str
    academic_year: Optional[str] = "2024 - 2025"
    school_name: Optional[str] = "École Nationale des Sciences Appliquées de Marrakech"
    filiere: Optional[str] = "Génie Informatique"
    date_debut: Optional[str] = "01/07/2024"
    date_fin: Optional[str] = "31/08/2024"

    # Project
    project_title: str
    project_title_en: Optional[str] = ""
    company_name: str
    company_description: Optional[str] = ""
    company_sector: Optional[str] = ""
    project_description: str
    problematique: str

    # Content
    remerciements: Optional[str] = ""
    dedicaces: Optional[list[str]] = None
    references: Optional[list[dict]] = []

    # Confirmed technologies (from step 4 confirmation)
    confirmed_technologies: Optional[list[dict]] = []

    # Extracted info from docs (from /extract-docs)
    extracted_info: Optional[dict] = {}

    # Modules from extraction
    modules: Optional[list[dict]] = []

    # Optional
    annexes_content: Optional[str] = ""
    company_logo_filename: Optional[str] = "logo_company.png"


# ── Health ────────────────────────────────────────────────────────────────────
@app.get("/health")
async def health():
    return {"status": "ok", "service": "pfe-agent", "version": "2.0.0"}


# ── Extract docs endpoint ─────────────────────────────────────────────────────
@app.post("/extract-docs")
async def extract_docs(files: list[UploadFile] = File(...)):
    """
    Upload documentation files (PDF, DOCX, TXT, MD).
    Returns extracted: technologies, tasks, modules, methodology, etc.
    """
    extractor = DocExtractor()
    docs = []

    for f in files:
        raw = await f.read()
        # Try UTF-8 decode (works for txt/md), fallback for PDF text extraction
        try:
            text = raw.decode("utf-8", errors="replace")
        except Exception:
            text = raw.decode("latin-1", errors="replace")

        # Basic PDF text extraction (strip binary)
        if f.filename.lower().endswith(".pdf"):
            text = _extract_pdf_text(raw)
        elif f.filename.lower().endswith(".docx"):
            text = _extract_docx_text(raw)

        docs.append({"filename": f.filename, "text": text[:12000]})

    if not docs:
        raise HTTPException(status_code=400, detail="No valid documents uploaded")

    result = await extractor.extract_from_docs(docs)

    # Cache with session id
    session_id = str(uuid.uuid4())
    extracted_cache[session_id] = result
    result["session_id"] = session_id

    return result


# ── Generate endpoint ─────────────────────────────────────────────────────────
@app.post("/generate")
async def generate_report(req: GenerateRequest, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())
    jobs[job_id] = {
        "status": "pending",
        "progress": [],
        "result": None,
        "error": None,
    }
    background_tasks.add_task(_run_generation, job_id, req.model_dump())
    return {"job_id": job_id, "status": "pending"}


# ── Job polling ───────────────────────────────────────────────────────────────
@app.get("/jobs/{job_id}")
async def get_job(job_id: str):
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    # Don't return raw zip bytes in status poll
    safe = {k: v for k, v in job.items() if k != "zip_bytes"}
    return safe


# ── Download ZIP ──────────────────────────────────────────────────────────────
@app.get("/jobs/{job_id}/zip")
async def download_zip(job_id: str):
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job["status"] != "done":
        raise HTTPException(status_code=425, detail="Job not finished yet")

    zip_bytes = job.get("zip_bytes")
    if not zip_bytes:
        raise HTTPException(status_code=404, detail="ZIP not available")

    return StreamingResponse(
        io.BytesIO(zip_bytes),
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename=rapport_pfe_{job_id[:8]}.zip"},
    )


# ── Download single .tex ──────────────────────────────────────────────────────
@app.get("/jobs/{job_id}/tex")
async def get_tex(job_id: str):
    job = jobs.get(job_id)
    if not job or job["status"] != "done":
        raise HTTPException(status_code=404, detail="Not ready")
    result = job.get("result", {})
    return {"tex": result.get("tex", "")}


# ── Background task ───────────────────────────────────────────────────────────
async def _run_generation(job_id: str, context: dict):
    def log(msg: str):
        jobs[job_id]["progress"].append(msg)
        logger.info(f"[{job_id[:8]}] {msg}")

    try:
        jobs[job_id]["status"] = "running"
        log("🚀 Démarrage de la génération du rapport PFE")
        log(f"📋 Projet : {context.get('project_title', '—')}")
        log(f"🏢 Entreprise : {context.get('company_name', '—')}")
        log(f"⚙️  Technologies confirmées : {len(context.get('confirmed_technologies', []))}")
        log(f"📦 Modules identifiés : {len(context.get('modules', []))}")

        orchestrator = PFEOrchestrator(context, log_callback=log)
        result = await orchestrator.run()

        jobs[job_id]["status"] = "done"
        jobs[job_id]["zip_bytes"] = result.get("zip_bytes")
        jobs[job_id]["result"] = {
            "status": result["status"],
            "pdf_url": result.get("pdf_url"),
            "project_files": result.get("project_files", []),
            "sections_count": len(result.get("sections", {})),
        }
        log(f"✅ Rapport complet — {len(result.get('project_files', []))} fichiers LaTeX")
        log("📥 Archive ZIP prête au téléchargement")

    except Exception as e:
        logger.exception(f"Job {job_id} failed")
        jobs[job_id]["status"] = "error"
        jobs[job_id]["error"] = str(e)


# ── PDF text extraction (basic) ───────────────────────────────────────────────
def _extract_pdf_text(raw: bytes) -> str:
    """Very basic PDF text extraction by looking for BT/ET text blocks."""
    try:
        import re
        text = raw.decode("latin-1", errors="replace")
        # Extract text between BT and ET markers
        matches = re.findall(r'\(([^)]{2,})\)', text)
        readable = " ".join(m for m in matches if all(32 <= ord(c) < 127 for c in m))
        if len(readable) > 200:
            return readable[:12000]
        # Fallback: just strip binary chars
        return re.sub(r'[^\x20-\x7E\n\r\t]', ' ', text)[:12000]
    except Exception:
        return ""


# ── Override PDF extraction with pypdf ────────────────────────────────────────
def _extract_pdf_text(raw: bytes) -> str:
    """Extract text from PDF bytes using pypdf."""
    try:
        import io as _io
        from pypdf import PdfReader
        reader = PdfReader(_io.BytesIO(raw))
        pages_text = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                pages_text.append(text)
        full = "\n\n".join(pages_text)
        return full[:14000]
    except Exception as e:
        logger.warning(f"pypdf failed: {e}, using fallback")
        import re
        text = raw.decode("latin-1", errors="replace")
        return re.sub(r'[^\x20-\x7E\n\r\t]', ' ', text)[:12000]


def _extract_docx_text(raw: bytes) -> str:
    """Extract text from DOCX bytes using python-docx."""
    try:
        import io as _io
        from docx import Document

        document = Document(_io.BytesIO(raw))
        paragraphs = [paragraph.text for paragraph in document.paragraphs if paragraph.text]
        return "\n".join(paragraphs)[:14000]
    except Exception as e:
        logger.warning(f"python-docx failed: {e}")
        return ""
