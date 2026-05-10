# TASKS.md — Intelligent User Feedback Analysis and Action System

> **Tech Stack:** LangGraph · OpenAI · Docker · Azure · SQLite · ChromaDB (RAG) · Streamlit · Python

---

## Legend

| Field | Values |
|---|---|
| Priority | P0 = Critical · P1 = High · P2 = Medium · P3 = Low |
| Complexity | XS · S · M · L · XL |
| Status | 🔲 Todo · 🔄 In Progress · ✅ Done |

---

## 📋 Product Manager

| ID | Task | Description | Priority | Complexity | Status |
|---|---|---|---|---|---|
| PM-01 | Define project structure & repo layout | Set up folder structure: `agents/`, `data/`, `ui/`, `tests/`, `config/` | P0 | XS | 🔲 |
| PM-02 | Define data schemas | Document CSV column schemas for all input/output files (`app_store_reviews.csv`, `support_emails.csv`, `expected_classifications.csv`, `generated_tickets.csv`, `processing_log.csv`, `metrics.csv`) | P0 | S | 🔲 |
| PM-03 | Define agent contracts | Document the input/output interface for each of the 6 agents so all devs align | P0 | S | 🔲 |
| PM-04 | Define classification categories & priorities | Agree on final category labels (Bug/Feature Request/Praise/Complaint/Spam) and priority levels (Critical/High/Medium/Low) with thresholds | P0 | XS | 🔲 |
| PM-05 | Create ticket template | Define the standard structure of a generated ticket (title, description, steps to reproduce, severity, category, source_id, timestamp) | P1 | XS | 🔲 |
| PM-06 | Write acceptance criteria checklist | Final demo checklist covering all system objectives (Automation, Speed, Consistency, Traceability, Usability) | P1 | S | 🔲 |

---

## 🗄️ Backend Dev — DB & Infrastructure

| ID | Task | Description | Acceptance Criteria | Priority | Complexity | Depends On | Status |
|---|---|---|---|---|---|---|---|
| DB-01 | Initialise project & virtual environment | Create `requirements.txt` with all dependencies (langgraph, anthropic, chromadb, streamlit, pandas, sqlalchemy, etc.) | `pip install -r requirements.txt` succeeds | P0 | XS | — | ✅ Done |
| DB-02 | Docker setup | Write `Dockerfile` and `docker-compose.yml` for the app | `docker compose up` boots the system | P0 | M | DB-01 | ✅ Done |
| DB-03 | Configure SQLite | Set up DB connection layer using SQLAlchemy with SQLite; create tables for tickets, processing log, and metrics | Tables exist; CRUD operations verified | P0 | M | DB-01 | ✅ Done |
| DB-04 | Configure ChromaDB | Initialise ChromaDB collection for storing feedback embeddings; write helper functions for upsert and query | Embeddings are stored and retrievable | P1 | M | DB-01 | ✅ Done |
| DB-05 | Azure deployment config | Provision Azure App Service / Container Instance; set up environment variables and secrets in Azure Key Vault | App accessible at Azure URL | P2 | L | DB-02 | 🔲 |
| DB-06 | Logging infrastructure | Set up structured logging to `processing_log.csv` and console; include agent name, timestamp, decision, confidence | Log file populated after a pipeline run | P1 | S | DB-01 | ✅ Done |
| DB-07 | Environment config module | Create `config.py` / `.env` handling for classification thresholds, priority mappings, model names, file paths | All settings overridable via env vars | P1 | XS | DB-01 | ✅ Done |

---

## ⚙️ Backend Dev — Agents & API

### Step 1 — Mock Data

| ID | Task | Description | Acceptance Criteria | Priority | Complexity | Depends On | Status |
|---|---|---|---|---|---|---|---|
| BE-01 | Create `app_store_reviews.csv` | Generate ≥ 30 realistic rows covering Bug, Feature Request, Praise, Complaint, and Spam entries. Columns: `review_id, platform, rating, review_text, user_name, date, app_version`. Mix Google Play & App Store entries. | File loads without errors; all 5 categories represented | P0 | S | PM-02 | ✅ Done |
| BE-02 | Create `support_emails.csv` | Generate ≥ 20 realistic rows. Columns: `email_id, subject, body, sender_email, timestamp, priority`. Include technical details and varied email styles. | File loads without errors; varied priority values | P0 | S | PM-02 | ✅ Done |
| BE-03 | Create `expected_classifications.csv` | Ground-truth labels for all rows above. Columns: `source_id, source_type, category, priority, technical_details, suggested_title`. | IDs match `app_store_reviews.csv` and `support_emails.csv` | P0 | S | BE-01, BE-02 | ✅ Done |

### Step 2 — Agent Implementation (LangGraph)

| ID | Task | Description | Acceptance Criteria | Priority | Complexity | Depends On | Status |
|---|---|---|---|---|---|---|---|
| BE-04 | CSV Reader Agent | Reads and parses CSVs; normalises into unified schema; **stores all feedback in RAG** for duplicate detection | Handles missing fields gracefully; feedback in ChromaDB | P0 | M | BE-01, BE-02, DB-07 | ✅ Done |
| BE-05 | Feedback Classifier Agent | Classifies each feedback item into Bug / Feature Request / Praise / Complaint / Spam with confidence score via **OpenAI** | Accuracy ≥ 80% vs `expected_classifications.csv` | P0 | L | BE-04, PM-04 | ✅ Done |
| BE-06 | Bug Analysis Agent | Extracts bug details; **uses product docs RAG** to match known bugs and identify root causes | Structured bug fields populated; known_bug_match from RAG | P1 | L | BE-05 | ✅ Done |
| BE-07 | Feature Extractor Agent | Extracts feature details; **uses product docs RAG** to check roadmap and existing features | Feature summary + impact + planned_version from RAG | P1 | L | BE-05 | ✅ Done |
| BE-08 | Ticket Creator Agent | Creates structured tickets; **uses ticket RAG for duplicate detection**; stores new tickets in RAG | Tickets created; duplicates flagged; tickets in ChromaDB | P0 | L | BE-06, BE-07, PM-05 | ✅ Done |
| BE-09 | Quality Critic Agent | Reviews tickets for completeness; auto-revises low-quality tickets (score < 0.7) | No ticket missing critical fields; rewrite rate logged | P1 | M | BE-08 | ✅ Done |
| BE-10 | LangGraph orchestration | All 6 agents wired in LangGraph `StateGraph`; sequential flow with specialist agents filtering by category | Full pipeline compiles and runs end-to-end | P0 | L | BE-04 – BE-09 | ✅ Done |
| BE-11 | Metrics collection | Integrated into pipeline `save_outputs` node; writes to `metrics.csv` and SQLite | `metrics.csv` populated after each run | P1 | S | BE-10 | ✅ Done |
| BE-12 | Error handling & retry logic | Every agent wraps LLM calls in try/except; errors collected in state without crashing pipeline | Pipeline completes even if individual items fail | P1 | M | BE-10 | ✅ Done |

---

## 🖥️ Frontend Dev — Streamlit UI

| ID | Task | Description | Acceptance Criteria | Priority | Complexity | Depends On | Status |
|---|---|---|---|---|---|---|---|
| FE-01 | App skeleton & navigation | Create `app.py` with Streamlit multi-page layout: Dashboard, Run Pipeline, Configuration, Manual Override, Analytics, Processing Log, Product Docs | App boots with no errors | P0 | S | DB-01 | ✅ Done |
| FE-02 | Dashboard page | Show overview: number of feedback items processed, breakdown by category (pie/bar chart), latest generated tickets table | Live data from `generated_tickets.csv` or DB | P0 | M | FE-01, BE-08 | ✅ Done |
| FE-03 | Pipeline trigger UI | Button to upload/select CSV files and trigger the full pipeline run; show real-time progress/status | Pipeline starts on click; progress visible | P0 | M | FE-01, BE-10 | ✅ Done |
| FE-04 | Configuration panel | Sliders/inputs for classification confidence threshold, priority mappings, and model selection; persist settings to `.env` or config file | Changed settings affect next pipeline run | P1 | M | FE-01, DB-07 | ✅ Done |
| FE-05 | Manual override page | Table of generated tickets with inline edit capability; allow changing category, priority, and title; save changes back to DB/CSV | Edited tickets saved and reflected in Dashboard | P1 | L | FE-02 | ✅ Done |
| FE-06 | Analytics page | Show processing statistics: accuracy vs expected classifications, time per agent, confidence score distribution | Charts render with real data | P2 | M | FE-01, BE-11 | ✅ Done |
| FE-07 | Processing log viewer | Scrollable view of `processing_log.csv` with filter by agent name and log level | Log entries visible in UI | P2 | S | FE-01, DB-06 | ✅ Done |
| FE-08 | Product docs upload | Upload technical documentation (.md/.txt) into product docs RAG; view/delete existing docs; re-index into ChromaDB | Docs uploaded and indexed; chunk count shown | P1 | M | FE-01, DB-04 | ✅ Done |

---

## 🧪 QA Engineer — Automated Tests

| ID | Task | Description | Acceptance Criteria | Priority | Complexity | Depends On | Status |
|---|---|---|---|---|---|---|---|
| QA-01 | Test framework setup | Set up `pytest` with `pytest-cov`; create `tests/` folder structure mirroring `agents/` | `pytest` runs with no import errors | P0 | XS | DB-01 | 🔲 |
| QA-02 | Unit tests — CSV Reader Agent | Test CSV loading, missing column handling, encoding edge cases, empty file | All edge cases pass | P0 | S | BE-04, QA-01 | 🔲 |
| QA-03 | Unit tests — Feedback Classifier Agent | Test classification logic against a labelled fixture dataset; assert confidence score range [0, 1] | ≥ 80% accuracy on fixture; no exceptions | P0 | M | BE-05, QA-01 | 🔲 |
| QA-04 | Unit tests — Bug Analysis Agent | Test extraction of required bug fields (steps, platform, severity) from known bug text | All required fields non-null for bug items | P1 | S | BE-06, QA-01 | 🔲 |
| QA-05 | Unit tests — Feature Extractor Agent | Test feature summary and impact score extraction | Fields populated for feature request items | P1 | S | BE-07, QA-01 | 🔲 |
| QA-06 | Unit tests — Ticket Creator Agent | Assert output ticket has all required columns; validate CSV write | `generated_tickets.csv` schema matches spec | P0 | S | BE-08, QA-01 | 🔲 |
| QA-07 | Unit tests — Quality Critic Agent | Test that incomplete tickets are flagged or rewritten | Flagged tickets have `needs_review=True` | P1 | S | BE-09, QA-01 | 🔲 |
| QA-08 | Integration test — full pipeline | Run complete LangGraph pipeline on mock CSVs; validate all output files exist and match schema | `generated_tickets.csv`, `processing_log.csv`, `metrics.csv` all valid | P0 | M | BE-10, QA-01 | 🔲 |
| QA-09 | Classification accuracy test | Compare pipeline output against `expected_classifications.csv`; assert accuracy ≥ 80% | Accuracy metric logged to `metrics.csv` | P1 | M | BE-10, BE-03, QA-08 | 🔲 |
| QA-10 | Error handling tests | Inject malformed rows, empty CSVs, and API timeouts; assert pipeline does not crash | All injected errors handled gracefully | P1 | M | BE-12, QA-01 | 🔲 |
| QA-11 | UI smoke tests | Use Streamlit testing or Playwright to verify Dashboard, Config, Override pages load without errors | No page throws an exception on load | P2 | M | FE-01 – FE-07, QA-01 | 🔲 |
| QA-12 | Coverage report | Enforce ≥ 80% code coverage on `agents/` module | `pytest --cov` reports ≥ 80% | P2 | XS | QA-02 – QA-10 | 🔲 |

---

## 📦 Output Files Reference

| File | Owner | Description |
|---|---|---|
| `data/app_store_reviews.csv` | Backend API | Input: app store reviews mock data |
| `data/support_emails.csv` | Backend API | Input: support email mock data |
| `data/expected_classifications.csv` | Backend API | Ground-truth labels for evaluation |
| `data/generated_tickets.csv` | Backend API | Output: structured tickets from pipeline |
| `data/processing_log.csv` | Backend DB | Per-item processing history and decisions |
| `data/metrics.csv` | Backend API | Accuracy, throughput, and performance stats |

---

## 🗺️ Dependency Graph (Summary)

```
PM-02, PM-03, PM-04, PM-05
        │
DB-01 ──┼──────────────────────────────────────────────────────────────────┐
        │                                                                   │
       DB-03, DB-04, DB-06, DB-07                                          │
        │                                                                   │
BE-01, BE-02, BE-03                                                         │
        │                                                                   │
      BE-04 (CSV Reader)                                                    │
        │                                                                   │
      BE-05 (Classifier)                                                    │
       / \                                                                  │
   BE-06  BE-07                                                             │
(Bug)   (Feature)                                                           │
      \  /                                                                  │
      BE-08 (Ticket Creator)                                                │
        │                                                                   │
      BE-09 (Quality Critic)                                                │
        │                                                                   │
      BE-10 (LangGraph Orchestration)                                       │
        │                                                                   │
      BE-11, BE-12                                   FE-01 ─── FE-02..FE-07┘
        │                                                │
      QA-08, QA-09                               QA-11
```

---

## 🏃 Suggested Sprint Order

| Sprint | Tasks |
|---|---|
| Sprint 1 — Foundation | PM-01 – PM-05, DB-01, DB-02, DB-03, DB-07, BE-01, BE-02, BE-03, QA-01 |
| Sprint 2 — Core Agents | BE-04, BE-05, BE-06, BE-07, DB-04, DB-06, FE-01, FE-02 |
| Sprint 3 — Pipeline & UI | BE-08, BE-09, BE-10, BE-11, BE-12, FE-03, FE-04, FE-05 |
| Sprint 4 — Quality & Polish | FE-06, FE-07, QA-02 – QA-12, DB-05, PM-06 |
