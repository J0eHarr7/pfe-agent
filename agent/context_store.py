"""
Context Store — Holds all PFE project data in one place.
Acts as the single source of truth for all generation prompts.
"""

from dataclasses import dataclass, field, asdict
from typing import Any


@dataclass
class PFEContext:
    # ── Identification ──────────────────────────────────────────────
    student_name: str = ""
    student_email: str = ""
    supervisor_name: str = ""
    jury_members: list[str] = field(default_factory=list)
    academic_year: str = "2025-2026"
    school_name: str = "École Nationale des Sciences Appliquées de Marrakech"

    # ── Project ─────────────────────────────────────────────────────
    project_title: str = ""
    project_title_en: str = ""
    project_title_ar: str = ""
    company_name: str = ""
    company_description: str = ""
    company_sector: str = ""
    project_description: str = ""
    problematique: str = ""

    # ── Technical ───────────────────────────────────────────────────
    technologies: list[str] = field(default_factory=list)
    architecture_description: str = ""
    diagrams: list[dict] = field(default_factory=list)   # [{name, description, type}]
    results: list[dict] = field(default_factory=list)     # [{metric, value, comment}]
    figures: list[dict] = field(default_factory=list)     # [{caption, filename}]
    references: list[dict] = field(default_factory=list)  # [{author, title, year, type, extra}]

    # ── Optional flags ──────────────────────────────────────────────
    dedicaces_enabled: bool = True
    annexes_enabled: bool = False
    annexes_content: str = ""


class ContextStore:
    def __init__(self, raw: dict):
        # Support either a PFEContext dict or a raw dict
        if isinstance(raw, PFEContext):
            self._data = asdict(raw)
        else:
            self._data = raw

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    def snapshot(self) -> dict:
        """Return a clean copy of all context data."""
        return dict(self._data)

    def update(self, key: str, value: Any):
        self._data[key] = value
