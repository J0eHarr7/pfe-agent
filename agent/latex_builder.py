"""
LaTeX Builder — Builds a structured LaTeX project matching the ENSA template exactly.

Structure:
  rapport_pfe/
    main.tex
    title.tex
    Chapters/
      Introduction.tex
      CH1.tex  Chapitre1.tex
      CH2.tex  Chapitre2.tex
      CH3.tex  Chapitre3.tex
      CH4.tex  Chapitre4.tex
      CH5.tex  Chapitre5.tex
      Conclusion.tex
      Perspectives.tex
      References.tex
      Remerciement.tex
      Résumé.tex
      ResumeArabe.tex
      Abstract.tex
    logo/
      Logo_ENSA.jpg   (placeholder)
      logo_company.jpg
"""

import re
from agent.context_store import ContextStore

HEADING_RE = re.compile(r'^#{1,6}\s+(.*)')
BOLD_RE = re.compile(r'\*\*(.+?)\*\*')
ITALIC_RE = re.compile(r'\*(.+?)\*')
INLINE_CODE_RE = re.compile(r'`([^`]+)`')
BULLET_RE = re.compile(r'^\s*[-*]\s+')
NUMBERED_RE = re.compile(r'^\s*\d+\.\s+')
HR_RE = re.compile(r'^-{3,}$')


# ─────────────────────────────────────────────────────────────────────────────
# main.tex  (matches the provided template exactly)
# ─────────────────────────────────────────────────────────────────────────────
def build_main() -> str:
    return r"""\documentclass[12pt]{article}
%--------- Packages ----------------
\usepackage{graphicx}
\usepackage[a4paper,left=1in,right=1in,top=1in,bottom=1in]{geometry}
\usepackage{newtxtext}
\usepackage{newtxmath}
\usepackage[style=apa,backend=biber]{biblatex}
\usepackage[french]{babel}
\usepackage{csquotes}
\usepackage{bookmark}
\usepackage{setspace}
\usepackage{fancyhdr}
\usepackage[font=footnotesize,justification=centering]{caption}
\usepackage{hyperref}
\usepackage{float}
\usepackage{xcolor}
\usepackage{pgfgantt}
\usepackage{rotating}
\usepackage{booktabs}
\usepackage{longtable}
\usepackage{array}
\usepackage{multirow}
\usepackage{enumitem}
\usepackage{tcolorbox}
\usepackage{listings}
\usepackage{amsmath}
\addbibresource{References.bib}
%--------- Set Up ------------------
\setstretch{1.5}
\pagestyle{fancy}
\fancyhf{}
\fancyhead[L]{\nouppercase{\leftmark}}
\fancyfoot[C]{\thepage}
\renewcommand{\headrulewidth}{0.4pt}
\fancypagestyle{plain}{%
  \fancyhf{}%
  \renewcommand{\headrulewidth}{0pt}%
}
\fancypagestyle{noheaderfooter}{%
  \fancyhf{}%
  \renewcommand{\headrulewidth}{0pt}%
  \renewcommand{\footrulewidth}{0pt}%
}
\lstset{
  basicstyle=\small\ttfamily,
  breaklines=true,
  frame=single,
  backgroundcolor=\color{gray!8},
  keywordstyle=\color{blue!70},
  commentstyle=\color{green!50!black},
  stringstyle=\color{red!70!black},
  numbers=left,
  numberstyle=\tiny\color{gray},
}
%-------- Document -----------------
\begin{document}
\input{title}
\fancyhf{}
\setlength{\headheight}{33pt}
\fancyhead[L]{\nouppercase{\leftmark}}
\fancyfoot[R]{\bf\thepage\ \rm}
\fancyfoot[L]{\emph{}}
\newpage
\thispagestyle{empty}
\phantom{123}
\fancyhead[L]{\nouppercase{\leftmark}}
\renewcommand{\listfigurename}{Liste des Figures}
\newpage
\input{Chapters/Remerciement}
\input{Chapters/Résumé}
\input{Chapters/Abstract}
\newpage
\renewcommand{\contentsname}{Table des Matières}
\thispagestyle{empty}
\tableofcontents
\thispagestyle{empty}
\newpage
\renewcommand{\listfigurename}{Liste des Figures}
\thispagestyle{empty}
\markboth{Liste des Figures}{Liste des Figures}
\listoffigures
\input{Chapters/Introduction}
\input{Chapters/CH1}
\input{Chapters/Chapitre1}
\input{Chapters/CH2}
\input{Chapters/Chapitre2}
\input{Chapters/CH3}
\input{Chapters/Chapitre3}
\input{Chapters/CH4}
\input{Chapters/Chapitre4}
\input{Chapters/CH5}
\input{Chapters/Chapitre5}
\input{Chapters/Conclusion}
\input{Chapters/Perspectives}
\input{Chapters/References}
\printbibliography[title={Bibliographie}]
\pagebreak
\newpage
\end{document}
"""


# ─────────────────────────────────────────────────────────────────────────────
# title.tex  (matches provided template)
# ─────────────────────────────────────────────────────────────────────────────
def build_title(ctx: ContextStore) -> str:
    students = ctx.get("students", [ctx.get("student_name", "Étudiant")])
    if isinstance(students, list):
        # format pairs on same line
        pairs = []
        for i in range(0, len(students), 2):
            if i + 1 < len(students):
                pairs.append(f"{tex(students[i])} \\hspace{{10pt}} {tex(students[i+1])}")
            else:
                pairs.append(tex(students[i]))
        student_lines = "\\\\\n".join(pairs)
    else:
        student_lines = tex(students)

    jury = ctx.get("jury_members", [ctx.get("supervisor_school", "Pr. Encadrant")])
    jury_lines = "\\\\\n".join(tex(j) for j in jury) if isinstance(jury, list) else tex(jury)

    company_logo = ctx.get("company_logo_filename", "logo_company.jpg")
    date_soutenance = ctx.get("date_soutenance", ctx.get("date_fin", "2025"))

    return rf"""\begin{{titlepage}}
\newcommand{{\HRule}}{{\rule{{\linewidth}}{{0.5mm}}}}
\begin{{minipage}}{{0.5\textwidth}}
    \begin{{flushleft}}
        \IfFileExists{{logo/Logo_ENSA.jpg}}{{\includegraphics[width=4cm]{{logo/Logo_ENSA.jpg}}}}{{}}
    \end{{flushleft}}
\end{{minipage}}%
\begin{{minipage}}{{0.5\textwidth}}
    \begin{{flushright}}
        \IfFileExists{{logo/{company_logo}}}{{\includegraphics[width=5cm]{{logo/{company_logo}}}}}{{}}
    \end{{flushright}}
\end{{minipage}}
\vspace{{0.8cm}}
\begin{{center}}
\textsc{{\large Université Cadi Ayyad\\
École Nationale des Sciences Appliquées de Marrakech\\
Filière {tex(ctx.get("filiere","Génie Cyber-Défense et Systèmes de Télécommunications Embarqués"))}}}\\[0.3cm]
\HRule\\[0.15cm]
{{\LARGE\bfseries
{tex(ctx.get("project_title","Titre du projet"))}\\[0.15cm]
\par}}
\HRule\\[0.8cm]
\end{{center}}
\vspace{{0.6cm}}
\begin{{minipage}}{{0.45\textwidth}}
\begin{{flushleft}}
\textbf{{\emph{{Réalisé par :}}}}\\
{student_lines}
\end{{flushleft}}
\end{{minipage}}
\hfill
\begin{{minipage}}{{0.45\textwidth}}
\begin{{flushright}}
\textbf{{\emph{{Encadré par :}}}}\\
{tex(ctx.get("supervisor_school","Pr. Encadrant"))}
\end{{flushright}}
\end{{minipage}}
\vspace{{0.6cm}}
\begin{{center}}
\textbf{{Soutenu le {tex(date_soutenance)} devant l'honorable jury}}\\[0.4cm]
{jury_lines}\\
\textbf{{{tex(ctx.get("academic_year","2025 / 2026"))}}}
\end{{center}}
\end{{titlepage}}
"""


# ─────────────────────────────────────────────────────────────────────────────
# CH[N].tex — chapter title page (full-page centered title)
# ─────────────────────────────────────────────────────────────────────────────
CHAPTER_TITLES = {
    1: "Contexte Général",
    2: "Analyse et Conception",
    3: "État de l'Art : Fondements Théoriques",
    4: "Outils et Technologies",
    5: "Conception et Implémentation",
}

def build_ch_title(n: int, title: str = "") -> str:
    display = title or CHAPTER_TITLES.get(n, f"Chapitre {n}")
    return rf"""\clearpage
\thispagestyle{{plain}}
\vspace*{{\fill}}
\begin{{center}}
  \Huge\bfseries Chapitre {n} : {tex(display)}
\end{{center}}
\vspace*{{\fill}}
"""


# ─────────────────────────────────────────────────────────────────────────────
# Chapitre[N].tex — actual chapter content
# ─────────────────────────────────────────────────────────────────────────────
def build_chapter_content(n: int, content: str, ctx: ContextStore = None) -> str:
    """Wrap LLM-generated plain text into a clean LaTeX section structure."""
    clean = _md_to_latex(content)
    clean = _sanitize_empty_lists(clean)

    # Special handling for chapter 1: inject Gantt diagram
    gantt_block = ""
    if n == 1 and ctx:
        tasks = ctx.get("tasks", [])
        if tasks:
            gantt_block = _build_gantt(tasks, ctx)

    return rf"""\newpage
\section{{Chapitre {n} : {tex(CHAPTER_TITLES.get(n, f"Chapitre {n}"))}}}

{clean}

{gantt_block}
"""


# ─────────────────────────────────────────────────────────────────────────────
# Front matter files
# ─────────────────────────────────────────────────────────────────────────────
def build_remerciement(ctx: ContextStore) -> str:
    content = ctx.get("remerciements", "Nous remercions toutes les personnes qui ont contribué à ce projet.")
    dedicaces = ctx.get("dedicaces", ["À nos familles pour leur soutien inconditionnel."])
    ded_items = "\n".join(f"\\item {tex(d)}" for d in dedicaces) if isinstance(dedicaces, list) else f"\\item {tex(dedicaces)}"
    return rf"""\newpage
\thispagestyle{{plain}}
\markboth{{Remerciements}}{{Remerciements}}
\section*{{Remerciements et Dédicaces}}
\addcontentsline{{toc}}{{section}}{{Remerciements et Dédicaces}}

{tex(content)}

\vspace{{1cm}}
\textbf{{Nous dédions ce travail :}}
\begin{{itemize}}
{ded_items}
\end{{itemize}}
\newpage
"""


def build_resume(content: str, ctx: ContextStore) -> str:
    kw = ctx.get("keywords_fr", [])
    kw_str = ", ".join(kw) if kw else ""
    return rf"""\newpage
\thispagestyle{{plain}}
\markboth{{Résumé}}{{Résumé}}
\section*{{Résumé}}
\addcontentsline{{toc}}{{section}}{{Résumé}}

{tex(content)}

\vspace{{0.5cm}}
\textbf{{Mots-clés :}} {tex(kw_str)}
\newpage
"""


def build_abstract(content: str, ctx: ContextStore) -> str:
    kw = ctx.get("keywords_en", [])
    kw_str = ", ".join(kw) if kw else ""
    return rf"""\newpage
\thispagestyle{{plain}}
\markboth{{Abstract}}{{Abstract}}
\section*{{Abstract}}
\addcontentsline{{toc}}{{section}}{{Abstract}}

{tex(content)}

\vspace{{0.5cm}}
\textbf{{Keywords:}} {tex(kw_str)}
\newpage
"""


def build_resume_arabe() -> str:
    return r"""\newpage
\thispagestyle{plain}
\markboth{ملخص}{ملخص}
\section*{ملخص}
\addcontentsline{toc}{section}{ملخص}

% Le résumé en arabe sera ajouté ici manuellement dans Overleaf.
% Arabic content requires XeLaTeX or specific Arabic packages.
% Placeholder:
\begin{center}
\textit{(Le résumé en langue arabe sera complété dans Overleaf)}
\end{center}
\newpage
"""


def build_introduction(content: str) -> str:
    clean = _md_to_latex(content)
    return rf"""\newpage
\markboth{{Introduction Générale}}{{Introduction Générale}}
\section*{{Introduction Générale}}
\addcontentsline{{toc}}{{section}}{{Introduction Générale}}

{clean}
\newpage
"""


def build_conclusion(content: str) -> str:
    clean = _md_to_latex(content)
    return rf"""\newpage
\markboth{{Conclusion Générale}}{{Conclusion Générale}}
\section*{{Conclusion Générale}}
\addcontentsline{{toc}}{{section}}{{Conclusion Générale}}

{clean}
\newpage
"""


def build_perspectives(content: str) -> str:
    clean = _md_to_latex(content)
    return rf"""\newpage
\markboth{{Perspectives}}{{Perspectives}}
\section*{{Perspectives}}
\addcontentsline{{toc}}{{section}}{{Perspectives}}

{clean}
\newpage
"""


def build_references_file(refs: list) -> str:
    """Chapter-style references list (in addition to printbibliography)."""
    if not refs:
        return r"""\newpage
\markboth{Références Bibliographiques}{Références Bibliographiques}
\section*{Références Bibliographiques}
\addcontentsline{toc}{section}{Références Bibliographiques}
% Les références seront affichées via \printbibliography
\newpage
"""
    items = []
    for i, r in enumerate(refs, 1):
        items.append(rf"\item[{{[{i}]}}] {tex(r.get('author',''))}. \textit{{{tex(r.get('title',''))}}}. {tex(r.get('extra',''))}. {r.get('year','')}.")
    return rf"""\newpage
\markboth{{Références Bibliographiques}}{{Références Bibliographiques}}
\section*{{Références Bibliographiques}}
\addcontentsline{{toc}}{{section}}{{Références Bibliographiques}}
\begin{{enumerate}}
{"".join(items)}
\end{{enumerate}}
\newpage
"""


def build_references_bib(refs: list) -> str:
    """BibTeX file content."""
    entries = []
    for i, ref in enumerate(refs, 1):
        key = f"ref{i}"
        rtype = ref.get("type", "misc")
        url = ref.get("url", ref.get("extra", ""))
        if rtype == "article":
            entries.append(
                f"@article{{{key},\n  author = {{{ref.get('author','')}}},\n"
                f"  title = {{{ref.get('title','')}}},\n"
                f"  journal = {{{ref.get('extra','')}}},\n"
                f"  year = {{{ref.get('year','')}}}\n}}"
            )
        elif rtype == "book":
            entries.append(
                f"@book{{{key},\n  author = {{{ref.get('author','')}}},\n"
                f"  title = {{{ref.get('title','')}}},\n"
                f"  publisher = {{{ref.get('extra','')}}},\n"
                f"  year = {{{ref.get('year','')}}}\n}}"
            )
        else:
            entries.append(
                f"@misc{{{key},\n  author = {{{ref.get('author','')}}},\n"
                f"  title = {{{ref.get('title','')}}},\n"
                f"  howpublished = {{\\url{{{url}}}}},\n"
                f"  year = {{{ref.get('year','')}}},\n"
                f"  note = {{Consulté en {ref.get('year','2025')}}}\n}}"
            )
    return "\n\n".join(entries)


# ─────────────────────────────────────────────────────────────────────────────
# Chapter 4 tech subsections with logos
# ─────────────────────────────────────────────────────────────────────────────
def build_tech_subsections(technologies: list) -> str:
    parts = []
    for tech in technologies:
        name = tech.get("name", "")
        desc = tech.get("description", "")
        justif = tech.get("justification", "")
        logo_fn = tech.get("logo_filename", "")

        logo_block = ""
        if logo_fn:
            logo_block = rf"""
\begin{{figure}}[H]
\centering
\includegraphics[height=1.8cm]{{logo/{logo_fn}}}
\caption{{Logo de {tex(name)}}}
\end{{figure}}
"""
        parts.append(rf"""
\subsection{{{tex(name)}}}
{logo_block}

\hspace{{10pt}}{tex(desc)}

\hspace{{10pt}}\textbf{{Justification du choix :}} {tex(justif)}
""")
    return "\n".join(parts)


# ─────────────────────────────────────────────────────────────────────────────
# Gantt diagram builder from tasks
# ─────────────────────────────────────────────────────────────────────────────
def _build_gantt(tasks: list, ctx: ContextStore) -> str:
    if not tasks:
        return ""

    date_debut = ctx.get("date_debut", "09/02/2026")
    date_fin   = ctx.get("date_fin",   "14/06/2026")

    # Parse months/weeks from dates
    try:
        parts_d = date_debut.split("/")
        parts_f = date_fin.split("/")
        month_start = int(parts_d[1])
        month_end   = int(parts_f[1])
        year = parts_d[2] if len(parts_d) > 2 else "2025"
        total_weeks = max((month_end - month_start + 1) * 4, len(tasks) * 2)
    except Exception:
        total_weeks = max(len(tasks) * 2, 8)
        month_start = 7
        year = "2025"

    MONTH_NAMES = {1:"Janvier",2:"Février",3:"Mars",4:"Avril",5:"Mai",6:"Juin",
                   7:"Juillet",8:"Août",9:"Septembre",10:"Octobre",11:"Novembre",12:"Décembre"}

    # Build gantt bars
    bars = []
    week_cursor = 1
    for i, task in enumerate(tasks[:12]):  # max 12 tasks
        title = tex(task.get("title", f"Tâche {i+1}")[:40])
        duration = max(task.get("duration_weeks", 2), 1)
        end_week = min(week_cursor + duration - 1, total_weeks)
        bars.append(rf"  \ganttbar{{{title}}}{{{week_cursor}}}{{{end_week}}} \\")
        week_cursor = end_week + 1
        if week_cursor > total_weeks:
            week_cursor = total_weeks

    bars_str = "\n".join(bars)

    # Month labels
    month_labels = []
    w = 1
    for m_offset in range(month_end - month_start + 1):
        m = month_start + m_offset
        mname = MONTH_NAMES.get(m, f"M{m}")
        month_labels.append(rf"  \gantttitle{{{mname} {year}}}{{4}}")
        if w + 4 > total_weeks:
            break
        w += 4
    months_str = "\n".join(month_labels)

    # Week labels
    week_labels = " ".join(rf"\gantttitle{{S{i+1}}}{{1}}" for i in range(total_weeks))

    return rf"""
\subsection{{Planification du projet}}

\hspace{{10pt}}Le diagramme de Gantt ci-dessous illustre la planification globale du projet,
répartissant les différentes phases de développement selon une approche progressive et itérative.

\begin{{figure}}[H]
\centering
\begin{{sideways}}
\begin{{ganttchart}}[
  hgrid,
  vgrid,
  title height=1,
  bar height=0.6,
  bar label font=\small,
  title label font=\small\bfseries,
  x unit=0.85cm,
  y unit title=0.6cm,
  y unit chart=0.7cm,
]{{{1}}}{{{total_weeks}}}
  \gantttitle{{\textbf{{Planification du Projet}}}}{{{total_weeks}}} \\
{months_str} \\
  {week_labels} \\
{bars_str}
\end{{ganttchart}}
\end{{sideways}}
\caption{{Diagramme de Gantt du projet}}
\label{{fig:gantt}}
\end{{figure}}
"""


# ─────────────────────────────────────────────────────────────────────────────
# Main builder class
# ─────────────────────────────────────────────────────────────────────────────
class LaTeXBuilder:

    def build_project(self, sections: dict, ctx: ContextStore) -> dict[str, str]:
        """
        Returns {relative_path: content} for every file in the LaTeX project.
        """
        technologies = ctx.get("confirmed_technologies", [])
        refs         = ctx.get("references", [])
        tasks        = ctx.get("tasks", [])

        # Inject tasks into context for Gantt
        if tasks:
            ctx.update("tasks", tasks)

        files = {}

        # ── Root files ──────────────────────────────────────────────────────
        files["main.tex"]        = build_main()
        files["title.tex"]       = build_title(ctx)
        files["References.bib"]  = build_references_bib(refs)

        # ── Front matter ─────────────────────────────────────────────────────
        files["Chapters/Remerciement.tex"] = build_remerciement(ctx)
        files["Chapters/Résumé.tex"]       = build_resume(sections.get("resume_fr", ""), ctx)
        files["Chapters/Abstract.tex"]     = build_abstract(sections.get("resume_en", ""), ctx)
        files["Chapters/ResumeArabe.tex"]  = build_resume_arabe()

        # ── Introduction ─────────────────────────────────────────────────────
        files["Chapters/Introduction.tex"] = build_introduction(sections.get("introduction_generale", ""))

        # ── Chapters ─────────────────────────────────────────────────────────
        chapter_map = {
            1: ("chapitre1_contexte",    "Contexte Général"),
            2: ("chapitre2_analyse",     "Analyse et Conception"),
            3: ("chapitre3_etat_art",    "État de l'Art"),
            4: ("chapitre4_outils",      "Outils et Technologies"),
            5: ("chapitre5_realisation", "Conception et Implémentation"),
        }

        for n, (key, title) in chapter_map.items():
            # CH{n}.tex — full-page title
            files[f"Chapters/CH{n}.tex"] = build_ch_title(n, title)

            # Chapitre{n}.tex — content
            content = sections.get(key, "")

            # Chapter 4: inject tech subsections if we have confirmed technologies
            if n == 4 and technologies:
                tech_tex = build_tech_subsections(technologies)
                content = _inject_tech_into_ch4(content, tech_tex)

            files[f"Chapters/Chapitre{n}.tex"] = build_chapter_content(n, content, ctx if n == 1 else None)

        # ── Back matter ──────────────────────────────────────────────────────
        files["Chapters/Conclusion.tex"]   = build_conclusion(sections.get("conclusion_generale", ""))
        files["Chapters/Perspectives.tex"] = build_perspectives(sections.get("perspectives", ""))
        files["Chapters/References.tex"]   = build_references_file(refs)

        # ── Placeholder dirs ─────────────────────────────────────────────────
        files["logo/.gitkeep"]    = "% Place Logo_ENSA.jpg and company logo here\n"
        files["screens/.gitkeep"] = "% Place your screenshot images here\n"

        return files

    def build(self, _sections: dict, _ctx: ContextStore) -> str:
        """Fallback: return main.tex for MCP single-file compile."""
        return build_main()


# ─────────────────────────────────────────────────────────────────────────────
# Markdown → LaTeX converter (removes all MD formatting)
# ─────────────────────────────────────────────────────────────────────────────
def _md_to_latex(text: str) -> str:
    """Convert markdown-formatted LLM output to clean LaTeX."""
    if not text:
        return ""

    lines = text.split("\n")
    out   = []
    i     = 0

    while i < len(lines):
        line = lines[i]

        # ── Headings → \section / \subsection / \subsubsection ──────────────
        heading_match = HEADING_RE.match(line)
        if heading_match:
            depth = len(line) - len(line.lstrip("#"))
            out.append(_render_heading(depth, heading_match.group(1).strip()))
            i += 1
            continue

        line = _format_inline_markdown(line)

        # ── Bullet lists: - item or * item ───────────────────────────────────
        if BULLET_RE.match(line):
            block, next_index = _consume_bullet_list(lines, i)
            out.extend(block)
            i = next_index
            continue

        # ── Numbered lists: 1. item ────────────────────────────────────────
        if NUMBERED_RE.match(line):
            block, next_index = _consume_numbered_list(lines, i)
            out.extend(block)
            i = next_index
            continue

        # ── Horizontal rule ---  ──────────────────────────────────────────────
        if HR_RE.match(line.strip()):
            out.append("\\hrule\n")
            i += 1
            continue

        # ── Empty line → paragraph break ─────────────────────────────────────
        if line.strip() == "":
            out.append("")
            i += 1
            continue

        # ── Regular paragraph line with indentation ─────────────────────────
        out.append(f"\\hspace{{10pt}}{tex(line)}")
        i += 1

    return "\n".join(out)


def _render_heading(depth: int, heading: str) -> str:
    latex_heading = tex(heading)
    if depth == 1:
        return f"\n\\section{{{latex_heading}}}\n"
    if depth == 2:
        return f"\n\\subsection{{{latex_heading}}}\n"
    if depth == 3:
        return f"\n\\subsubsection{{{latex_heading}}}\n"
    return f"\n\\paragraph{{{latex_heading}}}\n"


def _format_inline_markdown(line: str) -> str:
    line = BOLD_RE.sub(lambda m: f"\\textbf{{{tex(m.group(1))}}}", line)
    line = ITALIC_RE.sub(lambda m: f"\\textit{{{tex(m.group(1))}}}", line)
    line = INLINE_CODE_RE.sub(lambda m: f"\\texttt{{{m.group(1)}}}", line)
    return line


def _consume_bullet_list(lines: list[str], start_index: int) -> tuple[list[str], int]:
    block = ["\\begin{itemize}"]
    i = start_index
    while i < len(lines) and BULLET_RE.match(lines[i]):
        item = BULLET_RE.sub("", lines[i], count=1)
        item = _format_inline_markdown(item)
        block.append(f"  \\item {tex(item)}")
        i += 1
    block.append("\\end{itemize}\n")
    return block, i


def _consume_numbered_list(lines: list[str], start_index: int) -> tuple[list[str], int]:
    block = ["\\begin{enumerate}"]
    i = start_index
    while i < len(lines) and NUMBERED_RE.match(lines[i]):
        item = NUMBERED_RE.sub("", lines[i], count=1)
        item = _format_inline_markdown(item)
        block.append(f"  \\item {tex(item)}")
        i += 1
    block.append("\\end{enumerate}\n")
    return block, i


def _sanitize_empty_lists(text: str) -> str:
    text = re.sub(r"\\begin\{itemize\}\s*\\end\{itemize\}", "", text, flags=re.DOTALL)
    text = re.sub(r"\\begin\{enumerate\}\s*\\end\{enumerate\}", "", text, flags=re.DOTALL)
    return text


def _inject_tech_into_ch4(content: str, tech_tex: str) -> str:
    """Insert logo-bearing tech subsections into chapter 4 content."""
    # Find the section about technology descriptions and inject after
    marker = "justification"
    if marker.lower() in content.lower():
        # Split at the section and inject
        idx = content.lower().find(marker)
        # Find end of that paragraph
        para_end = content.find("\n\n", idx)
        if para_end > 0:
            return content[:para_end] + "\n\n" + tech_tex + content[para_end:]
    return content + "\n\n" + tech_tex


# ─────────────────────────────────────────────────────────────────────────────
# LaTeX special character escaping
# ─────────────────────────────────────────────────────────────────────────────
def tex(text) -> str:
    if not text:
        return ""
    text = str(text)
    # Don't double-escape already escaped content when the string is a full LaTeX command/block.
    stripped = text.strip()
    if stripped.startswith(("\\textbf{", "\\section{", "\\subsection{", "\\subsubsection{", "\\begin{", "\\end{", "\\item ")):
        return text
    replacements = [
        ("\\", "\\textbackslash{}"),
        ("&",  "\\&"),
        ("%",  "\\%"),
        ("$",  "\\$"),
        ("#",  "\\#"),
        ("_",  "\\_"),
        ("^",  "\\^{}"),
        ("{",  "\\{"),
        ("}",  "\\}"),
        ("~",  "\\~{}"),
        ("<",  "\\textless{}"),
        (">",  "\\textgreater{}"),
    ]
    # Fix double-escaped backslash from first replacement
    for old, new in replacements[1:]:
        text = text.replace(old, new)
    return text

# Alias used across files
tex_escape = tex