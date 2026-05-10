"""
MCP Server — Overleaf Tool
Exposes MCP-compatible tools:
  - write_tex_file: Save .tex content to disk
  - compile_latex: Run pdflatex, return errors or PDF path
  - list_files: List project files
"""

import os
import json
import logging
import asyncio
import shutil
import re
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
import aiofiles

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="MCP Overleaf Server", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

WORKSPACE = Path(os.getenv("WORKSPACE_DIR", "/workspace"))
WORKSPACE.mkdir(parents=True, exist_ok=True)
TITLE_INPUT = "\\input{title}"
TITLE_INPUT_ALT = "\\input{./title}"
UNKNOWN_COMPILATION_ERROR = "Unknown compilation error"

TOOLS = [
    {
        "name": "write_tex_file",
        "description": "Write LaTeX content to a .tex file in the workspace",
        "inputSchema": {
            "type": "object",
            "properties": {
                "filename": {"type": "string", "description": "Filename (e.g. rapport_pfe.tex)"},
                "content": {"type": "string", "description": "Full LaTeX source content"},
            },
            "required": ["filename", "content"],
        },
    },
    {
        "name": "compile_latex",
        "description": "Compile a .tex file with pdflatex. Returns success/errors.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "filename": {"type": "string", "description": ".tex filename to compile"},
                "passes": {"type": "integer", "description": "Number of compilation passes (default 2)", "default": 2},
            },
            "required": ["filename"],
        },
    },
    {
        "name": "list_files",
        "description": "List files in the workspace",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "read_log",
        "description": "Read the LaTeX compilation log",
        "inputSchema": {
            "type": "object",
            "properties": {
                "filename": {"type": "string", "description": "Log filename"},
            },
            "required": ["filename"],
        },
    },
    {
        "name": "read_tex_file",
        "description": "Read a LaTeX source file from the workspace",
        "inputSchema": {
            "type": "object",
            "properties": {
                "filename": {"type": "string", "description": ".tex filename to inspect"},
            },
            "required": ["filename"],
        },
    },
    {
        "name": "debug_latex",
        "description": "Inspect a LaTeX file and its compilation log, then return diagnostics and likely fixes",
        "inputSchema": {
            "type": "object",
            "properties": {
                "filename": {"type": "string", "description": ".tex filename to inspect"},
            },
            "required": ["filename"],
        },
    },
]


@app.get("/health")
async def health():
    return {"status": "ok", "service": "mcp-server"}


@app.post("/mcp")
async def mcp_endpoint(request: Request):
    """Main MCP JSON-RPC endpoint."""
    body = await request.json()
    method = body.get("method")
    params = body.get("params", {})
    req_id = body.get("id", 1)

    if method == "initialize":
        return _rpc_response(req_id, {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "overleaf-mcp", "version": "1.0.0"},
        })

    if method == "tools/list":
        return _rpc_response(req_id, {"tools": TOOLS})

    if method == "tools/call":
        tool_name = params.get("name")
        args = params.get("arguments", {})
        result = await _dispatch_tool(tool_name, args)
        return _rpc_response(req_id, {
            "content": [{"type": "text", "text": json.dumps(result)}]
        })

    return _rpc_error(req_id, -32601, f"Method not found: {method}")


@app.get("/pdf/{filename}")
async def serve_pdf(filename: str):
    """Serve compiled PDF files."""
    pdf_path = WORKSPACE/filename
    if not pdf_path.exists():
        return JSONResponse(status_code=404, content={"error": "PDF not found"})
    return FileResponse(pdf_path, media_type="application/pdf")


async def _dispatch_tool(tool_name: str, args: dict) -> dict:
    if tool_name == "write_tex_file":
        return await _write_tex_file(args["filename"], args["content"])
    elif tool_name == "compile_latex":
        return await _compile_latex(args["filename"], args.get("passes", 2))
    elif tool_name == "list_files":
        return _list_files()
    elif tool_name == "read_log":
        return await _read_log(args["filename"])
    elif tool_name == "read_tex_file":
        return await _read_tex_file(args["filename"])
    elif tool_name == "debug_latex":
        return await _debug_latex(args["filename"])
    else:
        return {"error": f"Unknown tool: {tool_name}"}


async def _write_tex_file(filename: str, content: str) -> dict:
    """Write .tex content to workspace."""
    filepath = _safe_workspace_path(filename)
    filepath.parent.mkdir(parents=True, exist_ok=True)
    async with aiofiles.open(filepath, "w", encoding="utf-8") as f:
        await f.write(content)
    logger.info(f"Written: {filepath} ({len(content)} chars)")
    return {"success": True, "path": str(filepath), "size": len(content)}


async def _compile_latex(filename: str, passes: int = 2) -> dict:
    """Run pdflatex on the file, return result."""
    tex_path = _safe_workspace_path(filename)
    if not tex_path.exists():
        return {"success": False, "errors": [f"File not found: {filename}"]}

    stem = tex_path.stem
    pdf_path = WORKSPACE / f"{stem}.pdf"
    log_path = WORKSPACE / f"{stem}.log"

    errors = []
    for i in range(passes):
        logger.info(f"pdflatex pass {i+1}/{passes} for {tex_path.name}")
        proc = await _run_pdflatex(tex_path)
        if proc.get("timeout"):
            return {"success": False, "errors": ["Compilation timeout (120s)"]}
        if proc.get("missing_pdflatex"):
            return {"success": False, "errors": ["pdflatex not found — install texlive"]}

        log_text = _read_compile_log(log_path, proc["output"])
        errors = _parse_errors(log_text)
        if proc["returncode"] != 0 or errors:
            debug_info = await _debug_latex(tex_path.name)
            if debug_info.get("likely_fixes") and await _apply_likely_fixes(tex_path, debug_info["likely_fixes"]):
                logger.info(f"Applied fixes to {tex_path.name}; recompiling")

    if pdf_path.exists():
        pdf_url = f"/pdf/{stem}.pdf"
        logger.info(f"✅ PDF generated: {pdf_path}")
        return {
            "success": True,
            "pdf_path": str(pdf_path),
            "pdf_url": pdf_url,
            "warnings": errors,
        }
    else:
        logger.error(f"❌ Compilation failed. Errors: {errors}")
        debug_info = await _debug_latex(tex_path.name)
        return {"success": False, "errors": errors, "debug": debug_info}


def _parse_errors(log_output: str) -> list[str]:
    """Extract meaningful errors from pdflatex log."""
    errors = []
    for line in log_output.split("\n"):
        line = line.strip()
        if line.startswith("!") or "Error:" in line or "Undefined control sequence" in line:
            errors.append(line)
    return errors[:20]  # Limit to 20 errors


def _read_compile_log(log_path: Path, fallback_text: str = "") -> str:
    if log_path.exists():
        try:
            return log_path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            pass
    return fallback_text


async def _read_tex_file(filename: str) -> dict:
    tex_path = _safe_workspace_path(filename)
    if not tex_path.exists():
        return {"error": "File not found"}
    async with aiofiles.open(tex_path, "r", encoding="utf-8", errors="replace") as f:
        content = await f.read()
    return {"content": content}


async def _debug_latex(filename: str) -> dict:
    safe_name = Path(filename).name
    tex_path = _safe_workspace_path(filename)
    log_path = WORKSPACE / f"{tex_path.stem}.log"

    source = ""
    if tex_path.exists():
        async with aiofiles.open(tex_path, "r", encoding="utf-8", errors="replace") as f:
            source = await f.read()

    log_text = ""
    if log_path.exists():
        async with aiofiles.open(log_path, "r", encoding="utf-8", errors="replace") as f:
            log_text = await f.read()

    findings = []
    likely_fixes = []

    if f"File `{Path(TITLE_INPUT).name}.tex' not found" in log_text or f"File `{Path(TITLE_INPUT).name}.tex' not found" in source:
        findings.append("Missing title.tex reference in the workspace root.")
        likely_fixes.append("Ensure title.tex exists at the workspace root, not only inside a nested folder.")

    if re.search(r"File `([^`]+)' not found", log_text):
        missing = re.findall(r"File `([^`]+)' not found", log_text)
        for item in missing:
            findings.append(f"Missing file referenced by LaTeX: {item}")
            likely_fixes.append(f"Copy or generate {item} at the project root, or update the input path to match its location.")

    if "Undefined control sequence" in log_text:
        findings.append("Undefined control sequence detected.")
        likely_fixes.append("Check for unsupported macros or missing packages in main.tex.")

    if "Something's wrong--perhaps a missing \\item." in log_text or "missing \\item" in log_text.lower():
        findings.append("A LaTeX list appears malformed or empty.")
        likely_fixes.append("Remove empty itemize/enumerate blocks from generated LaTeX content.")

    if "Emergency stop" in log_text:
        findings.append("Compilation stopped due to a fatal LaTeX error.")

    return {
        "filename": safe_name,
        "findings": findings,
        "likely_fixes": likely_fixes,
        "log_tail": log_text[-4000:] if log_text else "",
        "source_head": source[:4000] if source else "",
    }


async def _apply_likely_fixes(tex_path: Path, fixes: list[str]) -> bool:
    """Apply only deterministic structural fixes that can be inferred safely."""
    if not tex_path.exists():
        return False

    updated = False

    # Make the ENSA logo optional in the generated title page.
    if any("Logo_ENSA.jpg" in fix for fix in fixes):
        title_path = WORKSPACE / "title.tex"
        if title_path.exists():
            async with aiofiles.open(title_path, "r", encoding="utf-8", errors="replace") as f:
                title_content = await f.read()
            if "\\IfFileExists{logo/Logo_ENSA.jpg}" not in title_content:
                title_content = title_content.replace(
                    "        \\includegraphics[width=4cm]{logo/Logo_ENSA.jpg}",
                    "        \\IfFileExists{logo/Logo_ENSA.jpg}{\\includegraphics[width=4cm]{logo/Logo_ENSA.jpg}}{}",
                )
                async with aiofiles.open(title_path, "w", encoding="utf-8") as f:
                    await f.write(title_content)
                updated = True

    if any("list" in fix.lower() for fix in fixes):
        for path in WORKSPACE.rglob("*.tex"):
            async with aiofiles.open(path, "r", encoding="utf-8", errors="replace") as f:
                content = await f.read()
            cleaned = _remove_empty_list_blocks(content)
            if cleaned != content:
                async with aiofiles.open(path, "w", encoding="utf-8") as f:
                    await f.write(cleaned)
                updated = True

    return updated


def _remove_empty_list_blocks(content: str) -> str:
    content = re.sub(r"\\begin\{itemize\}\s*\\end\{itemize\}", "", content, flags=re.DOTALL)
    content = re.sub(r"\\begin\{enumerate\}\s*\\end\{enumerate\}", "", content, flags=re.DOTALL)
    return content


async def _run_pdflatex(tex_path: Path) -> dict:
    try:
        proc = await asyncio.create_subprocess_exec(
            "pdflatex",
            "-interaction=nonstopmode",
            "-output-directory", str(WORKSPACE),
            str(tex_path),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(WORKSPACE),
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=120)
        output = (stdout or b"").decode("utf-8", errors="replace") + (stderr or b"").decode("utf-8", errors="replace")
        return {"returncode": proc.returncode, "output": output}
    except asyncio.TimeoutError:
        return {"timeout": True}
    except FileNotFoundError:
        return {"missing_pdflatex": True}


def _list_files() -> dict:
    files = [f.name for f in WORKSPACE.iterdir() if f.is_file()]
    return {"files": sorted(files)}


async def _read_log(filename: str) -> dict:
    log_path = WORKSPACE / Path(filename).name
    if not log_path.exists():
        return {"error": "Log not found"}
    async with aiofiles.open(log_path, "r", encoding="utf-8", errors="replace") as f:
        content = await f.read()
    return {"content": content[-5000:]}  # Last 5000 chars


def _rpc_response(req_id, result):
    return {"jsonrpc": "2.0", "id": req_id, "result": result}


def _rpc_error(req_id, code, message):
    return {"jsonrpc": "2.0", "id": req_id, "error": {"code": code, "message": message}}


def _safe_workspace_path(filename: str) -> Path:
    candidate = (WORKSPACE / Path(filename)).resolve()
    workspace_root = WORKSPACE.resolve()
    if workspace_root not in candidate.parents and candidate != workspace_root:
        raise ValueError(f"Invalid path outside workspace: {filename}")
    return candidate
