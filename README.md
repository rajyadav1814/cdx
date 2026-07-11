# CDX — Commercial Signal Intelligence Engine (CSIE)

**Chromadata × Sony Music Latin**`

## What this project is

CDX is a proof-of-concept analytics and AI agent platform built by Chromadata for Sony Music Latin. It is called the **Commercial Signal Intelligence Engine (CSIE)**. It ingests music industry data signals, computes deterministic scores, and runs four sequential AI agents that transform raw data into explainable commercial recommendations for brand partnership decisions.

The platform is a local-first POC running entirely on the developer's MacBook. No cloud deployment in scope. No production database — CSV files are used throughout instead of PostgreSQL.

## Project root

`~/cdx/`

All instructions, file paths, and commands use this as the root. Do NOT rename this folder during development.

## Tech stack

### Backend (Python)

- Python 3.10+ inside virtualenv at `~/cdx/venv/`
- `anthropic` SDK — Anthropic API calls
- `openai` SDK — OpenAI API calls
- `pandas` — CSV read/write and data manipulation
- `faker` — supplemental fake data generation
- `playwright` — Kworb.net chart scraping during data generation
- `python-dotenv` — load `.env` file
- `http.server` (stdlib) — Python API server on port 8000
- `model_router.py` — unified LLM call router (Anthropic + OpenAI)

### Frontend (React)

- React 18 + Vite — app at `~/cdx/web/`
- Tailwind CSS v3 — utility-first styling (dark theme only)
- shadcn/ui — pre-built accessible components
- Recharts — data visualization charts
- TanStack Query — server state, caching, polling
- `lucide-react` — icons
- Vite dev server: port 5173
- Vite proxy: `/api/*` → `http://localhost:8000`

### Design system

- Theme: HumanX.co-inspired dark editorial
- Backgrounds: `#05050A` (base) / `#0D0D18` (surface) / `#12121F` (surface2)
- Brand red: `#CC1B1B` (Chromadata primary)
- Brand gold: `#D4A017` (Sony Music Latin accent)
- Font display: Satoshi (bold/black weights — geometric grotesque)
- Font body: DM Sans (400/500)
- Font mono: JetBrains Mono (scores, KPIs, data values)
- Borders: ultra-thin 1px `rgba(255,255,255,0.06)`
- Corners: 2px radius (angular, not rounded)
- NO light mode, NO gradients on surfaces, NO decorative shadows

## Environment variables (.env)

```
ANTHROPIC_API_KEY=...        ← from console.anthropic.com
OPENAI_API_KEY=...           ← from platform.openai.com/api-keys
PORT=8000
DATA_DIR=./data
DEFAULT_AGENT_MODEL=claude-sonnet-4-6
DEFAULT_AGENT_PROVIDER=anthropic
```

At least one API key must be set. The app works with either or both. The model selector in the chat UI only shows providers with keys set.

## How to run

### Development (two terminals, hot reload)

```bash
Terminal 1: bash dev.sh backend     ← Python API server on :8000
Terminal 2: bash dev.sh frontend    ← React dev server on :5173
Browser:    http://localhost:5173
```

### Production / demo (single server)

```bash
bash dev.sh build     ← builds React into web/dist/
bash launch.sh        ← starts Python server serving web/dist/ + API
Browser: http://localhost:8000
```

### Individual commands

```bash
bash dev.sh data      ← regenerate all 7 CSVs + scores
                        (runs Playwright Kworb scrape + falls back gracefully)
bash dev.sh scores    ← re-run scoring engine only
bash dev.sh agents    ← re-run all 4 agents (calls AI APIs)
bash dev.sh agent1    ← re-run Agent 1 only
bash dev.sh agent2    ← re-run Agent 2 only
bash dev.sh agent3    ← re-run Agent 3 only
bash dev.sh agent4    ← re-run Agent 4 only
bash dev.sh models    ← print available models from .env + models.json
```

## The four agents — execution order and dependencies

`Agent 1 → Agent 2 → Agent 3 → Agent 4`

Each agent MUST run in this order. Agent N depends on Agent N-1 output.

- Agent 1 reads: data CSVs + `scores_weekly.csv`
- Agent 2 reads: `agent1_output.csv` + data CSVs
- Agent 3 reads: `agent2_output.csv` + data CSVs
- Agent 4 reads: `agent3_output.csv` + data CSVs (including `client_campaigns.csv`)

### Core design rule — DO NOT VIOLATE

The LLM never invents or calculates numbers. ALL scores and financial figures are computed deterministically in Python/SQL BEFORE the LLM is called. The LLM receives pre-computed scores as JSON and writes human-readable narratives interpreting that evidence.

**WRONG:** asking the LLM to calculate ROI or score artists
**RIGHT:** calculating ROI in Python, then asking the LLM to explain it

### Agent identities

- Agent 1: Opportunity Discovery — "Where to Play" — finds emerging artists
- Agent 2: Strategy Synthesis — "How to Play" — brand-artist fit briefs
- Agent 3: Audience-Fit — "Who to Play With" — audience profiling
- Agent 4: ROI Forecast — "Is It Worth It?" — investment scenarios
