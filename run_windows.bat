@echo off
cd /d %~dp0
if not exist .venv (
  python -m venv .venv
  call .venv\Scripts\activate
  pip install -r requirements.txt
) else (
  call .venv\Scripts\activate
)
cd backend
start "" http://localhost:8000
python -m uvicorn app:app --port 8000
