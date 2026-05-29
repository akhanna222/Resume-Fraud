#!/usr/bin/env bash
set -e

# ── Resume Fraud Detector — Stage 1 ──────────────────────────────────────────
# Usage: ./run.sh [--port 8000] [--reload]

PORT=${PORT:-8000}
RELOAD=""

for arg in "$@"; do
  case $arg in
    --port) PORT="$2"; shift ;;
    --reload) RELOAD="--reload" ;;
  esac
done

# Ensure .env exists
if [ ! -f .env ]; then
  echo "⚠  No .env found — copying from .env.example"
  cp .env.example .env 2>/dev/null || echo "OPENAI_API_KEY=sk-your-key-here" > .env
fi

# Check key is set
if grep -q "sk-your-key-here" .env; then
  echo "⚠  OPENAI_API_KEY not set in .env — running in heuristics-only mode"
fi

# Install deps if needed
if ! python -c "import fastapi, openai, fitz" 2>/dev/null; then
  echo "→ Installing dependencies..."
  pip install -r requirements.txt -q
fi

echo ""
echo "▶  Starting Resume Fraud Detector on http://localhost:${PORT}"
echo "   Edit .env to add your OPENAI_API_KEY"
echo ""

uvicorn main:app --host 0.0.0.0 --port "$PORT" $RELOAD
