# CareerHound — resume-matched job aggregation platform

A CareerHound / JobLeads / Himalayas-style platform that pulls jobs from company
career pages and remote boards, matches them to **your resume**, streams new
postings live, and can **tailor your resume per company** using AI.

Python (FastAPI) backend + React (Vite) frontend.

---

## Features

| Feature | How it works |
| --- | --- |
| **Jobs from company career pages** | Adapters for **Greenhouse, Lever, Ashby** (the ATS backends behind thousands of company career pages) plus **Remotive** and **RemoteOK** remote boards. All via public JSON APIs — the real "Apply" links, no HTML scraping. |
| **Resume matching** | Upload a PDF/DOCX/TXT resume → parsed for skills + target role → jobs scored 0–100 (TF-IDF cosine, optional AI re-rank). |
| **Remote tabs** | `Remote · India`, `Remote · Outside India` classified at ingest from location + description. |
| **WFH · Delhi-NCR tab** | Flexible / work-from-home roles tied to Noida / Gurgaon / Delhi / Ghaziabad / Faridabad. |
| **Live streaming** | A scheduler polls sources; every new job is pushed to the UI over **Server-Sent Events**, scored against your resume in real time. |
| **Resume enhancement** | Per-job "Tailor resume" → tailored summary, rewritten bullets, ATS keywords, and a cover letter (AI when a key is set; rule-based draft otherwise). |
| **Filters** | Category, country, min salary, posted-since, title/company search, sort by recency or match. |

---

## Architecture

```
frontend (React/Vite)  ──/api──▶  backend (FastAPI)
                                    ├─ ingest/        adapters + pipeline + scheduler
                                    │    greenhouse, lever, ashby, remotive, remoteok
                                    ├─ matching/      resume parsing + TF-IDF matcher
                                    ├─ ai/            pluggable Anthropic client + enhancer
                                    ├─ events.py      in-process pub/sub → SSE
                                    └─ SQLModel DB    SQLite (default) / Postgres
```

Ingest flow: **fetch → normalize (`RawJob`) → classify (remote/WFH/country/salary) →
dedupe by fingerprint → persist → broadcast to SSE subscribers.**

---

## Quick start

### 1. Backend

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # optional: add ANTHROPIC_API_KEY for AI
uvicorn app.main:app --reload --port 8000
```

- API docs: http://localhost:8000/docs
- Health:  http://localhost:8000/api/health

On first run it seeds ~18 career-page sources (`app/ingest/seed_sources.json`)
and starts the polling scheduler. To try it **without network access**, load the
offline sample set:

```bash
curl -X POST http://localhost:8000/api/sources/load-sample
```

### 2. Frontend

```bash
cd frontend
npm install
npm run dev        # http://localhost:5173  (proxies /api → :8000)
```

Open the app → **Upload resume** → jobs get match scores → switch tabs →
click **✨ Tailor resume** on any job.

---

## Enabling AI

Set `ANTHROPIC_API_KEY` in `backend/.env`. Then:

- **Matching** — top candidates can be re-ranked by the LLM
  (`GET /api/resumes/{id}/matches?use_ai=true`).
- **Enhancement** — `/api/resumes/enhance` returns a genuinely tailored resume +
  cover letter instead of the rule-based draft.

The whole app runs with **no key** — it just uses TF-IDF matching and a
deterministic enhancement draft.

---

## Adding company sources

Most company career pages are powered by an ATS with a public board token:

```bash
# Greenhouse: https://boards.greenhouse.io/<slug>
curl -X POST localhost:8000/api/sources -H 'Content-Type: application/json' \
  -d '{"provider":"greenhouse","slug":"stripe"}'

# Lever: https://jobs.lever.co/<slug>
curl ... -d '{"provider":"lever","slug":"netflix"}'

# Ashby: https://jobs.ashbyhq.com/<slug>
curl ... -d '{"provider":"ashby","slug":"openai"}'
```

Supported providers: `greenhouse`, `lever`, `ashby`, `remotive`, `remoteok`.

---

## Key API endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/api/jobs` | List/filter jobs (`tab`, `q`, `category`, `country`, `min_salary`, `date_from`, `resume_id`, `sort`) |
| GET | `/api/jobs/meta/facets` | Categories/countries for filter dropdowns |
| POST | `/api/resumes` | Upload resume (multipart) |
| GET | `/api/resumes/{id}/matches` | Ranked matches (`use_ai=true` to LLM re-rank) |
| POST | `/api/resumes/enhance` | Tailor resume to a job |
| GET | `/api/stream/jobs` | SSE live feed of new jobs |
| GET/POST | `/api/sources` | List / add career-page sources |
| POST | `/api/sources/ingest` | Run an ingest pass now |
| POST | `/api/sources/load-sample` | Load offline sample jobs |

---

## Notes & next steps

- **Egress:** the live adapters need outbound access to
  `boards-api.greenhouse.io`, `api.lever.co`, `api.ashbyhq.com`,
  `remotive.com`, `remoteok.com`. In a restricted network these are blocked;
  use `load-sample` for local demos.
- **Scaling the "stream as soon as posted":** swap `events.py` for Redis pub/sub
  and run multiple workers; move the scheduler to a dedicated worker.
- **More sources:** add adapters for Workday, SmartRecruiters, Recruitee, and
  India boards; the `RawJob` contract keeps adapters uniform.
- **AI job extraction:** for career pages *not* on a known ATS, an AI extraction
  adapter (fetch page → LLM → `RawJob`) can be plugged into the same pipeline.
