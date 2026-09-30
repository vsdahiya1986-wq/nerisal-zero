#!/usr/bin/env bash
cd "$(dirname "$0")"
if [ ! -d .venv ]; then python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt; else source .venv/bin/activate; fi
cd backend
(sleep 2; (xdg-open http://localhost:8000 || open http://localhost:8000) >/dev/null 2>&1) &
python -m uvicorn app:app --port 8000
