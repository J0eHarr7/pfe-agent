"""
LLM Client — Specialized prompts per PFE section.
Pure httpx, no openai SDK dependency.
All output is clean LaTeX prose — NO markdown, NO ## headers, NO bullet points with *.
"""

import os, json, logging, httpx
logger = logging.getLogger(__name__)

# ── System prompt ─────────────────────────────────────────────────────────────
SYSTEM_PROMPT = r"""Tu es un expert en rédaction de rapports académiques de Projet de Fin d'Études (PFE/PFA)
pour les élèves ingénieurs de l'ENSA Marrakech.

RÈGLES ABSOLUES — RESPECTE-LES SANS EXCEPTION :

1. AUCUN MARKDOWN : N'utilise JAMAIS ##, ###, **, *, -, >. Ton texte sera intégré directement dans du LaTeX.
2. STRUCTURE LATEX : Utilise \section{}, \subsection{}, \subsubsection{}, \paragraph{} pour les titres.
3. LISTES : Utilise \begin{itemize}\item ... \end{itemize} ou \begin{enumerate}\item ... \end{enumerate}.
4. GRAS/ITALIQUE : Utilise \textbf{} et \textit{} jamais ** ou *.
5. PROSE ACADÉMIQUE : Rédige en paragraphes denses, style scientifique français, jamais de listes seules.
6. LONGUEUR : Chaque chapitre doit être substantiel (minimum 600 mots de contenu réel).
7. INTRODUCTION/CONCLUSION : Chaque chapitre commence par \section*{Introduction} et finit par \section*{Conclusion}.
8. PAS DE BALISES CODE : Ne mets jamais ```latex ou ``` dans ta réponse.
9. LANGUE : Français académique uniquement (sauf Abstract en anglais et résumé arabe).
10. CHIFFRES : Numérote les sections selon le chapitre (ex: pour ch2 → \section{2.1 Titre})."""

# ── Section prompts ───────────────────────────────────────────────────────────
SECTION_PROMPTS = {

"resume_fr": r"""Rédige le RÉSUMÉ en français du projet PFE.
Utilise ce format LaTeX exact (sans balises code) :

\section*{{Résumé}}
[Paragraphe 1 (~80 mots) : contexte général et enjeux du domaine]

[Paragraphe 2 (~100 mots) : description du projet, approche adoptée, contributions principales]

[Paragraphe 3 (~70 mots) : résultats obtenus et apport pour l'organisation]

\textbf{{Mots-clés :}} mot1, mot2, mot3, mot4, mot5.

Données du projet :
{context}""",

"resume_en": r"""Write the ABSTRACT in English for this PFE project.
Use this exact LaTeX format (no code fences):

\section*{{Abstract}}
[Paragraph 1 (~80 words): general context and domain challenges]

[Paragraph 2 (~100 words): project description, adopted approach, main contributions]

[Paragraph 3 (~70 words): results obtained and organizational value]

\textbf{{Keywords:}} word1, word2, word3, word4, word5.

Project data:
{context}""",

"resume_ar": r"""اكتب الملخص باللغة العربية لمشروع نهاية الدراسات.
استخدم هذا التنسيق اللاتيني بدون أكواد:

\section*{{ملخص}}
[الفقرة 1: السياق العام والإشكالية (~80 كلمة)]

[الفقرة 2: وصف المشروع والمساهمات الرئيسية (~100 كلمة)]

[الفقرة 3: النتائج والخلاصة (~70 كلمة)]

\textbf{{الكلمات المفتاحية:}} كلمة1، كلمة2، كلمة3، كلمة4، كلمة5.

بيانات المشروع:
{context}""",

"remerciements": r"""Rédige la page de REMERCIEMENTS en LaTeX (sans balises code, sans markdown).
Format attendu :

\section*{{Remerciements}}
[Paragraphe d'ouverture général remerciant toutes les personnes ayant contribué]

[Paragraphe dédié à l'encadrant(e) de l'entreprise : nom, rôle, qualités, apport]

[Paragraphe dédié à l'encadrant(e) pédagogique de l'ENSA : nom, expertise, soutien]

[Paragraphe de remerciements au corps professoral et à l'institution]

\section*{{Dédicaces}}
\begin{{itemize}}
\item [Dédicace 1]
\item [Dédicace 2]
\end{{itemize}}

Données :
{context}""",

"introduction_generale": r"""Rédige l'INTRODUCTION GÉNÉRALE du rapport PFA en LaTeX pur.
Maximum 3 pages (~700 mots). Format strict :

\section*{{Introduction Générale}}

[Paragraphe 1 (~120 mots) : contexte macro du domaine, enjeux stratégiques actuels, 
statistiques ou tendances récentes si pertinentes]

[Paragraphe 2 (~120 mots) : problèmes spécifiques que rencontrent les organisations 
dans ce domaine, limitations des solutions actuelles]

[Paragraphe 3 (~100 mots) : présentation de l'entreprise d'accueil en 3-4 phrases 
et positionnement du projet dans ce contexte]

[Paragraphe 4 (~100 mots) : approche adoptée et contributions du projet]

[Paragraphe 5 (~120 mots) : plan du rapport, présentation de chaque chapitre 
en prose (pas de liste)]

IMPORTANT : Ne mentionnez PAS les contributions détaillées ni les résultats — 
réservez-les pour la conclusion.

Données du projet :
{context}""",

"chapitre1_contexte": r"""Rédige le CHAPITRE 1 COMPLET en LaTeX pur (sans markdown, sans ##).

Le chapitre doit contenir ces sections dans cet ordre exact :

\section*{{Introduction}}
[1 paragraphe situant l'objectif du chapitre et son contenu]

\section{{1.1 Présentation de l'organisme d'accueil}}
\subsection{{1.1.1 Présentation générale}}
[3-4 paragraphes : histoire/fondation, secteur d'activité, expertise, zone géographique, 
taille/effectifs si connu, positionnement sur le marché]

\subsection{{1.1.2 Missions et valeurs}}
[2-3 paragraphes : mission principale, vision, valeurs fondamentales, convictions]

\subsection{{1.1.3 Services et offre}}
[2 paragraphes : services proposés, clients cibles, différenciation concurrentielle]

\section{{1.2 Motivation et problématique}}
[3 paragraphes structurés :
- Paragraphe 1 : constats et problèmes observés dans le domaine
- Paragraphe 2 : limitations des solutions existantes  
- Paragraphe 3 : formulation claire de la problématique centrale en \textit{{italique}}]

Questions secondaires découlant de la problématique (en \begin{{itemize}}...\end{{itemize}})

\section{{1.3 Objectifs du projet}}
\subsection{{1.3.1 Objectifs généraux}}
[Liste \begin{{enumerate}}...\end{{enumerate}} de 4-5 objectifs généraux avec explication]

\subsection{{1.3.2 Objectifs spécifiques}}
[Pour chaque module/composant : objectif spécifique détaillé]

\section{{1.4 Méthodologie de gestion de projet}}
\subsection{{1.4.1 Approche adoptée}}
[2 paragraphes sur la méthode (Agile/Scrum/autre) et sa justification]

\subsection{{1.4.2 Outils utilisés}}
[Paragraphe sur les outils de gestion (Jira/Trello/GitHub/etc.)]

\section{{1.5 Planification du projet}}
[Description de l'organisation en sprints/phases, diagramme de Gantt sera inséré ici]

\begin{{figure}}[H]
\centering
\includegraphics[width=0.95\linewidth]{{images/gantt.png}}
\caption{{Diagramme de Gantt du projet}}
\label{{fig:gantt}}
\end{{figure}}

\section{{1.6 Rôles et responsabilités}}
[Tableau ou liste des rôles Dev/Sec/Ops ou autre répartition selon le projet]

\section*{{Conclusion}}
[1 paragraphe récapitulatif et transition vers le chapitre suivant]

Données de l'entreprise et du projet :
{context}

Informations extraites des documents :
{extracted_info}

Tâches/modules identifiés :
{modules_info}""",

"chapitre2_analyse": r"""Rédige le CHAPITRE 2 COMPLET en LaTeX pur (sans markdown, sans ##).

\section*{{Introduction}}
[1 paragraphe présentant l'importance de l'analyse et la structure du chapitre]

\section{{2.1 Analyse des besoins}}
\subsection{{2.1.1 Besoins fonctionnels}}
[Organisation par module/acteur. Pour chaque module :
\subsubsection{{Module X — Nom}}
Description détaillée des fonctionnalités en prose + liste \begin{{itemize}}]

\subsection{{2.1.2 Besoins non fonctionnels}}
[Sous-sections pour chaque catégorie :]
\subsubsection{{Sécurité}}
[2 paragraphes détaillés]
\subsubsection{{Performance et scalabilité}}
[2 paragraphes]
\subsubsection{{Maintenabilité et évolutivité}}
[1-2 paragraphes]
\subsubsection{{Conformité réglementaire}}
[1-2 paragraphes : RGPD, ISO, OWASP selon le projet]
\subsubsection{{Portabilité et déploiement}}
[1 paragraphe]

\section{{2.2 Identification des acteurs}}
[Description des différents types d'utilisateurs et leur rôle dans le système]

\section{{2.3 Modélisation conceptuelle}}
\subsection{{2.3.1 Architecture en couches}}
[Description de l'architecture globale : présentation, logique métier, données, services]

\subsection{{2.3.2 Principes de conception}}
[Séparation des préoccupations, modularité, couplage faible, etc.]

\subsection{{2.3.3 Diagramme de cas d'utilisation}}
[Description textuelle des cas d'utilisation principaux par acteur]

\section*{{Conclusion}}
[Synthèse et transition vers le chapitre 3]

Données du projet :
{context}

Informations extraites :
{extracted_info}""",

"chapitre3_etat_art": r"""Rédige le CHAPITRE 3 COMPLET en LaTeX pur : "État de l'art — Fondements théoriques".
Ce chapitre est la revue de littérature (~15-18 pages). Sois TRÈS détaillé.

\section*{{Introduction}}
[1 paragraphe sur l'importance des fondements théoriques et la structure du chapitre]

Pour chaque domaine technologique/conceptuel du projet, génère une section complète :

\section{{3.1 [Premier domaine clé]}}
\subsection{{3.1.1 Définitions et concepts fondamentaux}}
[3-4 paragraphes denses définissant les concepts de base]

\subsection{{3.1.2 Évolution et contexte historique}}
[2 paragraphes sur l'évolution du domaine]

\subsection{{3.1.3 Standards et référentiels}}
[2-3 paragraphes sur les normes (OWASP, ISO 27001, NIST, etc. selon le domaine)]

\section{{3.2 [Deuxième domaine clé]}}
[Même structure]

\section{{3.3 Comparaison des solutions existantes}}
[Tableau comparatif ou analyse comparative des outils/approches disponibles]

\section{{3.4 Synthèse et positionnement du projet}}
[2-3 paragraphes justifiant les choix par rapport à l'état de l'art]

\section*{{Conclusion}}
[Synthèse et transition vers le chapitre des outils]

Domaines à couvrir selon les technologies :
{tech_domains}

Données du projet :
{context}

Informations extraites :
{extracted_info}""",

"chapitre4_outils": r"""Rédige le CHAPITRE 4 COMPLET en LaTeX pur : "Outils et Technologies".

\section*{{Introduction}}
[1 paragraphe présentant les critères de sélection technologique]

\section{{4.1 Description et justification des technologies}}

Pour CHAQUE technologie listée, génère une sous-section :
\subsection{{4.1.X [Nom de la technologie]}}
\begin{{figure}}[H]
\centering
\includegraphics[height=1.5cm]{{images/logo_[nom].png}}
\caption{{Logo de [Nom]}}
\label{{fig:logo_[nom]}}
\end{{figure}}

\textbf{{Description :}} [2-3 phrases décrivant la technologie : créateur, date, paradigme, usage]

\textbf{{Justification du choix :}}
\begin{{itemize}}
\item [Critère 1 : explication détaillée]
\item [Critère 2 : explication détaillée]
\item [Critère 3 : explication détaillée]
\end{{itemize}}

\textbf{{Rôle dans le projet :}} [1-2 phrases sur l'utilisation concrète dans ce projet]

\section{{4.2 Architecture technologique globale}}
[Description en prose de comment toutes les technologies s'articulent]

\begin{{figure}}[H]
\centering
\includegraphics[width=0.9\linewidth]{{images/architecture.png}}
\caption{{Architecture technologique globale}}
\label{{fig:architecture}}
\end{{figure}}

\section{{4.3 Considérations de sécurité et déploiement}}
[2-3 paragraphes sur les aspects sécurité et déploiement]

\section*{{Conclusion}}
[Transition vers le chapitre d'implémentation]

Technologies à traiter :
{technologies_list}

Données du projet :
{context}

Informations extraites :
{extracted_info}""",

"chapitre5_realisation": r"""Rédige le CHAPITRE 5 COMPLET en LaTeX pur : "Conception et Implémentation Pratique".
Longueur cible : 15 à 20 pages. Sois TRÈS détaillé et concret.

RÈGLE FONDAMENTALE DE CE CHAPITRE :
Le récit de l'implémentation doit STRICTEMENT SUIVRE L'ORDRE CHRONOLOGIQUE des tâches
listées dans "Tâches réalisées (ordonnées)". Chaque tâche correspond à une réalisation
concrète effectuée pendant le stage. Tu dois présenter le travail tel qu'il s'est déroulé
dans le temps, de la première tâche à la dernière, comme un journal technique de la
progression du projet. Ne réordonne jamais les tâches. Ne regroupe pas des tâches
non consécutives. Respecte l'enchaînement logique et temporel.

\section*{{Introduction}}
\addcontentsline{{toc}}{{section}}{{Introduction}}
[1-2 paragraphes : présente ce chapitre comme la traduction concrète et chronologique
des besoins identifiés au chapitre 2 en réalisations techniques. Mentionne que le
développement a suivi une progression structurée dont l'ordre est fidèlement retranscrit ici.]

\section{{5.1 Architecture globale du projet}}
\subsection{{5.1.1 Vision d'ensemble et principes architecturaux}}
[2-3 paragraphes denses : principes directeurs (modularité, API-first, séparation des
préoccupations, isolation des traitements, stateless). Explique comment ces principes
ont guidé chaque décision d'implémentation tout au long du projet.]

\subsection{{5.1.2 Architecture en couches détaillée}}
[Décris chaque couche (présentation, application, logique métier, services, données)
avec les composants qui la constituent et les responsabilités de chacun.
Inclus un placeholder figure :]
\begin{{figure}}[H]
\centering
\includegraphics[width=0.9\linewidth]{{screens/architecture_globale.png}}
\caption{{Architecture globale du projet}}
\label{{fig:arch_globale}}
\end{{figure}}

\subsection{{5.1.3 Flux de données et interactions entre composants}}
[2 paragraphes sur les flux de communication entre les couches et composants :
protocoles utilisés (REST, WebSocket, etc.), format des échanges (JSON, etc.),
gestion des erreurs et des états.]

\section{{5.2 Déroulement chronologique de l'implémentation}}
[1 paragraphe introductif : explique que le développement s'est déroulé en étapes
successives et interdépendantes, chaque réalisation s'appuyant sur les précédentes.
Le plan de cette section suit fidèlement l'ordre des sprints/tâches du projet.]

--- MAINTENANT, pour chaque tâche dans "Tâches réalisées (ordonnées)" ci-dessous,
génère une \subsection{{5.2.N [Titre exact de la tâche]}} dans L'ORDRE EXACT de la liste.
Ne saute aucune tâche. Ne change pas l'ordre.

Pour CHAQUE tâche, rédige :

\subsection{{5.2.N [Titre de la tâche N]}}

[Paragraphe de contexte (2-3 phrases) : Situe cette tâche dans la progression globale.
Explique pourquoi elle intervient à ce moment précis du développement, ce qui la précède
et ce qu'elle rend possible pour la suite. Utilise des connecteurs chronologiques :
"Dans la continuité de...", "À cette étape du développement...", "Fort des bases
établies précédemment...", "Cette phase constitue le fondement de..."]

\subsubsection{{Objectif et périmètre}}
[1-2 paragraphes : objectif précis de cette tâche, périmètre fonctionnel et technique,
ce qui était attendu comme livrable à l'issue de cette étape.]

\subsubsection{{Approche technique et implémentation}}
[2-4 paragraphes denses : comment cette tâche a été techniquement réalisée. Décris
les choix d'implémentation, les algorithmes ou logiques métier mis en œuvre, les
difficultés rencontrées et comment elles ont été surmontées. Référence les technologies
de la liste confirmée. Ne reproduis pas de code source — décris la logique.]

\subsubsection{{Résultats et validation}}
[1-2 paragraphes : qu'est-ce que cette tâche a produit concrètement ? Comment les
résultats ont-ils été validés ? Métriques, tests, démonstrations. Inclus un
placeholder figure si pertinent :]
\begin{{figure}}[H]
\centering
\includegraphics[width=0.85\linewidth]{{screens/tache_N.png}}
\caption{{[Légende pertinente pour cette tâche]}}
\label{{fig:tache_N}}
\end{{figure}}

[Phrase de transition vers la tâche suivante : "La réalisation de [cette tâche] a
permis d'aborder la phase suivante..." ou "Les résultats de cette étape ont
directement conditionné..." — sauf pour la dernière tâche.]

---

\section{{5.3 Intégration et tests}}
\subsection{{5.3.1 Stratégie d'intégration}}
[2 paragraphes : comment les composants développés séquentiellement ont été intégrés
progressivement. Approche bottom-up ou top-down, tests d'intégration continue, CI/CD
si applicable.]

\subsection{{5.3.2 Tests réalisés}}
[2-3 paragraphes : types de tests (unitaires, intégration, fonctionnels, sécurité),
outils utilisés pour chaque type, couverture atteinte.]

\subsection{{5.3.3 Résultats et métriques finaux}}
[2 paragraphes : bilan quantitatif et qualitatif des résultats de l'ensemble du
chapitre. Performance, couverture de test, vulnérabilités traitées, objectifs atteints.]

\section*{{Conclusion}}
\addcontentsline{{toc}}{{section}}{{Conclusion}}
[2 paragraphes : bilan technique du chapitre, points forts de l'implémentation
réalisée dans cet ordre chronologique, limitations identifiées, transition vers
la conclusion générale.]

---

Données du projet :
{context}

Informations détaillées extraites des documents de stage :
{extracted_info}

Tâches réalisées (ordonnées — RESPECTE CET ORDRE DANS TA RÉDACTION) :
{modules_info}""",

"conclusion_generale": r"""Rédige la CONCLUSION GÉNÉRALE en LaTeX pur (max 1.5 pages, ~450 mots).

\section*{{Conclusion Générale}}

[Paragraphe 1 (~100 mots) : rappel du contexte et de la problématique de départ]

[Paragraphe 2 (~150 mots) : récapitulatif des réalisations de chaque module/composant,
en mentionnant chaque chapitre et ses apports]

[Paragraphe 3 (~100 mots) : évaluation de l'atteinte des objectifs initiaux,
bilan technique et méthodologique]

[Paragraphe 4 (~100 mots) : compétences acquises (techniques, méthodologiques, 
professionnelles) et valeur de l'expérience]

[Phrase de clôture ouvrant sur les perspectives]

Données :
{context}

Résumé des chapitres générés :
{previous_sections_summary}""",

"perspectives": r"""Rédige la section PERSPECTIVES en LaTeX pur (~1 page, ~350 mots).

\section*{{Perspectives}}

[Paragraphe introductif présentant le potentiel d'évolution du projet]

\section*{{Axes d'amélioration}}

\subsection*{{Performance et scalabilité}}
[1-2 paragraphes concrets : mécanismes de queue, cache distribué, orchestration Kubernetes]

\subsection*{{Enrichissement fonctionnel}}
[1-2 paragraphes : modules complémentaires, nouvelles fonctionnalités identifiées]

\subsection*{{Qualité et intelligence artificielle}}
[1 paragraphe : IA, apprentissage automatique, fine-tuning si applicable]

\subsection*{{Conformité et certification}}
[1 paragraphe : ISO 27001, SOC 2, RGPD, certifications envisageables]

\subsection*{{Déploiement et industrialisation}}
[1 paragraphe : passage en production, monitoring, DevOps avancé]

Données :
{context}
{previous_sections_summary}""",

"glossaire": r"""Génère la LISTE DES ABRÉVIATIONS en LaTeX pur pour ce rapport PFA.

Format exact attendu (chaque ligne sur une entrée, classé alphabétiquement) :
\section*{{Liste des Abréviations}}
\begin{{description}}[leftmargin=3cm,style=nextline]
\item[SIGLE] Signification complète en français (English if applicable).
\end{{description}}

- Classe par ordre alphabétique STRICT
- Mets uniquement les acronymes réellement présents dans le projet
- Inclus les acronymes techniques, les outils, les protocoles, les standards
- Minimum 20 entrées

Technologies et domaine :
{context}

Acronymes identifiés dans les documents :
{extracted_info}""",
}


class LLMClient:
    def __init__(self):
        self.api_key  = os.getenv("OPENAI_API_KEY", "")
        self.base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
        self.model    = os.getenv("LLM_MODEL", "gpt-4o")
        logger.info(f"LLM: {self.model} @ {self.base_url}")

    async def generate_section(self, section_key, section_cfg, context, previous_sections):
        template = SECTION_PROMPTS.get(section_key)
        if not template:
            template = (
                f"Rédige la section LaTeX \\section*{{{section_cfg['title']}}} du rapport PFA "
                f"en LaTeX pur, sans markdown.\nContexte : {{context}}"
            )

        ctx_str      = _ctx_str(context)
        extracted    = json.dumps(context.get("extracted_info", {}), ensure_ascii=False, indent=2)
        prev_summary = _summarize(previous_sections)
        technologies = context.get("confirmed_technologies", [])
        tech_list    = "\n".join(
            f"- {t['name']} ({t.get('category','')}) : {t.get('description','')}"
            for t in technologies
        ) or ctx_str
        tech_domains = ", ".join(set(t.get("category","") for t in technologies))

        # Chapter 5: feed ordered tasks merged with modules as modules_info
        if section_key == "chapitre5_realisation":
            tasks   = context.get("tasks", [])
            modules = context.get("modules", [])
            module_map = {m.get("name","").lower(): m for m in modules}
            ordered = []
            for t in tasks:
                entry = {
                    "title":          t.get("title", ""),
                    "description":    t.get("description", ""),
                    "tools_used":     t.get("tools_used", []),
                    "deliverable":    t.get("deliverable", ""),
                    "duration_weeks": t.get("duration_weeks", 2),
                }
                for mname, mdata in module_map.items():
                    if mname in t.get("title","").lower() or t.get("title","").lower() in mname:
                        entry["implementation"] = mdata.get("implementation","")
                        entry["results"]        = mdata.get("results","")
                        entry["technologies"]   = mdata.get("technologies",[])
                        break
                ordered.append(entry)
            for m in modules:
                if not any(m.get("name","").lower() in t.get("title","").lower() for t in tasks):
                    ordered.append({
                        "title":          m.get("name",""),
                        "description":    m.get("objective",""),
                        "implementation": m.get("implementation",""),
                        "results":        m.get("results",""),
                        "technologies":   m.get("technologies",[]),
                    })
            modules_info = json.dumps(ordered, ensure_ascii=False, indent=2)
        else:
            modules_info = json.dumps(context.get("modules", []), ensure_ascii=False, indent=2)

        prompt = template.format(
            context=ctx_str,
            extracted_info=extracted,
            previous_sections_summary=prev_summary,
            technologies_list=tech_list,
            tech_domains=tech_domains,
            modules_info=modules_info,
        )

        raw = await self._chat(
            [{"role":"system","content":SYSTEM_PROMPT},
             {"role":"user","content":prompt}],
            temperature=0.6, max_tokens=4000,
        )
        # Strip any accidental markdown fences
        return _strip_md(raw)

    async def fix_latex(self, tex, errors):
        err_str = "\n".join(errors)
        raw = await self._chat([
            {"role":"system","content":"Tu es un expert LaTeX. Corrige les erreurs de compilation. Retourne UNIQUEMENT le LaTeX corrigé, aucun commentaire."},
            {"role":"user","content":f"Erreurs:\n{err_str}\n\nDocument:\n{tex}"},
        ], temperature=0.1, max_tokens=8000)
        return _strip_md(raw)

    async def _chat(self, messages, temperature=0.6, max_tokens=4000):
        url = f"{self.base_url}/chat/completions"
        payload = {"model":self.model,"messages":messages,"temperature":temperature,"max_tokens":max_tokens}
        async with httpx.AsyncClient(timeout=180.0) as c:
            r = await c.post(url, headers={"Content-Type":"application/json","Authorization":f"Bearer {self.api_key}"}, json=payload)
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"].strip()


def _strip_md(text: str) -> str:
    """Remove any accidental markdown formatting from LLM output."""
    import re
    # Remove code fences
    text = re.sub(r'```(?:latex|tex)?\n?', '', text)
    text = re.sub(r'```', '', text)
    # Convert markdown headers to LaTeX (safety net)
    text = re.sub(r'^#{4}\s+(.+)$', r'\\subsubsection{\1}', text, flags=re.MULTILINE)
    text = re.sub(r'^#{3}\s+(.+)$', r'\\subsection{\1}', text, flags=re.MULTILINE)
    text = re.sub(r'^#{2}\s+(.+)$', r'\\section{\1}', text, flags=re.MULTILINE)
    text = re.sub(r'^#{1}\s+(.+)$', r'\\section*{\1}', text, flags=re.MULTILINE)
    # Convert markdown bold
    text = re.sub(r'\*\*(.+?)\*\*', r'\\textbf{\1}', text)
    # Convert markdown italic (but not list bullets)
    text = re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', r'\\textit{\1}', text)
    return text.strip()

def _ctx_str(ctx: dict) -> str:
    safe = {k:v for k,v in ctx.items() if k not in ("extracted_info","doc_texts","zip_bytes")}
    return json.dumps(safe, ensure_ascii=False, indent=2)

def _summarize(sections: dict) -> str:
    if not sections: return "Aucune section précédente."
    return "\n".join(f"- {k}: {v[:250].replace(chr(10),' ')}..." for k,v in sections.items())