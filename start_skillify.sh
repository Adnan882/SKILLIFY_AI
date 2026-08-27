#!/bin/bash
# ============================================================================
# SKILLIFY - Start All AI Systems
# ============================================================================
# Runs all 5 AI services on localhost. Your app connects to these ports.
#
# Services:
#   :8000  Account Suggestions (ML-powered, Skills+Interests+Behaviors)
#   :8001  Skill Quiz (AI skill assessment)
#   :8002  CV Generator (PDF resume builder)
#   :8003  Post Recommendations (Instagram-style feed)
#   :5001  AI Chatbot (NLP-powered assistant)
#
# Usage:
#   chmod +x start_skillify.sh
#   ./start_skillify.sh
#
# To stop: Ctrl+C (all services stop together)
# ============================================================================

SKILLIFY_DIR="$(cd "$(dirname "$0")" && pwd)"
PYTHON=${PYTHON:-python3}
LOG_DIR="$SKILLIFY_DIR/.logs"
PIDS=()
PID_COUNT=0

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

cleanup() {
    echo ""
    echo -e "${YELLOW}Stopping all services...${NC}"
    for pid in "${PIDS[@]}"; do
        kill "$pid" 2>/dev/null || true
    done
    wait 2>/dev/null
    echo -e "${RED}All services stopped.${NC}"
    exit 0
}

trap cleanup SIGINT SIGTERM

mkdir -p "$LOG_DIR"

# ============================================================================
# Setup venv if needed
# ============================================================================
setup_venv() {
    local dir=$1
    local name=$2
    if [ ! -d "$dir/.venv" ]; then
        echo -e "${YELLOW}  Creating venv for $name...${NC}"
        $PYTHON -m venv "$dir/.venv"
    fi
    source "$dir/.venv/bin/activate"
    pip install -q --upgrade pip 2>/dev/null
}

# ============================================================================
# Install dependencies
# ============================================================================
install_deps() {
    local dir=$1
    local name=$2
    if [ -f "$dir/requirements.txt" ]; then
        echo -e "${CYAN}  Installing deps for $name...${NC}"
        pip install -q -r "$dir/requirements.txt" 2>"$LOG_DIR/${name}_install.log"
    fi
}

install_spacy_model() {
    local venv_dir=$1
    echo -e "${CYAN}  Downloading spacy model...${NC}"
    "$venv_dir/bin/python" -m spacy download en_core_web_sm 2>/dev/null || \
    "$venv_dir/bin/pip" install -q spacy-model-en-core-web-sm 2>/dev/null || true
}

# ============================================================================
# Free a port if a stale/orphaned process is still holding it
# ============================================================================
free_port() {
    local port=$1
    local pid
    pid=$(lsof -ti tcp:"$port" 2>/dev/null | head -1)
    if [ -n "$pid" ]; then
        echo -e "    ${YELLOW}Port $port held by PID $pid — stopping stale process...${NC}"
        kill "$pid" 2>/dev/null || true
        sleep 1
    fi
}

# ============================================================================
# Start a service
# ============================================================================
start_service() {
    local name=$1
    local port=$2
    local workdir=$3
    local cmd=$4

    free_port "$port"
    echo -e "${GREEN}  Starting ${BOLD}$name${NC}${GREEN} on port $port...${NC}"
    cd "$workdir"
    eval "$cmd" > "$LOG_DIR/${name}.log" 2>&1 &
    local pid=$!
    PIDS+=($pid)
    PID_COUNT=$((PID_COUNT + 1))
    sleep 4

    if kill -0 "$pid" 2>/dev/null; then
        echo -e "    ${GREEN}✓ $name running → http://localhost:$port${NC}"
    else
        echo -e "    ${RED}✗ $name FAILED (check .logs/${name}.log)${NC}"
        tail -5 "$LOG_DIR/${name}.log" 2>/dev/null | sed 's/^/      /'
    fi
}

# ============================================================================
# MAIN
# ============================================================================
echo ""
echo -e "${BOLD}${BLUE}╔══════════════════════════════════════════════╗${NC}"
echo -e "${BOLD}${BLUE}║         SKILLIFY AI SYSTEM LAUNCHER         ║${NC}"
echo -e "${BOLD}${BLUE}╚══════════════════════════════════════════════╝${NC}"
echo ""

# --- 1. Account Suggestions (port 8000) ---
echo -e "${BOLD}[1/5] Account Suggestions (ML Engine)${NC}"
SUGGEST_DIR="$SKILLIFY_DIR/SuggestionSystem_account"
setup_venv "$SUGGEST_DIR" "suggestions"
install_deps "$SUGGEST_DIR" "suggestions"
start_service "suggestions" 8000 "$SUGGEST_DIR" \
    ".venv/bin/uvicorn skill_suggestion_system:app --host 0.0.0.0 --port 8000"
cd "$SKILLIFY_DIR"

# --- 2. Skill Quiz (port 8001) ---
echo -e "${BOLD}[2/5] Skill Quiz${NC}"
QUIZ_DIR="$SKILLIFY_DIR/ai quiz test/skill-quiz"
setup_venv "$QUIZ_DIR" "quiz"
install_deps "$QUIZ_DIR" "quiz"
install_spacy_model "$QUIZ_DIR/.venv"
start_service "quiz" 8001 "$QUIZ_DIR" \
    ".venv/bin/uvicorn server:app --host 0.0.0.0 --port 8001"
cd "$SKILLIFY_DIR"

# --- 3. CV Generator (port 8002) ---
echo -e "${BOLD}[3/5] CV Generator${NC}"
CV_DIR="$SKILLIFY_DIR/CV Generator"
setup_venv "$CV_DIR" "cv"
install_deps "$CV_DIR" "cv"
start_service "cv" 8002 "$CV_DIR" \
    ".venv/bin/uvicorn server:app --host 0.0.0.0 --port 8002"
cd "$SKILLIFY_DIR"

# --- 4. Post Recommendations (port 8003) ---
echo -e "${BOLD}[4/5] Post Recommendations${NC}"
FEED_DIR="$SKILLIFY_DIR/suggestion_ai"
setup_venv "$FEED_DIR" "feed"
install_deps "$FEED_DIR" "feed"
start_service "feed" 8003 "$FEED_DIR" \
    ".venv/bin/uvicorn server:app --host 0.0.0.0 --port 8003"
cd "$SKILLIFY_DIR"

# --- 5. AI Chatbot (port 5001) ---
echo -e "${BOLD}[5/5] AI Chatbot${NC}"
CHATBOT_DIR="$SKILLIFY_DIR/ai-chatbot"
setup_venv "$CHATBOT_DIR" "chatbot"
install_deps "$CHATBOT_DIR" "chatbot"
start_service "chatbot" 5001 "$CHATBOT_DIR" \
    ".venv/bin/python app.py"
cd "$SKILLIFY_DIR"

# ============================================================================
# Summary
# ============================================================================
echo ""
echo -e "${BOLD}${GREEN}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BOLD}${GREEN}║              ALL 5 AI SERVICES ARE RUNNING                  ║${NC}"
echo -e "${BOLD}${GREEN}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BOLD}  Service                  Port   URL${NC}"
echo -e "  ──────────────────────── ────── ──────────────────────────────"
echo -e "  ${CYAN}Account Suggestions${NC}     8000   http://localhost:8000"
echo -e "  ${CYAN}Skill Quiz${NC}              8001   http://localhost:8001"
echo -e "  ${CYAN}CV Generator${NC}            8002   http://localhost:8002"
echo -e "  ${CYAN}Post Recommendations${NC}    8003   http://localhost:8003"
echo -e "  ${CYAN}AI Chatbot${NC}              5001   http://localhost:5001"
echo ""
echo -e "  ${BOLD}Docs:${NC}"
echo -e "    http://localhost:8000/docs   (Account Suggestions)"
echo -e "    http://localhost:8001/docs   (Skill Quiz)"
echo -e "    http://localhost:8002/docs   (CV Generator)"
echo -e "    http://localhost:8003/docs   (Post Recommendations)"
echo -e "    http://localhost:5001         (Chatbot - Flask)"
echo ""
echo -e "  ${BOLD}Logs:${NC} $LOG_DIR/"
echo -e "  ${YELLOW}Press Ctrl+C to stop all services${NC}"
echo ""

# Wait for all background processes
wait
