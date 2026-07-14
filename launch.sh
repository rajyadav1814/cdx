#!/bin/bash
set -e
cd ~/cdx
[ ! -f ".env" ] && echo "Error: .env not found in ~/cdx" && exit 1
source venv/bin/activate
if [ -f "requirements.txt" ]; then
  pip install -r requirements.txt
fi
export $(grep -v '^#' .env | xargs 2>/dev/null)
streamlit run streamlit_app.py --server.port 8000 --server.address 0.0.0.0
