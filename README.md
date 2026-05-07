# 🎓 PFE Report AI Agent — ENSA Marrakech

An end-to-end AI agent that generates a complete, standards-compliant PFE report in **LaTeX/PDF**, following the official ENSA Marrakech guide.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Browser (port 3000)                       │
│               React-like Wizard Frontend                     │
└──────────────────────┬──────────────────────────────────────┘
                       │ REST (HTTP)
┌──────────────────────▼──────────────────────────────────────┐
│              AI Agent — FastAPI (port 8000)                  │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │ Orchestrator│  │  LLM Client  │  │  Context Store   │   │
│  │  (flow ctrl)│→ │ (OpenAI API) │  │  (PFE data)      │   │
│  └─────────────┘  └──────────────┘  └──────────────────┘   │
│         │              ↑ prompts/sections                    │
│         └──────── LaTeX Builder ──────────────────────┐     │
└───────────────────────────────────────────────────────┼─────┘
                                                         │ MCP (JSON-RPC)
┌────────────────────────────────────────────────────────▼────┐
│              MCP Server — Overleaf Tool (port 8001)          │
│   write_tex_file  │  compile_latex  │  read_log              │
│                  pdflatex / TeXLive                          │
│                  /workspace/*.tex, *.pdf                     │
└─────────────────────────────────────────────────────────────┘
```

---

## 📦 Services

| Service       | Port | Description                              |
|---------------|------|------------------------------------------|
| `frontend`    | 3000 | Web UI — multi-step wizard               |
| `agent`       | 8000 | FastAPI — orchestration + LLM calls      |
| `mcp-server`  | 8001 | MCP tool — LaTeX compilation engine      |

---

## 🚀 Quick Start

### 1. Clone & configure

```bash
git clone https://github.com/your-repo/pfe-agent
cd pfe-agent
cp .env.example .env
# Edit .env and set your OPENAI_API_KEY
```

### 2. Launch with Docker Compose

```bash
docker-compose up --build
```

> ⚠️ First build downloads ~3GB TeXLive — grab a coffee ☕

### 3. Open the UI

```
http://localhost:3000
```

Fill in the 5-step wizard and click **⚡ Générer le rapport**.

---

## 🔧 LLM Provider

The agent uses an OpenAI-compatible API. You can swap providers via `.env`:

```env
# OpenAI (default)
OPENAI_API_KEY=sk-...
LLM_MODEL=gpt-4o

# Anthropic Claude
OPENAI_BASE_URL=https://api.anthropic.com/v1/
LLM_MODEL=claude-sonnet-4-20250514

# Mistral
OPENAI_BASE_URL=https://api.mistral.ai/v1
LLM_MODEL=mistral-large-latest

# Ollama (local/free)
OPENAI_BASE_URL=http://host.docker.internal:11434/v1
LLM_MODEL=mistral:7b
```

---

## 📋 Report Structure Generated

Following the official ENSA Marrakech PFE guide (max 80 pages):

| Section | Pages | Status |
|---------|-------|--------|
| Page de garde | 1 | ✅ Auto |
| Résumé FR / EN / AR | 3 | ✅ AI |
| Table des matières | 2 | ✅ Auto |
| Liste figures/tables | 1 | ✅ Auto |
| Introduction générale | ≤3 | ✅ AI |
| Chapitre 1 — Organisme & stage | ~15 | ✅ AI |
| Chapitre 2 — Bibliographie | ~22 | ✅ AI |
| Chapitre 3 — Réalisation | ~22 | ✅ AI |
| Conclusion & perspectives | ≤3 | ✅ AI |
| Références bibliographiques | 1–2 | ✅ Auto |
| Glossaire des acronymes | 1–5 | ✅ AI |

---

## 🔌 MCP Tools Available

| Tool | Description |
|------|-------------|
| `write_tex_file` | Write `.tex` content to workspace |
| `compile_latex` | Run pdflatex (2 passes), return PDF path or errors |
| `list_files` | List workspace files |
| `read_log` | Read the LaTeX compilation log |

---

## 📡 API Endpoints

### Agent (port 8000)

```
GET  /health              — Health check
POST /generate            — Start a generation job
GET  /jobs/{id}           — Poll job status + progress
GET  /jobs/{id}/tex       — Get generated .tex
```

### MCP Server (port 8001)

```
POST /mcp                 — JSON-RPC 2.0 endpoint
GET  /pdf/{filename}      — Download compiled PDF
GET  /health              — Health check
```

---

## 🛠️ Development

Run services individually:

```bash
# Agent only
cd pfe-agent
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# MCP Server only
cd mcp-server
pip install -r requirements.txt
uvicorn server:app --reload --port 8001

# Frontend
cd frontend
python -m http.server 3000
```

---

## 📁 Project Structure

```
pfe-agent/
├── agent/
│   ├── __init__.py
│   ├── orchestrator.py      # Flow controller
│   ├── llm_client.py        # LLM + section prompts
│   ├── context_store.py     # PFE data container
│   ├── latex_builder.py     # .tex document assembler
│   ├── mcp_client.py        # MCP protocol client
│   └── sections.py          # Section registry
├── mcp-server/
│   ├── server.py            # MCP tool server
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── index.html           # Full SPA wizard
│   ├── nginx.conf
│   └── Dockerfile
├── main.py                  # FastAPI entrypoint
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── .env.example
```

---

## 📐 LaTeX Formatting (ENSA Standard)

- **Marges** : 2.5cm haut/bas/gauche/droite ✅
- **Police** : TeX Gyre Heros (≈ Trebuchet MS) ✅
- **Taille texte** : 12pt obligatoire ✅
- **Interligne** : simple ✅
- **Titres** : gras 20/14/13pt selon niveau ✅
- **Équations** : numérotées automatiquement ✅
- **Légendes** : gras 10pt en bas ✅
- **Pagination** : continue bas-droite ✅
- **Numérotation** : scientifique 3 niveaux ✅
