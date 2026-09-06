# Multi-Store / Franchise Management Application — Architecture Document

**Status:** Architecture proposal — no implementation code yet.
**Stack:** React Native (mobile), React (web), FastAPI (Python), MySQL + SQLAlchemy, REST/JSON.

---

## 1. Requirements Summary

You are building a system where an **Organization** owns multiple **Stores**. Three roles interact with it:

- **Admin/Owner** — full visibility and control across all stores in the org.
- **Supervisor** — visibility/control limited to stores they're assigned to.
- **Staff** — belongs to one store, submits daily reports, sees only their own data.

Core capabilities: daily reporting, sales analytics, notifications, RBAC + org/store-scoped authorization, audit logging, dashboards per role, mobile app for staff-heavy workflows, web app for management-heavy workflows.

The system must be multi-tenant-ready (multiple orgs, no cross-org leakage) even though you'll likely launch with one organization.

---

## 2. Assumptions

These are the defaults I'm building the design around. Flag any you want changed:

1. One organization owns many stores; a store belongs to exactly one organization (no shared stores between orgs).
2. A user account belongs to exactly one organization (an owner running two separate businesses would need two accounts — simplest and safest starting point).
3. A Staff user belongs to exactly one store at a time. A Supervisor can be assigned to many stores. An Admin implicitly has access to all stores in their org (no explicit assignment rows needed).
4. Daily reports are submitted once per staff member per store per day, editable only within a limited window (e.g., same day, or until a supervisor approves it).
5. "Approval workflow" for reports is wanted, but simple: submitted → approved/rejected by supervisor. No multi-stage approval chains initially.
6. Money fields are stored in a fixed-point/decimal type, currency is single-currency per organization for v1 (multi-currency postponed).
7. Notifications are in-app (stored + polled/pushed via websockets or push notifications) for v1; email is a later phase.
8. Deployment target is a single region, single environment initially (dev → staging → prod later), not a multi-region setup.

---

## 3. Open Questions (please answer before Phase 2)

| # | Question | Why it matters |
|---|---|---|
| 1 | Can a Staff member ever belong to more than one store? | Determines whether user↔store is one-to-one or many-to-many |
| 2 | Do reports need supervisor approval before they "count," or are they just logged? | Determines report status/workflow states |
| 3 | Can staff edit a submitted report, and for how long? | Determines edit-window and audit rules |
| 4 | Is sales data entered manually by staff (as part of the daily report) or will it eventually sync from a POS system? | Affects whether "Sales" is its own table or derived from reports |
| 5 | Single currency for now? | Affects schema for money fields |
| 6 | Do you need multi-organization support on day one, or just designed so it's *possible* later? | Affects whether org_id is enforced everywhere now or added defensively |
| 7 | Any compliance requirements (data retention length, export requirements)? | Affects audit log retention, soft-delete policy |
| 8 | Expected scale (number of stores, staff, reports/day) in year one? | Affects whether MySQL indexing/partitioning needs early attention |

---

## 4. Recommended Technology Stack

| Layer | Choice | Why |
|---|---|---|
| Mobile | React Native (+ Expo or bare RN) | Single codebase for iOS/Android, matches your requirement |
| Web | React (Vite) | Fast dev experience, same component mental model as RN |
| Backend | FastAPI (Python) | Async-first, automatic OpenAPI docs (huge for a Postman-less workflow and for RN/React clients), Pydantic validation, easy to keep a modular monolith clean |
| ORM | SQLAlchemy 2.0 (async) | Mature, explicit, plays well with MySQL |
| Migrations | Alembic | The standard companion to SQLAlchemy; versioned, reversible migrations you can review before applying |
| Database | MySQL 8 | As required; MySQL 8 supports window functions, CTEs, JSON columns — useful for analytics and flexible "extra fields" |
| Auth | JWT access token (short-lived) + refresh token (longer-lived, rotated, stored server-side or as httpOnly cookie on web / secure storage on mobile) | Stateless access checks, standard, well-supported by FastAPI |
| API style | REST + JSON | As required; OpenAPI docs come free from FastAPI |
| Background jobs (later) | Celery or FastAPI `BackgroundTasks` for simple cases | For notification delivery, scheduled "missing report" checks |

---

## 5. High-Level System Architecture

```
┌─────────────┐     ┌─────────────┐
│ React Native│     │  React Web  │
│  (mobile)   │     │  (desktop)  │
└──────┬──────┘     └──────┬──────┘
       │      REST/JSON     │
       └─────────┬──────────┘
                  ▼
          ┌───────────────┐
          │   FastAPI      │  (modular monolith)
          │  - auth        │
          │  - RBAC layer  │
          │  - services    │
          │  - repositories│
          └───────┬────────┘
                  ▼
          ┌───────────────┐
          │  MySQL (via    │
          │  SQLAlchemy)   │
          └───────────────┘
```

One backend serves both clients. All business logic and authorization live server-side; clients are "dumb" about permissions — they render based on what the API returns/allows, but the API is the actual gatekeeper.

---

## 6. Database Architecture

### Core tables

**organizations**
- PK: `id`
- Columns: `name`, `created_at`, `updated_at`, `is_active`
- Purpose: top-level tenant boundary.

**stores**
- PK: `id`
- FK: `organization_id → organizations.id`
- Columns: `name`, `address`, `timezone`, `is_active`, `created_at`, `updated_at`
- Index: `(organization_id)`

**users**
- PK: `id`
- FK: `organization_id → organizations.id`
- Columns: `email` (unique per org), `hashed_password`, `full_name`, `role` (enum: admin/supervisor/staff) or a separate `roles` table (see below), `is_active`, `created_at`, `updated_at`, `last_login_at`
- Index: `(organization_id, email)` unique

**roles** (optional normalization)
- If you want more than 3 fixed roles later, use a `roles` table + `user_roles` join table. For v1, a `role` enum column on `users` is simpler and sufficient — you can migrate to a full RBAC table later without breaking the API contract.

**user_store_assignments**
- PK: `id`
- FK: `user_id → users.id`, `store_id → stores.id`
- Columns: `created_at`
- Purpose: many-to-many between Supervisors and Stores (and Staff, if a staff member can belong to more than one store — see Open Question 1). Unique constraint on `(user_id, store_id)`.
- Admins do **not** need rows here — their access is "all stores where store.organization_id == user.organization_id," computed, not stored.

**daily_reports**
- PK: `id`
- FK: `store_id → stores.id`, `submitted_by_user_id → users.id`
- Columns: `report_date` (date), `total_sales`, `transaction_count`, `cash_sales`, `card_sales`, `other_payment_sales`, `expenses`, `refunds`, `notes`, `status` (enum: submitted/approved/rejected), `reviewed_by_user_id` (nullable FK to users), `reviewed_at`, `created_at`, `updated_at`
- Constraint: unique `(store_id, submitted_by_user_id, report_date)` — one report per staff per store per day (adjust if multiple shifts/day are needed).
- Index: `(store_id, report_date)` for fast date-range queries.
- Note: extra/business-specific metrics that vary by org can go in a JSON column (`extra_fields`) rather than adding new columns per client — configurable without a migration.

**sales** (optional, separate from daily_reports)
- If sales will ever be more granular than "one row per report" (e.g., itemized, per-hour, POS-synced), keep it as its own table now:
- PK: `id`, FK: `store_id`, `report_id` (nullable), Columns: `amount`, `payment_method`, `occurred_at`, `source` (manual/pos), `created_at`
- If sales are *only* ever the aggregate numbers staff type into their daily report, you don't need this table yet — the fields on `daily_reports` are enough. I recommend deferring this table until you confirm Open Question 4.

**notifications**
- PK: `id`
- FK: `user_id → users.id` (recipient), nullable `organization_id`, nullable `store_id` for scoping
- Columns: `type` (enum: report_submitted, report_approved, report_rejected, missing_report, system), `title`, `body`, `is_read`, `created_at`, `related_entity_type`, `related_entity_id` (generic pointer back to e.g. a report)

**audit_logs**
- PK: `id`
- FK: `user_id → users.id` (nullable, for failed logins before identity is confirmed), `organization_id`
- Columns: `action` (enum/string: login, logout, failed_login, user_created, user_updated, store_created, store_updated, report_submitted, report_updated, report_approved, report_rejected), `entity_type`, `entity_id`, `metadata` (JSON — old/new values, IP address, user agent), `created_at`
- Index: `(organization_id, created_at)`, `(user_id, created_at)`
- No updates/deletes — audit logs are append-only.

### Relationships summary

- Organization 1→N Stores
- Organization 1→N Users
- User N→N Stores (via `user_store_assignments`, for supervisors/multi-store staff)
- Store 1→N Reports
- User 1→N Reports (as submitter), 1→N Reports (as reviewer)
- User 1→N Notifications
- Organization 1→N Audit Logs, User 1→N Audit Logs

### Soft delete

Use `is_active` boolean (not physical delete) on `organizations`, `stores`, `users` — you'll want to deactivate a store or user without losing historical report/sales/audit data that references them. `daily_reports` and `audit_logs` themselves are never deleted.

---

## 7. Role & Permission Matrix

| Action | Admin | Supervisor | Staff |
|---|---|---|---|
| View all stores in org | ✓ | ✗ (assigned only) | ✗ (own store only) |
| Manage stores (create/edit) | ✓ | ✗ | ✗ |
| Manage users | ✓ | Limited (can view staff at assigned stores; cannot create/deactivate accounts) | ✗ |
| Assign supervisor to store | ✓ | ✗ | ✗ |
| Submit daily report | ✗ (not their job, but not blocked) | ✗ typically | ✓ |
| Review/approve report | ✓ | ✓ (assigned stores only) | ✗ |
| View sales — all stores | ✓ | ✗ | ✗ |
| View sales — assigned/own store | ✓ | ✓ | ✓ (own submissions only) |
| View analytics/dashboards | ✓ (org-wide) | ✓ (assigned stores) | ✓ (own store, limited) |
| View audit logs | ✓ | Limited (their own actions + their stores' report-related events) | ✗ |
| Receive notifications | ✓ | ✓ | ✓ |

**Three layers of authorization, checked in this order on every request:**

1. **Authentication** — is the JWT valid and not expired?
2. **Organization scope** — does the requested resource belong to the user's `organization_id`? (Always checked, even for Admins — this is what prevents cross-org leakage.)
3. **Role + store scope** — given the role, is this specific store/report/user within what that role is allowed to touch? (Admin: any store in org. Supervisor: only stores in their `user_store_assignments`. Staff: only their own store and own reports.)

This is enforced with a dependency function in FastAPI (e.g. `get_current_user_with_store_access(store_id)`) used on every store-scoped endpoint — never trust a `store_id` from the request body/query without re-checking it against the DB relationship for that user.

---

## 8. API Architecture (representative endpoints)

Grouped by resource: `/auth`, `/users`, `/stores`, `/reports`, `/sales`, `/notifications`, `/analytics`, `/audit-logs`.

**POST /auth/login**
- Access: public
- Body: `{ email, password }`
- Response: `{ access_token, refresh_token, user }`
- Errors: 401 invalid credentials, 429 too many attempts

**POST /auth/refresh**
- Access: valid refresh token
- Response: new access token (+ rotated refresh token)

**GET /stores**
- Access: Admin (all in org), Supervisor (assigned only), Staff (own only)
- Response: list scoped automatically by role — the endpoint never takes an "org_id" param from the client; it's derived from the authenticated user.

**GET /stores/{store_id}**
- Access: must pass the store-access dependency described above
- Errors: 403 if store not in the user's allowed set (not 404 — but consider returning 404 instead of 403 to avoid confirming a store ID exists across orgs)

**POST /reports**
- Access: Staff (their own store only)
- Body: `{ store_id, report_date, total_sales, cash_sales, card_sales, expenses, refunds, notes, extra_fields }`
- Validation: `store_id` must be in the caller's assigned store(s); `report_date` cannot be in the future; one report per store/user/day (409 on duplicate)

**PATCH /reports/{report_id}/review**
- Access: Supervisor (assigned store) or Admin
- Body: `{ status: approved|rejected, comment }`
- Side effect: creates a notification for the submitter, writes an audit log entry

**GET /analytics/sales?store_id=&from=&to=&group_by=day|week|month**
- Access: scoped per role as above
- Response: aggregated sales figures — computed server-side via SQL aggregation, not by shipping raw rows to the client

---

## 9. Backend Folder Structure (FastAPI, modular monolith)

```
backend/
  app/
    main.py                 # FastAPI app instance, router registration
    core/
      config.py             # settings via env vars (pydantic-settings)
      security.py           # password hashing, JWT creation/verification
    api/
      v1/
        auth.py
        users.py
        stores.py
        reports.py
        sales.py
        notifications.py
        analytics.py
        audit_logs.py
        deps.py             # shared dependencies: get_current_user, store-access checks
    models/                 # SQLAlchemy ORM models (one file per entity)
    schemas/                # Pydantic request/response models
    services/               # business logic (e.g. report_service.py)
    repositories/            # DB query functions, isolated from business logic
    db/
      session.py
      base.py
    middleware/              # e.g. audit logging middleware, request logging
    utils/
  alembic/                   # migration scripts
  tests/
  .env.example
  requirements.txt
```

Each folder's job: `api/` only parses requests and calls `services/`; `services/` holds business rules (e.g., "can this user approve this report?"); `repositories/` only talks to the DB. This separation means you can unit-test business logic without spinning up a database.

---

## 10. React Native Folder Structure

```
mobile/
  src/
    api/                # thin wrapper around fetch/axios, shared response types
    auth/                # token storage (secure), auth context
    navigation/          # stack/tab navigators per role
    screens/
      auth/
      staff/             # report submission, own reports
      supervisor/        # assigned stores, review queue
      shared/
    components/
    hooks/
    store/               # global state (Zustand/Redux) — mostly auth + cached lookups
    utils/
```

## 11. React Web Folder Structure

```
web/
  src/
    api/                 # same contract shape as mobile's api layer
    auth/
    routes/              # role-based route guards
    pages/
      admin/
      supervisor/
      staff/
    components/
    hooks/
    store/
    utils/
```

**Shared logic:** put anything not tied to React Native or DOM-specific UI (API client, validation schemas, types/interfaces, auth token refresh logic) in a shared package (e.g. a small internal npm workspace) so both apps import the same code instead of re-implementing it.

---

## 12. Authentication Architecture

1. User logs in → backend verifies password hash → issues short-lived access token (~15 min) and a refresh token (~7–30 days).
2. Web: refresh token in an httpOnly secure cookie; access token in memory. Mobile: refresh token in secure storage (Keychain/Keystore) via `expo-secure-store` or equivalent.
3. Access token carries `user_id`, `organization_id`, `role` as claims — so most requests don't need an extra DB lookup just to know the role, though store-level access is still re-verified against the DB on every store-scoped request (claims are for role, not for store lists — store assignments can change and shouldn't wait for token expiry).
4. Refresh tokens are stored (hashed) server-side so they can be revoked (logout, password change, admin-forced logout).

## 13. Security Architecture

- **Never trust client-supplied IDs.** Every endpoint that takes a `store_id`, `user_id`, or `report_id` re-derives the allowed set from the database using the authenticated user's ID — it does not simply check "does this ID look valid," it checks "is this ID in the set this specific user is allowed to touch." This is what stops someone from editing a URL/body to hit another store's data.
- Passwords hashed with bcrypt/argon2, never reversible.
- Rate-limit `/auth/login` and `/auth/refresh`.
- All inputs validated via Pydantic schemas (type, length, format).
- CORS locked to your known frontend origins.
- SQL access exclusively through SQLAlchemy (parameterized) — no raw string-interpolated queries.
- Audit log write is not optional/best-effort for sensitive actions — treat it as part of the transaction where reasonable.

## 14. Dashboard Architecture

**Admin (web-first, mobile secondary):** org-wide KPIs, store comparison table/chart, missing-reports list, notification feed. Desktop shows more density (tables, multi-chart grids); mobile shows summarized cards.

**Supervisor (both):** assigned-store list with quick status, pending-review queue, sales trend for their stores.

**Staff (mobile-first):** today's report status (submitted/not), quick-entry form, list of past reports, notifications. Desktop staff view (if any) is a simplified read-only version.

## 15. Reporting Workflow

Staff opens app → "Today's Report" screen → fills fields → submit → row created with `status=submitted` → notification created for the store's supervisor(s) → supervisor reviews → approve/reject → notification back to staff → audit log entries at submit and at review.

## 16. Sales Workflow

For v1 (pending Open Question 4): sales figures are entered as part of the daily report — no separate sales-entry screen. Analytics endpoints aggregate `daily_reports` rows by store/date range. If POS integration is added later, a dedicated `sales` table (see §6) can be introduced without breaking the reports table.

## 17. Notification Workflow

Event occurs (report submitted, reviewed, or a scheduled job detects a missing report) → a row is written to `notifications` → client fetches unread notifications on load and polls or subscribes (websocket) for new ones. Push notifications (APNs/FCM) and email are additive delivery channels on top of the same `notifications` table — not a redesign.

---

## 18. Development Phases (adjusted)

1. Project setup (repo structure, tooling, env config)
2. MySQL schema + Alembic migrations for core tables (org, stores, users, assignments)
3. FastAPI skeleton + health check + OpenAPI docs working
4. Authentication (login, JWT, refresh, password hashing)
5. Users & roles (CRUD scoped by org, RBAC dependency)
6. Stores (CRUD, assignment endpoints)
7. Daily reports (submit, list, review)
8. Notifications (basic in-app)
9. Audit logging (middleware/service)
10. Analytics endpoints (aggregation queries)
11. Admin dashboard (web)
12. Supervisor dashboard (web)
13. Staff mobile app (React Native)
14. Testing pass (backend unit/integration, key frontend flows)
15. Deployment (staging → production)

(Moved audit logging earlier than your original draft, and notifications before analytics, since reports rely on both.)

## 19. Recommended MVP Scope

- Single organization, single currency.
- Staff: submit/view own reports.
- Supervisor: view assigned stores, review reports.
- Admin: manage stores/users, view all reports and basic aggregated sales (today/week/month, by store).
- In-app notifications only.
- Web app for Admin/Supervisor, mobile app for Staff (Admin/Supervisor mobile views can follow after MVP).

## 20. Postpone Until Later

- Multi-organization support beyond schema readiness (build the `organization_id` scoping now, but don't build an org-signup/switching flow yet).
- Multi-currency.
- Push and email notification delivery.
- POS integration / itemized sales table.
- Multi-stage report approval chains.
- Advanced analytics (forecasting, anomaly detection).
- Microservices split — stay a modular monolith until you have a concrete scaling reason.

## 21. Potential Risks / Design Watchpoints

- **Store-ID tampering** — mitigated by the always-re-check-from-DB rule in §13; needs to be enforced consistently across every endpoint, not just some.
- **Report double-submission / race conditions** — the unique constraint `(store_id, submitted_by_user_id, report_date)` prevents duplicates at the DB level, not just in application code.
- **Timezone handling** — stores may span timezones; `report_date` should be computed using the store's timezone, not the server's or the client device's.
- **JSON "extra_fields" column growing unmanaged** — fine for flexibility, but don't let core reporting logic depend on parsing arbitrary JSON; promote a field to a real column once it's used by most orgs/stores.
- **Audit log volume** — append-only table will grow quickly; plan an index/retention strategy even if you don't implement archiving in v1.

---

## 22. Recommended Architecture — Summary

A **modular monolith FastAPI backend** with a single MySQL database, organization/store scoping enforced in a shared authorization layer, serving both a React web app (Admin/Supervisor-focused) and a React Native app (Staff-focused). This avoids the operational overhead of microservices while keeping clean internal boundaries (`api` / `services` / `repositories`) so pieces can be split out later if the product genuinely needs it. The schema is built around Organization → Store → User/Report as the spine, with Notifications and Audit Logs as cross-cutting tables that hang off Users and Stores rather than being deeply nested — this keeps the core relationships simple while still supporting rich history and traceability.

**Next step:** review the Open Questions in §3 — your answers to those will lock in a few schema details (report editability, user↔store cardinality, sales granularity) before we start Phase 1.
