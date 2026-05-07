"""
Document Extractor — Extracts tasks, technologies, modules from internship docs.
Also builds duration estimates for Gantt diagram.
"""

import json, logging, httpx, os

logger = logging.getLogger(__name__)


class DocExtractor:
    def __init__(self):
        self.api_key  = os.getenv("OPENAI_API_KEY", "")
        self.base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
        self.model    = os.getenv("LLM_MODEL", "gpt-4o")

    async def extract_from_docs(self, docs: list[dict]) -> dict:
        combined = "\n\n---\n\n".join(
            f"=== FICHIER: {d['filename']} ===\n{d['text'][:8000]}"
            for d in docs
        )
        prompt = f"""Analyse ces documents de stage et extrais TOUTES les informations structurées.
Réponds UNIQUEMENT avec un objet JSON valide, sans markdown, sans backticks, sans texte avant ou après.

JSON attendu :
{{
  "technologies": [
    {{
      "name": "Nom exact",
      "version": "version ou null",
      "category": "langage|framework|outil|base_de_données|cloud|sécurité|devops|autre",
      "description": "description technique 1-2 phrases",
      "justification": "raison du choix dans ce projet spécifique"
    }}
  ],
  "tasks": [
    {{
      "title": "Titre court de la tâche (max 35 caractères)",
      "description": "Description complète de ce qui a été fait",
      "tools_used": ["outil1", "outil2"],
      "deliverable": "livrable produit",
      "duration_weeks": 1
    }}
  ],
  "modules": [
    {{
      "name": "Nom du module",
      "objective": "objectif précis",
      "implementation": "comment il a été implémenté (technique)",
      "technologies": ["tech1", "tech2"],
      "results": "résultats mesurables ou qualitatifs"
    }}
  ],
  "methodology": "Méthodologie globale adoptée (Agile, Scrum, DevSecOps, etc.)",
  "architecture": "Description de l'architecture technique (couches, composants, flux)",
  "problematique": "Problématique centrale identifiée",
  "company_info": {{
    "name": "nom",
    "sector": "secteur",
    "description": "description 2-3 phrases"
  }},
  "results": [
    {{"metric": "nom", "value": "valeur", "comment": "contexte"}}
  ],
  "keywords_fr": ["mot1", "mot2", "mot3", "mot4", "mot5"],
  "keywords_en": ["word1", "word2", "word3", "word4", "word5"],
  "acronyms": ["API", "CI/CD", "OWASP"],
  "raw_summary": "Résumé global du stage en 3-4 phrases"
}}

DOCUMENTS :
{combined}"""

        raw = await self._call(prompt)
        parsed = self._parse_json_response(raw)
        if parsed is not None:
            return parsed

        repaired = await self._repair_json(raw)
        if repaired is not None:
            return repaired

        return {
            "error": "Unable to parse extractor JSON response",
            "technologies": [],
            "tasks": [],
            "modules": [],
            "keywords_fr": [],
            "keywords_en": [],
            "acronyms": [],
            "raw_summary": raw[:300],
        }

    async def _call(self, prompt: str) -> str:
        url     = f"{self.base_url}/chat/completions"
        headers = {"Content-Type":"application/json","Authorization":f"Bearer {self.api_key}"}
        payload = {
            "model": self.model,
            "messages": [{"role":"user","content":prompt}],
            "temperature": 0.1,
            "max_tokens": 8000,
        }
        async with httpx.AsyncClient(timeout=180.0) as client:
            resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"].strip()

    def _parse_json_response(self, raw: str) -> dict | None:
        clean = raw.strip()
        if clean.startswith("```"):
            parts = clean.split("```")
            if len(parts) >= 2:
                clean = parts[1].strip()
                if clean.startswith("json"):
                    clean = clean[4:].lstrip()

        start = clean.find("{")
        end = clean.rfind("}")
        if start != -1 and end != -1 and end > start:
            clean = clean[start:end + 1]

        try:
            return json.loads(clean)
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {e}")
            return None

    async def _repair_json(self, raw: str) -> dict | None:
        repair_prompt = f"""Réécris le contenu ci-dessous en JSON valide strict uniquement.
Ne conserve aucun texte hors JSON.
Ne change pas la structure logique, corrige seulement la syntaxe.

CONTENU À CORRIGER :
{raw}"""

        repaired_raw = await self._call(repair_prompt)
        return self._parse_json_response(repaired_raw)