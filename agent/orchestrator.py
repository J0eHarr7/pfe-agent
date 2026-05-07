"""
PFE Report Orchestrator — Full generation pipeline.
"""

import asyncio, json, logging, io, zipfile
from typing import Any, Callable
from agent.llm_client import LLMClient
from agent.context_store import ContextStore
from agent.latex_builder import LaTeXBuilder
from agent.mcp_client import MCPClient
from agent.doc_extractor import DocExtractor
from agent.sections import SECTION_REGISTRY

logger = logging.getLogger(__name__)


class PFEOrchestrator:
    def __init__(self, context: dict, log_callback: Callable = None):
        self.ctx   = ContextStore(context)
        self.llm   = LLMClient()
        self.latex = LaTeXBuilder()
        self.mcp   = MCPClient()
        self.extractor = DocExtractor()
        self.sections: dict[str, str] = {}
        self._log = log_callback or logger.info

    async def extract_from_docs(self, docs: list[dict]) -> dict:
        self._log("📖 Analyse des documents de stage en cours...")
        result = await self.extractor.extract_from_docs(docs)
        ntechs = len(result.get("technologies", []))
        ntasks = len(result.get("tasks", []))
        nmods  = len(result.get("modules", []))
        self._log(f"✅ Extraction : {ntechs} technologies | {ntasks} tâches | {nmods} modules")
        return result

    async def run(self) -> dict[str, Any]:
        self._log("🚀 Démarrage génération rapport PFA")

        # Propagate tasks & modules to context for Gantt and chapter 5
        extracted = self.ctx.get("extracted_info", {})
        if extracted.get("tasks") and not self.ctx.get("tasks"):
            self.ctx.update("tasks", extracted["tasks"])
        if extracted.get("modules") and not self.ctx.get("modules"):
            self.ctx.update("modules", extracted["modules"])
        if extracted.get("keywords_fr"):
            self.ctx.update("keywords_fr", extracted["keywords_fr"])
        if extracted.get("keywords_en"):
            self.ctx.update("keywords_en", extracted["keywords_en"])

        await self._generate_all_sections()

        self._log("🔧 Assemblage du projet LaTeX...")
        project_files = self.latex.build_project(self.sections, self.ctx)
        self._log(f"📁 {len(project_files)} fichiers LaTeX générés")

        self._log("📦 Création de l'archive ZIP...")
        zip_bytes = self._build_zip(project_files)

        # Try MCP compile (best-effort)
        compile_result = {"status": "skipped"}
        try:
            single_tex = self.latex.build(self.sections, self.ctx)
            compile_result = await self.mcp.compile(single_tex, project_files=project_files)
        except Exception as e:
            self._log(f"⚠️  Compilation MCP ignorée : {e}")

        self._log(f"✅ Terminé — compilation: {compile_result['status']}")
        return {
            "status": compile_result["status"],
            "pdf_url": compile_result.get("pdf_url"),
            "zip_bytes": zip_bytes,
            "project_files": list(project_files.keys()),
            "sections": self.sections,
        }

    async def _generate_all_sections(self):
        for key, cfg in SECTION_REGISTRY.items():
            self._log(f"📝 {cfg['title']}...")
            content = await self.llm.generate_section(
                section_key=key,
                section_cfg=cfg,
                context=self.ctx.snapshot(),
                previous_sections=self.sections,
            )
            self.sections[key] = content
            self._log(f"   ✓ {cfg['title']} ({len(content)} car.)")

    def _build_zip(self, files: dict[str, str]) -> bytes:
        buf = io.BytesIO()
        root = "rapport_pfe/"
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            for path, content in files.items():
                zf.writestr(root + path, content.encode("utf-8"))
            zf.writestr(root + "README.md", _README)
        buf.seek(0)
        return buf.read()


_README = """# Rapport PFA — Projet LaTeX Overleaf

## Structure
```
rapport_pfe/
├── main.tex              ← Document principal (compiler celui-ci)
├── title.tex             ← Page de garde
├── References.bib        ← Bibliographie BibTeX
├── Chapters/
│   ├── Remerciement.tex
│   ├── Résumé.tex
│   ├── Abstract.tex
│   ├── ResumeArabe.tex
│   ├── Introduction.tex
│   ├── CH1.tex  ←  page titre Chapitre 1
│   ├── Chapitre1.tex  ←  contenu
│   ├── CH2.tex  /  Chapitre2.tex
│   ├── CH3.tex  /  Chapitre3.tex
│   ├── CH4.tex  /  Chapitre4.tex
│   ├── CH5.tex  /  Chapitre5.tex
│   ├── Conclusion.tex
│   ├── Perspectives.tex
│   └── References.tex
├── logo/
│   ├── Logo_ENSA.jpg        ← À ajouter manuellement
│   └── logo_company.jpg     ← Logo entreprise
└── screens/                 ← Captures d'écran / figures
```

## Import dans Overleaf
1. New Project → Upload Project → sélectionner ce ZIP
2. Définir **main.tex** comme document principal
3. Ajouter les images dans logo/ et screens/
4. Compiler avec **pdfLaTeX** (ou XeLaTeX pour l'arabe)

## Compilation locale
```bash
pdflatex main.tex
biber main
pdflatex main.tex
pdflatex main.tex
```
"""