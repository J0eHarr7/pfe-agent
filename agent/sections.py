"""
Section Registry — Maps section keys to their metadata.
Order matters: sections are generated in this order.
Matches the structure of the example PFE report from ENSA Marrakech.
"""

from collections import OrderedDict

SECTION_REGISTRY = OrderedDict([
    ("resume_fr", {
        "title": "Résumé",
        "required": True,
        "max_pages": 1,
        "latex_chapter": False,
    }),
    ("resume_en", {
        "title": "Abstract",
        "required": True,
        "max_pages": 1,
        "latex_chapter": False,
    }),
    ("resume_ar", {
        "title": "ملخص",
        "required": True,
        "max_pages": 1,
        "latex_chapter": False,
    }),
    ("introduction_generale", {
        "title": "Introduction Générale",
        "required": True,
        "max_pages": 3,
        "latex_chapter": True,
        "numbered": False,
    }),
    ("chapitre1_contexte", {
        "title": "Contexte général du projet",
        "required": True,
        "max_pages": 10,
        "latex_chapter": True,
        "numbered": True,
        "chapter_number": 1,
        "sections": [
            "Présentation de l'organisme d'accueil",
            "Motivation et problématique",
            "Objectifs du projet",
            "Planification du projet",
        ]
    }),
    ("chapitre2_analyse", {
        "title": "Analyse et conception",
        "required": True,
        "max_pages": 12,
        "latex_chapter": True,
        "numbered": True,
        "chapter_number": 2,
        "sections": [
            "Analyse des besoins fonctionnels",
            "Analyse des besoins non fonctionnels",
            "Modélisation conceptuelle",
            "Architecture en couches",
        ]
    }),
    ("chapitre3_etat_art", {
        "title": "État de l'art : Fondements théoriques",
        "required": True,
        "max_pages": 15,
        "latex_chapter": True,
        "numbered": True,
        "chapter_number": 3,
        "sections": [
            "Fondements théoriques du domaine",
            "Méthodologies et approches",
            "Comparaison des solutions existantes",
        ]
    }),
    ("chapitre4_outils", {
        "title": "Outils et Technologies",
        "required": True,
        "max_pages": 12,
        "latex_chapter": True,
        "numbered": True,
        "chapter_number": 4,
        "sections": [
            "Description et justification des technologies utilisées",
            "Architecture technologique globale",
            "Considérations de déploiement",
        ]
    }),
    ("chapitre5_realisation", {
        "title": "Conception et implémentation pratique",
        "required": True,
        "max_pages": 20,
        "latex_chapter": True,
        "numbered": True,
        "chapter_number": 5,
        "sections": [
            "Architecture globale du projet",
            "Implémentation des modules",
            "Tests et résultats",
        ]
    }),
    ("conclusion_generale", {
        "title": "Conclusion Générale",
        "required": True,
        "max_pages": 2,
        "latex_chapter": True,
        "numbered": False,
    }),
    ("perspectives", {
        "title": "Perspectives",
        "required": True,
        "max_pages": 1,
        "latex_chapter": True,
        "numbered": False,
    }),
    ("glossaire", {
        "title": "Liste des abréviations",
        "required": True,
        "max_pages": 2,
        "latex_chapter": False,
    }),
])