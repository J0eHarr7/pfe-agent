"""
LLM Client — Highly specific prompts per PFA chapter.
Output is ALWAYS plain academic French prose — NO markdown.
"""

import os, json, logging, httpx

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """Tu es un expert en rédaction de rapports académiques de Projet de Fin d'Études (PFE)
pour des élèves ingénieurs de l'ENSA Marrakech (filière Génie Informatique / Cyber-Défense).

RÈGLES ABSOLUES — respecte-les sans exception :

1. LANGUE : français académique uniquement, phrases complètes, style soutenu.
2. FORMAT : prose pure — ZÉRO markdown. N'utilise JAMAIS :
   - les symboles ## ### **texte** *texte* - liste ou 1. 2. 3.
   - les astérisques, dièses, tirets de liste
   Tu peux utiliser des listes LaTeX via \\begin{itemize}...\\end{itemize} si nécessaire.
3. INDENTATION : commence chaque paragraphe par \\hspace{10pt}
4. SECTIONS : utilise \\subsection{Titre} et \\subsubsection{Titre} pour structurer.
5. LONGUEUR : respecte le nombre de pages indiqué.
6. CONTENU : base-toi EXCLUSIVEMENT sur les données fournies — n'invente rien.
7. Ne commence JAMAIS ta réponse par une explication ou un titre général."""

# ─────────────────────────────────────────────────────────────────────────────
PROMPTS = {

"resume_fr": """Rédige le RÉSUMÉ EN FRANÇAIS du projet PFA. Longueur : environ 250 mots, 3 paragraphes.

Paragraphe 1 — Contexte et enjeux : situe le domaine, présente les défis actuels.
Paragraphe 2 — Description du projet et contributions : que fait la plateforme, quels modules, quelle approche.
Paragraphe 3 — Résultats et conclusion : ce qui a été accompli, impact.
Dernière ligne séparée : les 5-6 mots-clés (ne mets PAS "Mots-clés :" ici, cela sera ajouté automatiquement).

DONNÉES DU PROJET :
{context}""",

"resume_en": """Write the ENGLISH ABSTRACT for this internship project. Length: ~250 words, 3 paragraphs.

Paragraph 1 — Context and challenges: domain overview, current issues.
Paragraph 2 — Project and contributions: what the platform does, modules, approach.
Paragraph 3 — Results and conclusion: achievements, impact.
Last line: 5-6 keywords only (no "Keywords:" prefix).

PROJECT DATA:
{context}""",

"introduction_generale": """Rédige l'INTRODUCTION GÉNÉRALE du rapport PFA. Longueur : 2 à 3 pages (~600 mots).

Structure obligatoire en prose (sans titres de sections) :

Paragraphe 1 — Contexte global : présente le domaine technologique, les enjeux actuels pour les organisations, la tendance à la digitalisation et aux cybermenaces.

Paragraphe 2 — Problématique : amène progressivement les difficultés observées dans le secteur, les manques existants dans les solutions actuelles.

Paragraphe 3 — Présentation succincte : mentionne l'entreprise d'accueil en une phrase, puis présente le projet développé.

Paragraphe 4 — Organisation du rapport : décris en prose la structure du rapport (5 chapitres) sans énumérer mais en rédigeant des phrases de transition.

IMPORTANT : ne mentionne AUCUN résultat ni contribution — ceux-ci apparaissent dans la conclusion.

DONNÉES :
{context}""",

"chapitre1_contexte": """Rédige le CHAPITRE 1 complet du rapport PFA : "Contexte Général du Projet".
Longueur cible : 8 à 12 pages. Structure exacte en LaTeX (utilise \\subsection et \\subsubsection) :

\\subsection{Introduction}
Un paragraphe situant le chapitre, ce qu'il va présenter.

\\subsection{Présentation de l'établissement}
Présente l'ENSA Marrakech, son rattachement à l'Université Cadi Ayyad, sa mission de formation d'ingénieurs, son engagement dans l'innovation et la recherche appliquée.

\\subsection{Présentation de la filière}
Présente la filière indiquée dans les données, ses objectifs pédagogiques, ses domaines (sécurité, réseaux, systèmes embarqués), et son lien avec le projet.

\\subsection{Présentation de l'organisme d'accueil}
\\subsubsection{Présentation générale}
Présente l'entreprise : nom, secteur, mission principale, expertise, zone géographique d'intervention.
\\subsubsection{Les convictions et valeurs}
Valeurs de l'entreprise et son positionnement.
\\subsubsection{Les services proposés}
Ce que l'entreprise offre à ses clients.

\\subsection{Présentation du projet}
Description détaillée : nom du projet, objectif général, acteurs concernés, fonctionnalités principales sous forme de liste \\begin{itemize}...\\end{itemize}.

\\subsection{Problématique et enjeux}
Constat des problèmes existants. Formule la problématique centrale en italique via \\textit{...}. Pose 3 à 4 questions secondaires découlant de cette problématique.

\\subsection{Objectifs du projet}
Liste \\begin{itemize}...\\end{itemize} des objectifs généraux puis spécifiques (par module si applicable).

\\subsection{Méthodologie de gestion de projet}
\\subsubsection{Approche adoptée}
Décris la méthode (Agile/Scrum ou autre) et pourquoi elle a été choisie.
\\subsubsection{Organisation du travail}
Outils utilisés (Jira, GitHub, etc.), organisation des sprints.
\\subsubsection{Gestion du code source}
Utilisation de GitHub ou autre : versionnement, collaboration, branches.

\\subsection{Rôles et responsabilités}
Répartition Dev / Sec / Ops si DevSecOps, ou par modules.

\\subsection{Conclusion}
Récapitulatif du chapitre et transition vers le chapitre 2.

DONNÉES DE L'ENTREPRISE ET DU PROJET :
{context}

INFORMATIONS EXTRAITES DES DOCUMENTS DE STAGE :
{extracted_info}""",

"chapitre2_analyse": """Rédige le CHAPITRE 2 complet : "Analyse et Conception". Longueur : 10 à 14 pages.
Structure en LaTeX :

\\subsection{Introduction}
Rôle de l'analyse dans la réussite du projet.

\\subsection{Analyse des besoins}
\\subsubsection{Besoins fonctionnels}
Pour chaque module/composant du projet, décris les fonctionnalités attendues sous forme de liste.
\\subsubsection{Besoins non fonctionnels}
Organise en sous-parties : Sécurité, Performance, Maintenabilité, Conformité (RGPD/ISO si applicable), Portabilité, Utilisabilité.

\\subsection{Modélisation conceptuelle}
\\subsubsection{Architecture en couches}
Décris l'architecture (présentation / logique métier / services / données).
\\subsubsection{Diagrammes}
Décris textuellement les diagrammes de cas d'utilisation, de séquence, de classes ou d'architecture. Exemple : "Le diagramme de cas d'utilisation (Figure X) illustre...". Utilise \\begin{figure}[H]\\centering\\includegraphics[width=0.75\\linewidth]{screens/nom_figure.png}\\caption{Légende}\\end{figure}

\\subsection{Architecture système globale}
Description de l'architecture microservices/monolithique, API REST, base de données.

\\subsection{Conclusion}
Résumé et transition vers le chapitre 3.

DONNÉES :
{context}

INFORMATIONS EXTRAITES DES DOCUMENTS :
{extracted_info}""",

"chapitre3_etat_art": """Rédige le CHAPITRE 3 complet : "État de l'Art : Fondements Théoriques". Longueur : 12 à 16 pages.

C'est la revue de littérature académique du projet. Structure :

\\subsection{Introduction}
Objectif du chapitre, méthode de recherche.

Pour chaque domaine technologique du projet, crée une \\subsection avec :
- Définition et concepts fondamentaux
- Taxonomie / classification
- Standards et référentiels (OWASP, ISO 27001, RGPD, etc. selon le domaine)
- Cycle de vie / processus associé
- Comparaison des approches existantes

Domaines à couvrir obligatoirement selon les technologies identifiées :
{tech_domains}

\\subsection{Synthèse et positionnement du projet}
Comment les concepts théoriques justifient les choix du projet.

\\subsection{Conclusion}
Transition vers le chapitre des outils.

DONNÉES ET TECHNOLOGIES :
{context}

INFORMATIONS EXTRAITES :
{extracted_info}""",

"chapitre4_outils": """Rédige le CHAPITRE 4 complet : "Outils et Technologies". Longueur : 10 à 14 pages.

Structure LaTeX obligatoire :

\\subsection{Introduction}
Critères de sélection des technologies : adéquation fonctionnelle, maturité, performance, coût, communauté, standards.

\\subsection{Description et justification des technologies utilisées}
Pour CHAQUE technologie de la liste ci-dessous, rédige une \\subsubsection{{Nom de la technologie}} avec :
- \\textbf{{Description :}} qu'est-ce que c'est, qui l'a créé, dans quel contexte, quel est son rôle.
- \\textbf{{Justification du choix :}} pourquoi cette technologie pour CE projet spécifiquement (liste \\begin{{itemize}}).
- \\textbf{{Rôle dans le projet :}} comment elle est utilisée concrètement.

Technologies à documenter (une subsubsection par technologie) :
{technologies_list}

\\subsection{Architecture technologique globale}
Comment ces technologies s'articulent en couches cohérentes (couche présentation / application / services / données).

\\subsection{Considérations de déploiement}
Portabilité, configuration, monitoring, sécurité des dépendances.

\\subsection{Conclusion}
Cohérence du stack technologique et transition vers l'implémentation.

DONNÉES :
{context}

INFORMATIONS EXTRAITES :
{extracted_info}""",

"chapitre5_realisation": """Rédige le CHAPITRE 5 complet : "Conception et Implémentation Pratique". Longueur : 15 à 20 pages.

C'est le cœur technique du rapport. Base-toi PRINCIPALEMENT sur les documents de stage.
Structure LaTeX :

\\subsection{Introduction}
Présente ce chapitre comme la traduction des besoins en réalisations concrètes.

\\subsection{Architecture globale du projet}
\\subsubsection{Vision d'ensemble et principes architecturaux}
Principes : modularité, API-first, séparation des préoccupations, stateless, etc.
\\subsubsection{Architecture en couches détaillée}
Décris chaque couche avec ses composants (client, application, logique métier, services externes, données).

\\subsection{Implémentation des modules}
Pour CHAQUE module/composant réalisé pendant le stage (issue des documents), rédige une \\subsubsection :
- \\textbf{{Objectif et périmètre :}} ce que fait le module.
- \\textbf{{Architecture interne :}} comment il est structuré.
- \\textbf{{Implémentation :}} détails techniques clés (sans code source confidentiel).
- \\textbf{{Workflow :}} flux de traitement pas à pas.
- Références aux figures : "Comme illustré en Figure X..." avec placeholders \\begin{{figure}}[H]...\\end{{figure}}.

Modules à documenter :
{modules_info}

\\subsection{Intégration et tests}
\\subsubsection{Stratégie d'intégration}
Comment les modules communiquent (API REST, événements, queues).
\\subsubsection{Tests réalisés}
Types de tests (unitaires, intégration, sécurité), outils utilisés, résultats.
\\subsubsection{Résultats et métriques}
Performance, couverture de test, vulnérabilités détectées et corrigées.

\\subsection{Conclusion}
Bilan technique, points forts, limitations identifiées.

DONNÉES DU PROJET :
{context}

INFORMATIONS DÉTAILLÉES DES DOCUMENTS DE STAGE :
{extracted_info}""",

"conclusion_generale": """Rédige la CONCLUSION GÉNÉRALE du rapport PFA. Longueur : 1 à 1.5 pages (~400 mots).
Prose continue sans sections ni titres.

Structure des paragraphes :
1. Rappel du contexte et de la problématique posée en introduction.
2. Synthèse des réalisations chapitre par chapitre (1-2 phrases chacun).
3. Évaluation de l'atteinte des objectifs initiaux.
4. Compétences techniques et méthodologiques acquises durant le stage.
5. Limitations identifiées (honnêteté académique requise).
6. Phrase de transition vers les perspectives.

DONNÉES :
{context}

RÉSUMÉ DES SECTIONS :
{previous_sections_summary}""",

"perspectives": """Rédige la section PERSPECTIVES du rapport PFA. Longueur : ~1 page (~300 mots).
Prose structurée, sans listes à puces — utilise des sous-paragraphes.

Présente 4 à 5 axes d'amélioration concrets et réalistes :
- Performance et scalabilité (ex: Kubernetes, cache Redis, queues)
- Enrichissement fonctionnel (ex: nouveaux modules, intégrations)
- Qualité et fiabilité (ex: IA pour améliorer les résultats, fine-tuning)
- Conformité et certification (ISO 27001, SOC 2, RGPD avancé)
- Évolutions technologiques (ex: passage vers une architecture événementielle)

Chaque axe = 1 paragraphe de 2-3 phrases avec \\hspace{10pt}.

DONNÉES :
{context}""",

"glossaire": """Génère la LISTE DES ABRÉVIATIONS du rapport PFA.
Format STRICT — une abréviation par ligne, ordre alphabétique :
SIGLE : Signification complète (traduction française entre parenthèses si anglais).

Exemple :
API : Application Programming Interface (Interface de Programmation Applicative).
CI/CD : Continuous Integration / Continuous Deployment.
CVE : Common Vulnerabilities and Exposures.
DNS : Domain Name System.

N'inclus QUE les acronymes réellement utilisés dans ce projet.
Technologies : {context}
Acronymes identifiés dans les documents : {extracted_info}""",
}


class LLMClient:
    def __init__(self):
        self.api_key  = os.getenv("OPENAI_API_KEY", "")
        self.base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
        self.model    = os.getenv("LLM_MODEL", "gpt-4o")
        logger.info(f"LLM: {self.model} @ {self.base_url}")

    async def generate_section(self, section_key, section_cfg, context, previous_sections) -> str:
        template = PROMPTS.get(section_key)
        if not template:
            template = (
                "Rédige la section '{section_title}' du rapport PFE en prose LaTeX pure.\n"
                "Contexte : {context}"
            )

        ctx_str      = _ctx_str(context)
        extracted    = json.dumps(context.get("extracted_info", {}), ensure_ascii=False, indent=2)
        prev_summary = _summarize(previous_sections)
        technologies = context.get("confirmed_technologies", [])
        tech_list    = "\n".join(
            f"- {t['name']} ({t.get('category','')})"
            for t in technologies
        ) if technologies else "Voir données du projet"
        tech_domains = ", ".join(sorted({
            t.get("category","") for t in technologies if t.get("category")
        })) or "informatique, sécurité"
        modules_info = json.dumps(context.get("modules", []), ensure_ascii=False, indent=2)

        prompt = _render_prompt(template, {
            "section_title": section_cfg.get("title", "Sans titre"),
            "context": ctx_str,
            "extracted_info": extracted,
            "previous_sections_summary": prev_summary,
            "technologies_list": tech_list,
            "tech_domains": tech_domains,
            "modules_info": modules_info,
        })

        return await self._chat(
            [{"role":"system","content":SYSTEM_PROMPT},
             {"role":"user","content":prompt}],
            temperature=0.55,
            max_tokens=4000,
        )

    async def fix_latex(self, tex: str, errors: list) -> str:
        return await self._chat(
            [{"role":"system","content":"Expert LaTeX. Corrige les erreurs. Retourne UNIQUEMENT le code corrigé."},
             {"role":"user","content":f"Erreurs:\n{chr(10).join(errors)}\n\nDocument:\n{tex}"}],
            temperature=0.1, max_tokens=8000,
        )

    async def _chat(self, messages, temperature=0.55, max_tokens=4000) -> str:
        url     = f"{self.base_url}/chat/completions"
        headers = {"Content-Type":"application/json","Authorization":f"Bearer {self.api_key}"}
        payload = {"model":self.model,"messages":messages,"temperature":temperature,"max_tokens":max_tokens}
        async with httpx.AsyncClient(timeout=180.0) as client:
            resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"].strip()


def _ctx_str(ctx: dict) -> str:
    safe = {k:v for k,v in ctx.items() if k not in ("extracted_info","doc_texts","zip_bytes")}
    return json.dumps(safe, ensure_ascii=False, indent=2)


def _render_prompt(template: str, values: dict) -> str:
    rendered = template.replace("{{", "{").replace("}}", "}")
    for key, value in values.items():
        rendered = rendered.replace(f"{{{key}}}", str(value))
    return rendered


def _summarize(sections: dict) -> str:
    if not sections:
        return "Aucune section précédente."
    return "\n".join(f"- {k}: {str(v)[:200]}..." for k,v in sections.items())
