# Franchise / Multi-Store Management Application

Centralized management application for a business that owns or manages multiple stores/locations. See `docs/architecture.md` for the full architecture document (roles, database design, API design, security model, etc.).

## Stack

- **Backend:** Python, FastAPI, SQLAlchemy (async), Alembic migrations
- **Database:** MySQL 8
- **Web:** React
- **Mobile:** React Native
- **Auth:** JWT access + refresh tokens, RBAC, org/store-scoped authorization

## Repository layout

```
backend/   FastAPI application (modular monolith)
web/       React web app (Admin / Supervisor focused)
mobile/    React Native app (Staff focused)
docs/      Architecture and design documents
```

## Development phases

- [x] Phase 1 — Project setup
- [ ] Phase 2 — MySQL schema + Alembic migrations
- [ ] Phase 3 — FastAPI backend skeleton
- [ ] Phase 4 — Authentication
- [ ] Phase 5 — Users & roles
- [ ] Phase 6 — Stores
- [ ] Phase 7 — Daily reports
- [ ] Phase 8 — Notifications
- [ ] Phase 9 — Audit logging
- [ ] Phase 10 — Analytics endpoints
- [ ] Phase 11 — Admin dashboard (web)
- [ ] Phase 12 — Supervisor dashboard (web)
- [ ] Phase 13 — Staff mobile app
- [ ] Phase 14 — Testing
- [ ] Phase 15 — Deployment

## Getting started (backend)

```bash
cd backend
python -m venv .venv
source .venv/bin/activate       # macOS/Linux
pip install -r requirements.txt
cp .env.example .env            # then fill in real values
```

Full setup instructions for each phase will be added to `docs/` as we go.
