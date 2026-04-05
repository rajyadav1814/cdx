#!/bin/bash
cd ~/cdx
source venv/bin/activate
export $(grep -v '^#' .env | xargs 2>/dev/null)

case "$1" in
  frontend)
    echo "Starting React dev server on http://localhost:5173"
    cd web && npm run dev
    ;;
  backend)
    echo "Starting Python API server on http://localhost:8000"
    python3 web/server.py
    ;;
  dev)
    echo "Starting both servers..."
    echo "  React app:  http://localhost:5173"
    echo "  Python API: http://localhost:8000"
    python3 web/server.py &
    BACKEND_PID=$!
    cd web && npm run dev
    kill $BACKEND_PID
    ;;
  build)
    echo "Building React app for production..."
    cd web && npm run build
    echo "Built to ~/cdx/web/dist/ — served by Python on :8000"
    ;;
  data)   python3 data/generate_data.py && python3 scores/scoring_engine.py ;;
  scores) python3 scores/scoring_engine.py ;;
  agents) python3 agents/run_all_agents.py ;;
  agent1) python3 -c "from agents.agent1_opportunity import run_agent; run_agent()" ;;
  agent2) python3 -c "from agents.agent2_strategy import run_agent; run_agent()" ;;
  agent3) python3 -c "from agents.agent3_audience import run_agent; run_agent()" ;;
  agent4) python3 -c "from agents.agent4_roi import run_agent; run_agent()" ;;
  models) python3 -c "from model_router import get_models_for_frontend; \
    import json; print(json.dumps(get_models_for_frontend(), indent=2))" ;;
  *)
    echo "CDX — Commercial Signal Intelligence Engine"
    echo "Usage: bash dev.sh [command]"
    echo ""
    echo "  Development:"
    echo "    dev       — React + Python servers together"
    echo "    frontend  — React dev server only (port 5173)"
    echo "    backend   — Python API server only (port 8000)"
    echo "    build     — build React for production"
    echo ""
    echo "  Data & agents:"
    echo "    data    scores    agents"
    echo "    agent1  agent2    agent3    agent4    models"
    ;;
esac
