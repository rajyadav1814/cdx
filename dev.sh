#!/bin/bash
cd ~/cdx
source venv/bin/activate
export $(grep -v '^#' .env | xargs 2>/dev/null)

if [ -f "requirements.txt" ]; then
  pip install -r requirements.txt
fi

case "$1" in
  streamlit)
    echo "Starting Streamlit app on http://localhost:8501"
    streamlit run streamlit_app.py
    ;;
  frontend)
    echo "Starting React dev server on http://localhost:5173"
    cd web && npm run dev
    ;;
  backend)
    echo "Starting Python API server on http://localhost:8000"
    python3 web/server.py
    ;;
  dev)
    echo "Starting Streamlit and backend together..."
    python3 web/server.py &
    BACKEND_PID=$!
    streamlit run streamlit_app.py
    kill $BACKEND_PID
    ;;
  build)
    echo "Building React app for legacy use..."
    cd web && npm run build
    ;;
  data)   python3 data/generate_data.py && python3 scores/scoring_engine.py ;;
  scores) python3 scores/scoring_engine.py ;;
  agents) python3 agents/run_all_agents.py ;;
  agent1) python3 -c "from agents.agent1_opportunity import run_agent; run_agent()" ;;
  agent2) python3 -c "from agents.agent2_strategy import run_agent; run_agent()" ;;
  agent3) python3 -c "from agents.agent3_audience import run_agent; run_agent()" ;;
  agent4) python3 -c "from agents.agent4_roi import run_agent; run_agent()" ;;
  models) python3 -c "from model_router import get_models_for_frontend; import json; print(json.dumps(get_models_for_frontend(), indent=2))" ;;
  *)
    echo "CDX — Commercial Signal Intelligence Engine"
    echo "Usage: bash dev.sh [command]"
    echo ""
    echo "  Streamlit:"
    echo "    streamlit  — Streamlit app only (port 8501)"
    echo ""
    echo "  Legacy frontend:"
    echo "    dev       — Streamlit + backend"
    echo "    frontend  — React dev server only (port 5173)"
    echo "    backend   — Python API server only (port 8000)"
    echo "    build     — build React for legacy use"
    echo ""
    echo "  Data & agents:"
    echo "    data    scores    agents"
    echo "    agent1  agent2    agent3    agent4    models"
    ;;
esac
