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

        # Compile LaTeX with automatic error fixing
        self._log("🔨 Compilation LaTeX avec correction automatique...")
        single_tex = self.latex.build(self.sections, self.ctx)
        compile_result = await self._compile_with_auto_fix(single_tex, project_files)

        if compile_result["status"] != "success":
            self._log("❌ Compilation échouée après tentatives de correction")
            return {
                "status": "error",
                "message": "Compilation LaTeX échouée. Veuillez vérifier les erreurs et réessayer.",
                "errors": compile_result.get("errors", []),
                "pdf_url": None,
                "zip_bytes": None,
            }

        self._log("📦 Création de l'archive ZIP...")
        zip_bytes = self._build_zip(project_files)

        self._log("✅ Terminé — compilation réussie avec PDF généré")
        return {
            "status": "success",
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

    async def _compile_with_auto_fix(self, tex: str, project_files: dict, max_attempts: int = 3) -> dict[str, Any]:
        """Compile LaTeX with automatic error fixing."""
        current_tex = tex
        
        for attempt in range(max_attempts):
            self._log(f"🔨 Tentative de compilation {attempt + 1}/{max_attempts}...")
            
            try:
                result = await self.mcp.compile(current_tex, project_files=project_files)
                
                if result["status"] == "success":
                    self._log(f"✅ Compilation réussie à la tentative {attempt + 1}")
                    return result
                
                # Compilation failed with errors
                errors = result.get("errors", [])
                if not errors or attempt == max_attempts - 1:
                    self._log(f"❌ Compilation échouée après {attempt + 1} tentatives")
                    return result
                
                self._log(f"⚠️  {len(errors)} erreurs détectées, tentative de correction automatique...")
                current_tex = await self.llm.fix_latex(current_tex, errors)
                
                # Update main.tex in project_files with fixed content
                if "main.tex" in project_files:
                    project_files["main.tex"] = current_tex
                
            except Exception as e:
                self._log(f"❌ Erreur lors de la compilation : {e}")
                if attempt == max_attempts - 1:
                    return {
                        "status": "error",
                        "errors": [str(e)],
                        "pdf_url": None,
                    }
        
        return {
            "status": "error",
            "errors": ["Maximum compilation attempts reached"],
            "pdf_url": None,
        }


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