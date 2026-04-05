# CLAUDE.md — CDX Project
# Chromadata × Sony Music Latin
# Commercial Signal Intelligence Engine (CSIE)
# ─────────────────────────────────────────────

## What this project is

CDX is a proof-of-concept analytics and AI agent platform built by
Chromadata for Sony Music Latin. It is called the **Commercial Signal
Intelligence Engine (CSIE)**. It ingests music industry data signals,
computes deterministic scores, and runs four sequential AI agents that
transform raw data into explainable commercial recommendations for brand
partnership decisions.

The platform is a local-first POC running entirely on the developer's
MacBook. No cloud deployment in scope. No production database — CSV files
are used throughout instead of PostgreSQL.

---

## Project root

  ~/cdx/

All instructions, file paths, and commands use this as the root.
Do NOT rename this folder during development.

---

## Tech stack

### Backend (Python)
  - Python 3.10+ inside virtualenv at ~/cdx/venv/
  - anthropic SDK — Anthropic API calls
  - openai SDK — OpenAI API calls
  - pandas — CSV read/write and data manipulation
  - faker — supplemental fake data generation
  - playwright — Kworb.net chart scraping during data generation
  - python-dotenv — load .env file
  - http.server (stdlib) — Python API server on port 8000
  - model_router.py — unified LLM call router (Anthropic + OpenAI)

### Frontend (React)
  - React 18 + Vite — app at ~/cdx/web/
  - Tailwind CSS v3 — utility-first styling (dark theme only)
  - shadcn/ui — pre-built accessible components
  - Recharts — data visualization charts
  - TanStack Query — server state, caching, polling
  - lucide-react — icons
  - Vite dev server: port 5173
  - Vite proxy: /api/* → http://localhost:8000

### Design system
  - Theme: HumanX.co-inspired dark editorial
  - Backgrounds: #05050A (base) / #0D0D18 (surface) / #12121F (surface2)
  - Brand red: #CC1B1B (Chromadata primary)
  - Brand gold: #D4A017 (Sony Music Latin accent)
  - Font display: Satoshi (bold/black weights — geometric grotesque)
  - Font body: DM Sans (400/500)
  - Font mono: JetBrains Mono (scores, KPIs, data values)
  - Borders: ultra-thin 1px rgba(255,255,255,0.06)
  - Corners: 2px radius (angular, not rounded)
  - NO light mode, NO gradients on surfaces, NO decorative shadows

---

## Directory structure

  ~/cdx/
  ├── .env                     ← API keys and config (never commit)
  ├── .gitignore
  ├── CLAUDE.md                ← this file
  ├── README.md
  ├── requirements.txt
  ├── models.json              ← Anthropic + OpenAI model registry
  ├── model_router.py          ← unified call_llm() for all agents
  ├── launch.sh                ← production: build React + start server
  ├── dev.sh                   ← development shortcuts
  │
  ├── data/
  │   ├── generate_data.py     ← creates all 7 sample CSVs
  │   │                           scrapes Kworb live (falls back gracefully)
  │   ├── README.md            ← CSV data dictionary
  │   ├── artists.csv          ← 100 artists (real Latin names from Kworb)
  │   ├── spotify_charts.csv   ← 300 chart rows (5 weeks × 8 territories)
  │   ├── kworb_crosschart.csv ← 100 cross-platform chart rows
  │   ├── social_blade_growth.csv ← 200 social growth rows (2 per artist)
  │   ├── media_mentions.csv   ← 150 press/RSS mentions with sentiment
  │   ├── audience_segments.csv ← 200 segment rows (2 markets per artist)
  │   ├── client_campaigns.csv ← 50 historical campaign ROI rows
  │   ├── scores_weekly.csv    ← output of scoring engine
  │   ├── agent1_output.csv    ← output of Agent 1
  │   ├── agent2_output.csv    ← output of Agent 2
  │   ├── agent3_output.csv    ← output of Agent 3
  │   ├── agent4_output.csv    ← output of Agent 4
  │   ├── roi_scenarios_detail.csv ← 3 rows per artist (conservative/base/optimistic)
  │   └── pipeline_summary.json ← run metadata for overview panel
  │
  ├── scores/
  │   └── scoring_engine.py    ← reads CSVs, writes scores_weekly.csv
  │
  ├── agents/
  │   ├── agent1_opportunity.py  ← Opportunity Discovery — Where to Play
  │   ├── agent2_strategy.py     ← Strategy Synthesis — How to Play
  │   ├── agent3_audience.py     ← Audience-Fit — Who to Play With
  │   ├── agent4_roi.py          ← ROI Forecast — Is It Worth It?
  │   └── run_all_agents.py      ← orchestrates agents 1→2→3→4 in sequence
  │
  └── web/
      ├── vite.config.js
      ├── tailwind.config.js
      ├── package.json
      ├── public/
      │   ├── brand/             ← Chromadata logo files go here
      │   │   ├── chromadata-logo.svg   (full logo — provide this file)
      │   │   ├── chromadata-logo.png   (PNG fallback)
      │   │   ├── chromadata-icon.svg   (icon only — provide this file)
      │   │   └── chromadata-icon.png   (PNG fallback)
      │   └── fonts/             ← Satoshi font files (.woff2/.woff)
      └── src/
          ├── main.jsx
          ├── App.jsx
          ├── index.css
          ├── lib/
          │   ├── utils.js       ← cn() helper
          │   ├── api.js         ← all /api/* fetch calls
          │   └── constants.js   ← AGENTS config, AGENT_SUGGESTIONS
          ├── components/
          │   ├── layout/
          │   │   ├── Header.jsx
          │   │   ├── WorkflowBanner.jsx
          │   │   └── AppShell.jsx
          │   ├── shared/
          │   │   ├── LogoImage.jsx    ← logo with onError fallback to "CD"
          │   │   ├── LogoIcon.jsx     ← icon with onError fallback
          │   │   ├── KpiCard.jsx
          │   │   ├── AgentBadge.jsx
          │   │   ├── StatusDot.jsx
          │   │   ├── EmptyState.jsx
          │   │   ├── SkeletonPanel.jsx
          │   │   └── SectionLabel.jsx
          │   ├── chat/
          │   │   ├── ChatPanel.jsx
          │   │   ├── MessageBubble.jsx
          │   │   ├── ModelSelector.jsx
          │   │   ├── SuggestedQuestions.jsx
          │   │   └── TypingIndicator.jsx
          │   └── ui/             ← shadcn generated components
          ├── hooks/
          │   ├── useChat.js      ← conversation state per agent
          │   ├── useModels.js    ← model selection + localStorage
          │   └── usePipeline.js  ← pipeline run + status polling
          └── panels/
              ├── OverviewPanel.jsx
              ├── Agent1Panel.jsx
              ├── Agent2Panel.jsx
              ├── Agent3Panel.jsx
              ├── Agent4Panel.jsx
              └── analytics/
                  ├── Agent2Analytics.jsx
                  ├── Agent3Analytics.jsx
                  └── Agent4Analytics.jsx

---

## Environment variables (.env)

  ANTHROPIC_API_KEY=...        ← from console.anthropic.com
  OPENAI_API_KEY=...           ← from platform.openai.com/api-keys
  PORT=8000
  DATA_DIR=./data
  DEFAULT_AGENT_MODEL=claude-sonnet-4-6
  DEFAULT_AGENT_PROVIDER=anthropic

At least one API key must be set. The app works with either or both.
The model selector in the chat UI only shows providers with keys set.

---

## How to run

### Development (two terminals, hot reload)
  Terminal 1: bash dev.sh backend     ← Python API server on :8000
  Terminal 2: bash dev.sh frontend    ← React dev server on :5173
  Browser:    http://localhost:5173

### Production / demo (single server)
  bash dev.sh build     ← builds React into web/dist/
  bash launch.sh        ← starts Python server serving web/dist/ + API
  Browser: http://localhost:8000

### Individual commands
  bash dev.sh data      ← regenerate all 7 CSVs + scores
                          (runs Playwright Kworb scrape + falls back gracefully)
  bash dev.sh scores    ← re-run scoring engine only
  bash dev.sh agents    ← re-run all 4 agents (calls AI APIs)
  bash dev.sh agent1    ← re-run Agent 1 only
  bash dev.sh agent2    ← re-run Agent 2 only
  bash dev.sh agent3    ← re-run Agent 3 only
  bash dev.sh agent4    ← re-run Agent 4 only
  bash dev.sh models    ← print available models from .env + models.json

---

## The four agents — execution order and dependencies

  Agent 1 → Agent 2 → Agent 3 → Agent 4

  Each agent MUST run in this order. Agent N depends on Agent N-1 output.
  Agent 1 reads:  data CSVs + scores_weekly.csv
  Agent 2 reads:  agent1_output.csv + data CSVs
  Agent 3 reads:  agent2_output.csv + data CSVs
  Agent 4 reads:  agent3_output.csv + data CSVs (including client_campaigns.csv)

### Core design rule — DO NOT VIOLATE
  The LLM never invents or calculates numbers. ALL scores and financial
  figures are computed deterministically in Python/SQL BEFORE the LLM
  is called. The LLM receives pre-computed scores as JSON and writes
  human-readable narratives interpreting that evidence.

  WRONG: asking the LLM to calculate ROI or score artists
  RIGHT: calculating ROI in Python, then asking the LLM to explain it

### Agent identities
  Agent 1: Opportunity Discovery  — "Where to Play" — finds emerging artists
  Agent 2: Strategy Synthesis     — "How to Play" — brand-artist fit briefs
  Agent 3: Audience-Fit          — "Who to Play With" — audience profiling
  Agent 4: ROI Forecast          — "Is It Worth It?" — investment scenarios

---

## Sample data — important notes

  Artists: 100 real Latin music artists sourced from Kworb.net Spotify
  charts (MX, CO, AR, ES, BR territories, early 2026). Names, genres,
  and track titles are real. All streaming numbers, social metrics,
  audience demographics, and campaign financials are SIMULATED.

  The data generator (data/generate_data.py) attempts a live Playwright
  scrape of Kworb at runtime to embed current chart positions. If Kworb
  is unreachable, it falls back to hardcoded reference data silently.
  Either way all 7 CSVs are produced with correct schemas.

  Data volumes:
    artists.csv              100 rows
    spotify_charts.csv       300 rows
    kworb_crosschart.csv     100 rows
    social_blade_growth.csv  200 rows
    media_mentions.csv       150 rows
    audience_segments.csv    200 rows
    client_campaigns.csv      50 rows

  Disclaimer (also in data/README.md):
  "Artist names are real public figures from Kworb Latin charts.
   All financial, streaming, social, and campaign metrics are
   simulated and do not represent actual commercial relationships,
   endorsements, or real data from any artist, brand, or label."

---

## Model routing

  model_router.py provides a single call_llm() function used everywhere.
  It routes to anthropic or openai based on the model_id passed in.
  All 4 agents use call_llm(). All 3 chat endpoints use call_llm().

  Available models are defined in models.json at the project root.
  The frontend fetches GET /api/models to know which are available.
  Model selection per chat agent is persisted in localStorage.

  Key edge case: o1 models (OpenAI) don't accept system messages.
  model_router.py handles this automatically by merging system
  prompt into the first user message. No code changes needed elsewhere.

---

## API server endpoints

  GET  /api/models           ← available providers/models from .env
  GET  /api/summary          ← pipeline_summary.json (or empty defaults)
  GET  /api/agent1           ← agent1_output.csv as JSON array
  GET  /api/agent2           ← agent2_output.csv as JSON array
  GET  /api/agent3           ← agent3_output.csv as JSON array
  GET  /api/agent4           ← agent4_output.csv as JSON array
  GET  /api/roi_scenarios    ← roi_scenarios_detail.csv as JSON array
  GET  /api/pipeline_status  ← {status: running|complete|idle}
  POST /api/run_pipeline     ← triggers run_all_agents.py as subprocess
  POST /api/chat/agent2      ← conversational chat for Agent 2
  POST /api/chat/agent3      ← conversational chat for Agent 3
  POST /api/chat/agent4      ← conversational chat for Agent 4
  GET  /api/chat/clear       ← clear session history by session_id

  Missing CSV files return [] not a 500 error.
  Chat errors return HTTP 200 with an error message in the reply field
  (never a 500 — the UI must always get a displayable message).

---

## Chat agents (Agents 2, 3, 4 only)

  Agent 1 is analytics-only — NO chat interface.
  Agents 2, 3, 4 have a split-panel layout:
    LEFT 38%:  ChatPanel (model selector + message thread + input)
    RIGHT 62%: Analytics panel (charts, tables, cards)

  Chat state management:
    session_id: stored in sessionStorage (per-tab, resets on tab close)
    model_id:   stored in localStorage (persists across sessions)
    history:    stored server-side in-memory dict (keyed by session_id)
    artist filter: stored in React state, passed to API on each message

  Context injection: each chat call injects the full agent output CSV
  as a JSON block into the system prompt so the LLM has all data.
  If artist_filter is set, only that artist's rows are injected.

  Cross-agent navigation:
    Agent 2 chat → "View Audience-Fit →" → Agent 3
    Agent 3 chat → "View ROI Forecast →" → Agent 4
    Agent 4 chat → "← Back to overview"   → Overview
    Artist filter carries over between agents via sessionStorage.

---

## Data pipeline — what generates what

  generate_data.py    →  7 source CSVs in data/
                          (Playwright scrapes Kworb, falls back to hardcoded)
  scoring_engine.py   →  data/scores_weekly.csv
  agent1_opportunity  →  data/agent1_output.csv
  agent2_strategy     →  data/agent2_output.csv
  agent3_audience     →  data/agent3_output.csv
  agent4_roi          →  data/agent4_output.csv
                         data/roi_scenarios_detail.csv
  run_all_agents.py   →  data/pipeline_summary.json

  All files must exist before the web app will show data.
  Missing files return [] from API — not an error — just empty state.

---

## Design rules — enforce these throughout

  1. BACKGROUNDS: Use only these values — never use gray-800, gray-900
     or any Tailwind dark gray. Always use:
       bg-bg-base     (#05050A)  — page background
       bg-bg-surface  (#0D0D18)  — cards, panels
       bg-bg-surface2 (#12121F)  — hover, elevated
       bg-bg-surface3 (#1A1A2E)  — dropdowns, tooltips

  2. TYPOGRAPHY: Headlines and labels use Satoshi (font-display class).
     Body text uses DM Sans (font-sans). Numbers/scores use JetBrains Mono
     (font-mono). Never use Inter, system-ui alone, or Arial.

  3. BORDERS: Always 1px, always rgba(255,255,255,0.06) to 0.18.
     Never use Tailwind's border-gray-* colors.

  4. CORNERS: borderRadius 2px everywhere except large containers (4px).
     Never use rounded-lg (8px) or rounded-xl (12px) — too soft.

  5. AGENT COLORS: Use only the defined agent colors:
       Agent 1: #1D9E75   Agent 2: #8B7FE8
       Agent 3: #4A9EE8   Agent 4: #D4924A
     Never use generic Tailwind green/purple/blue/yellow.

  6. NO LIGHT MODE: html has class="dark" permanently. Do not add
     any light mode variants or toggle functionality.

  7. LOGO: LogoImage and LogoIcon components handle file detection
     automatically via onError. Never hardcode logo paths directly.
     If /brand/chromadata-logo.svg exists it shows. If not, "CD" fallback
     shows. DO NOT add conditional logic elsewhere for logo display.

  8. LLM RULE: Never ask any LLM to calculate, score, or estimate a
     number. Only ask it to interpret and narrate pre-computed data.

  9. EMPTY STATES: Every panel and table must handle empty data
     gracefully with an <EmptyState> component. Never render an
     empty table or blank panel.

  10. ERROR STATES: Network errors show a red-bordered card with retry
      button. Never let an uncaught error produce a blank screen.
      Wrap all panels in <ErrorBoundary>.

---

## Naming conventions

  Engine name:   Commercial Signal Intelligence Engine (CSIE)
  Company:       Chromadata
  Client:        Sony Music Latin / Sony Music Latin Region
  Project root:  cdx  (~/cdx/)
  Agents:        Agent 1, Agent 2, Agent 3, Agent 4
                 (never "agent_1", always "agent1" in code identifiers)
  CSV files:     snake_case, descriptive (agent1_output.csv)
  React files:   PascalCase components, camelCase hooks/utils
  Python files:  snake_case throughout
  CSS classes:   Tailwind utilities only — no custom CSS except
                 what is defined in index.css @layer components

  DO NOT refer to "Altempo" anywhere in the codebase.
  The client is always "Sony Music Latin" or "the client".

---

## Build sequence — prompts to run in order

  PROMPT 0  — Mac setup (Python venv, React/Vite, Tailwind, Satoshi font)
  PROMPT 1  — Sample data generation
               (100 real artists, 5× volume, Playwright Kworb scrape)
  PROMPT 2  — Scoring engine (scores_weekly.csv)
  PROMPT 3  — Agent 1: Opportunity Discovery
  PROMPT 4  — Agent 2: Strategy Synthesis
  PROMPT 5  — Agent 3: Audience-Fit
  PROMPT 6  — Agent 4: ROI Forecast
  PROMPT 7  — Agent orchestrator + run_all_agents.py
  PROMPT 8  — React app shell + workflow banner (HumanX design)
  PROMPT 9  — Python API server (web/server.py)
  PROMPT 10 — Agent 1 panel (full-width analytics)
  PROMPT 11A— Chat API endpoints (server.py update)
  PROMPT 11B— Split-panel chat UI (ChatPanel, ModelSelector, useChat)
  PROMPT 11C— Artist → chat deep linking + cross-agent navigation
  PROMPT 12 — Overview dashboard + pipeline polling
  PROMPT 13 — Final integration, production build, launch test

  Each prompt builds one logical piece. Run them strictly in order.
  Do not skip ahead. Verify each prompt compiles before moving on.

  Before Prompt 3: set ANTHROPIC_API_KEY and/or OPENAI_API_KEY in .env
  Before Prompt 8: optionally drop logo files into web/public/brand/
  After Prompt 13: bash launch.sh → http://localhost:8000

---

## Common issues and fixes

  "No module named anthropic"
    → Run: source venv/bin/activate
    → Check: pip list | grep anthropic

  "No module named playwright"
    → Run: pip install playwright && playwright install chromium
    → Only needed for data generation (generate_data.py)
    → If install fails, delete the scrape block and use hardcoded data only

  "Playwright scrape failed" / Kworb unreachable
    → Expected and handled — script falls back to hardcoded artist data
    → All 7 CSVs still generate correctly
    → Check the print output: "Live data obtained for territories: none (using hardcoded)"

  "Satoshi font not loading"
    → Font shows as fallback system-ui — this is acceptable
    → For real Satoshi: manually download from fontshare.com/fonts/satoshi
      and place .woff2 files in web/public/fonts/

  "Logo not showing"
    → Expected until logo files are provided
    → "CD" text fallback is intentional — not a bug
    → To add logo: copy SVG files to web/public/brand/

  "API returns 500 on chat endpoints"
    → Check ANTHROPIC_API_KEY or OPENAI_API_KEY is set in .env
    → Chat errors should always return 200 with error in reply field
    → If seeing 500s, check server.py exception handling in chat handlers

  "Charts not rendering / blank panels"
    → Run bash dev.sh agents first to generate output CSVs
    → Check data/ folder for agent1_output.csv through agent4_output.csv
    → Panels show EmptyState (not error) when CSVs are missing

  "venv/bin/python3 not found in subprocess"
    → server.py must use the venv Python for subprocess calls
    → Path: os.path.join(PROJECT_ROOT, 'venv', 'bin', 'python3')

  "CORS error in browser"
    → In development, Vite proxy handles this — use port 5173
    → In production, server.py adds CORS headers to every response
    → Never call http://localhost:8000 directly from the Vite dev server

  "Scoring engine fails with KeyError or empty dataframe"
    → Most likely data/artists.csv or scores_weekly.csv row count mismatch
    → Re-run: bash dev.sh data to regenerate everything from scratch
    → With 100 artists the scoring engine must handle larger datasets —
      avoid any hardcoded row count assumptions in scoring_engine.py

  "Agent output CSV has fewer rows than expected"
    → Agent 1 processes top 10 artists by default — increase N if needed
    → Agents 2/3/4 only process HIGH and MEDIUM from prior agent
    → With 100 artists you will have more HIGH/MEDIUM results — this is correct

---

## What this project does NOT do

  - No real Spotify, Chartmetric, or Luminate API connections
    (all metrics are simulated; artist names are real but data is not)
  - No PostgreSQL database (CSV files only)
  - No user authentication
  - No deployment to GCP or any cloud service
  - No mobile native app
  - No real-time data streaming
  - No Power BI integration
  - This is a POC/demo only — production version would replace
    CSV files with PostgreSQL and add real data source connectors

---

## Logo files needed (user action required)

  Place these files in ~/cdx/web/public/brand/ when available:

    chromadata-logo.svg    ← horizontal full logo (preferred format)
    chromadata-logo.png    ← PNG fallback (min 400px wide at 2x)
    chromadata-icon.svg    ← icon/mark only, square (preferred format)
    chromadata-icon.png    ← icon PNG fallback (min 64×64 at 2x)

  Until files are provided: "CD" text placeholder renders automatically.
  Once files are placed: they appear on next hot reload, no code changes.
  SVG is preferred over PNG for crisp rendering at all sizes.