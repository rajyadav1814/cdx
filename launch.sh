#!/bin/bash
set -e
RED='\033[0;31m'; GREEN='\033[0;32m'
YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  CDX — Commercial Signal Intelligence Engine         ${NC}"
echo -e "${BLUE}  Chromadata × Sony Music Latin                       ${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

cd ~/cdx
[ ! -f ".env" ] && echo -e "${RED}Error: .env not found in ~/cdx${NC}" && exit 1

source venv/bin/activate

if [ -f "requirements.txt" ]; then
  echo -e "${BLUE}→ Installing Python dependencies...${NC}"
  pip install -r requirements.txt
fi
export $(grep -v '^#' .env | xargs 2>/dev/null)

ANTHROPIC_OK=false; OPENAI_OK=false
[[ -n "$ANTHROPIC_API_KEY" && "$ANTHROPIC_API_KEY" != "your_anthropic_key_here" ]] \
  && ANTHROPIC_OK=true && echo -e "${GREEN}✓ Anthropic key found${NC}" \
  || echo -e "${YELLOW}⚠ Anthropic key not set${NC}"
[[ -n "$OPENAI_API_KEY" && "$OPENAI_API_KEY" != "your_openai_key_here" ]] \
  && OPENAI_OK=true && echo -e "${GREEN}✓ OpenAI key found${NC}" \
  || echo -e "${YELLOW}⚠ OpenAI key not set${NC}"

[ "$ANTHROPIC_OK" = false ] && [ "$OPENAI_OK" = false ] \
  && echo -e "${RED}Error: no API keys set in ~/cdx/.env${NC}" && exit 1

[ ! -f "data/artists.csv" ] \
  && echo -e "${YELLOW}→ Generating sample data...${NC}" \
  && python3 data/generate_data.py \
  && echo -e "${GREEN}✓ Data generated${NC}"

[ ! -f "data/scores_weekly.csv" ] \
  && echo -e "${YELLOW}→ Running scoring engine...${NC}" \
  && python3 scores/scoring_engine.py \
  && echo -e "${GREEN}✓ Scores done${NC}"

[ ! -f "data/agent4_output.csv" ] \
  && echo -e "${YELLOW}→ Running agents (calls AI APIs)...${NC}" \
  && python3 agents/run_all_agents.py \
  && echo -e "${GREEN}✓ Agents complete${NC}"

if [ ! -d "web/dist" ]; then
  echo -e "${YELLOW}→ Building React app...${NC}"
  cd web && npm run build && cd ..
  echo -e "${GREEN}✓ React app built${NC}"
fi

echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}  App running at: http://localhost:8000               ${NC}"
echo -e "${GREEN}  Press Ctrl+C to stop                               ${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
python3 web/server.py
