# Backend (FastAPI)

Phase 1: project skeleton only (see `app/main.py`).
Phase 3 onward: full app structure per `docs/architecture.md` §9.

## Run locally
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```
Then visit http://127.0.0.1:8000/docs for the interactive API docs.
