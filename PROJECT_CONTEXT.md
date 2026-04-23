# CampaignPilot — Project Context

> A production-grade multi-agent system that automates the end-to-end B2B marketing campaign lifecycle — built as a portfolio project for a **Marketing Technology Manager, AI** role at Meta.

The system models how **Meta's SMB marketing team** would plan, execute, and optimize campaigns that acquire small business owners as Meta advertisers. Agents handle strategy, creative generation, performance analysis, and optimization — grounded in Meta's real benchmarks, brand guidelines, and SMB product catalog.

The differentiator is not LLM usage itself. It's the **eval infrastructure**: a golden-dataset framework with deterministic + LLM-as-judge metrics, regression detection, Langfuse observability, and a Streamlit dashboard — the kind of production-readiness patterns expected in a real MarTech environment.

**Brand context:** Meta markets its advertising products (Facebook Ads, Instagram Ads, Advantage+, WhatsApp Business API) to small and medium businesses. This system models that motion — campaigns targeting local retailers, e-commerce founders, service businesses, and multi-location SMBs.

---

## Project Status

### ✅ Completed

| Section | Files | Notes |
|---|---|---|
| Infrastructure | `docker-compose.yml`, `.env.example`, `pyproject.toml` | 5 Docker services: Postgres, ChromaDB, n8n, Langfuse, Langfuse-DB. `.env.example` now includes `ACTIVE_BRAND=meta`. |
| Database Schema | `db/schema.sql` | 9 tables + indexes + view: original 6 campaign tables **plus** `smb_advertisers`, `ab_experiments`, `ab_experiment_assignments` |
| **Brand Config System** | `brands/config.py`, `brands/meta/config.json` | Swap brands via `ACTIVE_BRAND=meta` in `.env`. Add new brand = new folder. |
| **Meta Knowledge Base** | `brands/meta/knowledge_base/` | Brand guidelines, product catalog, 4 SMB personas, Meta benchmarks — all grounded in real Meta data |
| Synthetic Campaign Data | `data/synthetic/` | 50 Meta SMB campaigns, creatives, performance events with realistic distributions (beta CTR, ad fatigue decay) |
| **SMB Advertiser Pool** | `data/synthetic/generate_smbs.py`, `data/synthetic/seed_smbs.py` | 500 synthetic SMB records across 10 industries, 40 US DMAs, 4 ad experience levels, with full demographics (revenue, employees, business age, ad spend, Meta ads history) |
| Golden Datasets | `data/golden_datasets/` | 57 labeled examples: 15 strategist + 20 creative (incl. 3 brand-safety failures) + 12 analyst SQL pairs + 10 optimizer scenarios |
| Base Agent | `agents/base_agent.py` | Agentic loop, Langfuse tracing, token tracking, cost estimation, structured error handling |
| Strategist Agent | `agents/strategist.py` | RAG + tool-use: recommends channel mix, budget split, KPIs, rationale. **Now uses brand config dynamically** |
| Creative Agent | `agents/creative.py` | Brand-safe copy generation across Facebook, Instagram, email, search. **Now uses brand config dynamically** |
| Analyst Agent | `agents/analyst.py` | Text-to-SQL with schema awareness, insight narration. **Now uses brand config dynamically** |
| Optimizer Agent | `agents/optimizer.py` | Performance vs benchmark analysis, prioritised recommendations. **Now uses brand config dynamically** |
| **A/B Testing Agent** | `agents/ab_testing_agent.py` | Stratified random assignment (industry × size × DMA tier × ad experience), power analysis (scipy.stats two-proportion z-test), balance diagnostics (chi-square + Welch's t-test), LLM interpretation of experiment design, DB persistence |
| Tools | `tools/` | ChromaDB client, PostgreSQL query tool, brand safety checker, SQL allowlist validator |
| Eval Framework | `evals/runner.py`, `evals/metrics/` | Deterministic + LLM-as-judge metrics, regression detection (>5% drop), cost tracking |
| **Measurement Dashboard** | `evals/dashboard/app.py` | Two-tab Streamlit dashboard: **Agent Evals** (score trends, regression alerts, cost) + **A/B Testing** (SMB pool distribution, experiment balance diagnostics, power analysis, covariate p-value charts) |
| Eval Rubrics | `evals/rubrics/` | Full 1–5 rubric JSON for strategist, creative, analyst agents |
| **FastAPI App — All Agents** | `api/main.py`, `api/routes/agents.py` | `POST /agents/strategist/run`, `/creative/run`, `/analyst/run`, `/optimizer/run`, `/ab-test/design`, eval trigger + status. All 5 agents now fully wired. |
| n8n Workflow | `orchestration/n8n_workflows/campaign_lifecycle.json` | 7-node lifecycle: Webhook → Strategist → Creative → Eval → Response |
| Scripts | `scripts/setup.sh`, `scripts/run_eval.sh`, `scripts/ingest_knowledge_base.py` | `ingest_knowledge_base.py` now reads from `brands/{ACTIVE_BRAND}/knowledge_base/` via brand config, writes to `{brand_id}_knowledge_base` collection |

### ⚠️ Remaining Work (in priority order)

| # | Task | Priority | Status | What to do |
|---|---|---|---|---|
| ~~1~~ | ~~End-to-end smoke test~~ | ✅ DONE | ✅ | All 6 criteria passed: DB schema, SMB pool (500), ChromaDB (49 docs), Strategist test, Eval CLI, 9 API endpoints |
| ~~2~~ | ~~Seed SMB pool~~ | ✅ DONE | ✅ | Completed: 500 SMB records seeded across 10 industries, 40 DMAs |
| ~~3~~ | ~~Run A/B experiment smoke test~~ | ✅ DONE | ✅ | Completed: Power analysis + stratified sampling validated |
| ~~4~~ | ~~Wire Creative/Analyst/Optimizer to API~~ | ✅ DONE | ✅ | All 4 agents wired to `api/routes/agents.py` |
| ~~5~~ | ~~Wire A/B Testing Agent to API~~ | ✅ DONE | ✅ | `POST /agents/ab-test/design` endpoint active |
| ~~6~~ | ~~Wire all agents to eval CLI~~ | ✅ DONE | ✅ | `evals/runner.py` dispatches all 4 agents with correct metrics |
| ~~7~~ | ~~Build Strategist UI Tab~~ | ✅ DONE | ✅ | New `app.py` with Gong+Meta design + full real-time observability (threaded, event-streamed). Launch at `http://localhost:8501` |
| **8** | **Build Creative UI Tab** | 🔴 HIGH | ⏳ PENDING | Generate ad variants, brand safety checks, preview gallery with tone controls |
| **9** | **Build Analyst UI Tab** | 🔴 HIGH | ⏳ PENDING | Natural language question input, SQL generation + execution display, result visualization with charts |
| **10** | **Build Optimizer UI Tab** | 🔴 HIGH | ⏳ PENDING | Campaign selection, performance analysis vs benchmarks, drag-to-adjust budget recommendations |
| **11** | **Build A/B Testing UI Tab** | 🔴 HIGH | ⏳ PENDING | Experiment design form, power analysis visualization, stratification display, sample size calculator |
| **12** | **Wire all UI tabs to real agents** | 🔴 HIGH | ⏳ PENDING | Connect each Streamlit form to corresponding agent via API or direct import |
| 13 | **Langfuse smoke test** | 🟡 MEDIUM | ⏳ PENDING | After agent runs, verify traces appear at `http://localhost:3000` |
| 14 | **n8n workflow test** | 🟡 MEDIUM | ⏳ PENDING | Import `campaign_lifecycle.json` into n8n UI (localhost:5678), activate, fire test webhook |
| 15 | **Add `amex/` brand stub** | 🟢 LOW | ⏳ PENDING | Create `brands/amex/config.json` + knowledge base folder to demonstrate brand swappability |
| 16 | **pytest suite** | 🟢 LOW | ⏳ PENDING | `tests/test_deterministic_metrics.py`, `tests/test_safety_checker.py`, `tests/test_sql_validator.py` |
| 17 | **Alembic migrations** | 🟢 LOW | ⏳ PENDING | Replace raw `schema.sql` with Alembic for schema versioning |

---

## Architecture

```
                        ┌─────────────────────────────┐
                        │   ACTIVE_BRAND = meta        │
                        │   brands/meta/config.json     │
                        │   brands/meta/knowledge_base/ │
                        └──────────────┬──────────────┘
                                       │  BrandConfig loaded at agent init
                                       ▼
User / n8n Webhook ──▶ FastAPI (port 8000)
                              │
                    ┌─────────┴──────────┐
                    ▼                    ▼
           Agent Layer              campaigns/, evals/
     ┌──────────────────────┐       routes return data
     │  Strategist          │       from Postgres
     │  Creative            │
     │  Analyst             │
     │  Optimizer           │
     └────────┬─────────────┘
              │  tool calls
      ┌───────┴────────┐
      ▼                ▼
 ChromaDB          PostgreSQL
 port 8000         port 5432
 (RAG / KB)        (campaigns,
 collection:        performance_events,
 meta_knowledge     eval_runs, ...)
 _base
      │
      ▼
 Langfuse           Streamlit
 port 3000          port 8501
 (traces,           (eval dashboard,
  token cost)        regression alerts)
      │
      ▼
 n8n
 port 5678
 (visual orchestration,
  webhook trigger)
```

---

## Brand Configuration System

The brand is fully modular. One env variable controls everything:

```env
ACTIVE_BRAND=meta   # or: amex, hubspot, etc.
```

Each brand lives in its own folder:

```
brands/
├── config.py                      ← load_brand() + BrandConfig dataclass
├── meta/
│   ├── config.json                ← company name, products, prohibited phrases, voice summary
│   └── knowledge_base/
│       ├── brand_guidelines.md    ← Meta SMB marketing voice & tone
│       ├── product_catalog.json   ← Meta Ads, Advantage+, Business Suite, WhatsApp API
│       ├── audience_personas.json ← 4 SMB personas: Local Retailer, E-Commerce Founder, Service Biz, Multi-Location
│       └── industry_benchmarks.json ← Real Meta benchmarks: ROAS 2.19x, CTR 2.19%, CPM $13.48
└── (future brands here)
```

To add a new brand (e.g. Amex):
1. `mkdir brands/amex/knowledge_base/`
2. Create `brands/amex/config.json` following the same schema as `brands/meta/config.json`
3. Populate the 4 knowledge base files
4. Set `ACTIVE_BRAND=amex` in `.env`
5. Re-run `python scripts/ingest_knowledge_base.py` to load the new KB into ChromaDB

No code changes needed. The agents, ingestion script, and safety checker all read from `BrandConfig` at runtime.

---

## Quick Start

```bash
# 1. Clone and configure
git clone <repo> && cd campaignpilot
cp .env.example .env
# Edit .env: add ANTHROPIC_API_KEY, confirm ACTIVE_BRAND=meta

# 2. Boot everything (Docker, schema, synthetic data, ChromaDB ingestion)
./scripts/setup.sh
```

The setup script handles everything. See the Prerequisites section if it fails.

---

## Prerequisites

- **Docker Desktop** running (tested with Docker 24+)
- **uv** installed: `curl -LsSf https://astral.sh/uv/install.sh | sh`
- **ANTHROPIC_API_KEY** — required. Get from [console.anthropic.com](https://console.anthropic.com)
- **Langfuse keys** — optional. Tracing silently disabled if not set. Get from [cloud.langfuse.com](https://cloud.langfuse.com) or use the self-hosted instance started by Docker.

---

## Environment Variables

```env
ANTHROPIC_API_KEY=sk-ant-...           # Required
ACTIVE_BRAND=meta                      # Controls which brand KB + config to load

DATABASE_URL=postgresql://cp_user:cp_password@localhost:5432/campaignpilot
CHROMA_HOST=localhost
CHROMA_PORT=8000

LANGFUSE_PUBLIC_KEY=                   # Optional
LANGFUSE_SECRET_KEY=                   # Optional
LANGFUSE_HOST=http://localhost:3000

N8N_HOST=http://localhost:5678
POSTGRES_USER=cp_user
POSTGRES_PASSWORD=cp_password
POSTGRES_DB=campaignpilot
```

---

## Docker Services

```bash
docker compose up -d      # start all services
docker compose ps         # check status
docker compose logs -f    # stream logs
```

| Service | Port | Purpose |
|---|---|---|
| `postgres` | 5432 | Main application database |
| `chromadb` | 8000 | Vector store for RAG (brand KB + creative examples) |
| `n8n` | 5678 | Visual workflow orchestration |
| `langfuse-db` | 5433 | Langfuse's own Postgres (separate from app DB) |
| `langfuse` | 3000 | LLM observability UI |

---

## Project Structure

```
campaignpilot/
├── README.md
├── docker-compose.yml
├── .env.example
├── pyproject.toml
│
├── brands/                            ← Brand configuration system
│   ├── config.py                      ← BrandConfig dataclass + load_brand()
│   └── meta/
│       ├── config.json                ← Meta brand metadata, products, prohibited phrases
│       └── knowledge_base/
│           ├── brand_guidelines.md    ← Meta SMB marketing voice & writing rules
│           ├── product_catalog.json   ← Meta Ads, Advantage+, Business Suite, WhatsApp API
│           ├── audience_personas.json ← 4 SMB buyer personas
│           └── industry_benchmarks.json ← Real Meta benchmarks (ROAS, CTR, CPM, CPA)
│
├── data/
│   ├── synthetic/                     ← Synthetic data generators
│   │   ├── generate_campaigns.py      ← 50 Meta SMB marketing campaigns
│   │   ├── generate_creatives.py      ← 3-5 ad variants per campaign/channel
│   │   ├── generate_smbs.py           ← 500 SMB advertiser records (industry, DMA, demographics)
│   │   ├── seed_db.py                 ← Inserts campaigns + performance events (beta dist.)
│   │   └── seed_smbs.py               ← Inserts 500 SMB records into smb_advertisers
│   │
│   └── golden_datasets/               ← ⭐ Most important files — eval ground truth
│       ├── strategist_golden.json     ← 15 examples (acquisition, re-engagement, upsell, brand)
│       ├── creative_golden.json       ← 20 examples incl. 3 brand-safety failures
│       ├── analyst_golden.json        ← 12 SQL Q&A pairs (simple → CTE → window functions)
│       └── optimizer_golden.json      ← 10 scenarios (underperform → scale → rebalance)
│
├── db/
│   └── schema.sql                     ← PostgreSQL schema: 6 tables + indexes + view
│
├── agents/
│   ├── base_agent.py                  ← Agentic loop, Langfuse tracing, AgentResult dataclass
│   ├── strategist.py                  ← Channel mix, budget split, KPIs for Meta SMB campaigns
│   ├── creative.py                    ← Brand-safe ad copy for Facebook/Instagram/email/search
│   ├── analyst.py                     ← Text-to-SQL + narrative insight generation
│   ├── optimizer.py                   ← Performance vs Meta benchmarks, prioritised actions
│   └── ab_testing_agent.py            ← Stratified A/B group selection, power analysis, balance validation
│
├── tools/
│   ├── vector_search.py               ← ChromaDB: ingest_document, search, ingest_batch
│   ├── db_query.py                    ← Postgres: execute_query, get_campaign_history, metrics
│   ├── safety_checker.py              ← Brand phrase detection + unsubstantiated claims
│   └── sql_generator.py              ← SQL allowlist validator (SELECT-only, known tables)
│
├── evals/
│   ├── runner.py                      ← EvalRunner: run(), regression detection, Rich report
│   ├── metrics/
│   │   ├── deterministic.py           ← CompletenessMetric, BudgetRealismMetric, SqlAccuracyMetric, SafetyMetric
│   │   ├── llm_judge.py               ← StrategicCoherenceMetric, BrandVoiceMetric, InsightQualityMetric
│   │   └── brand_safety.py            ← BrandSafetyMetric (SafetyChecker wrapper)
│   ├── rubrics/
│   │   ├── strategist_rubric.json     ← strategic_coherence (40%) + completeness (30%) + budget_realism (30%)
│   │   ├── creative_rubric.json       ← brand_voice + safety + completeness
│   │   └── analyst_rubric.json        ← insight_quality + sql_accuracy + completeness
│   └── dashboard/
│       └── app.py                     ← Streamlit two-tab dashboard: Agent Evals + A/B Testing tab (SMB pool, balance diagnostics, power analysis)
│
├── api/
│   ├── main.py                        ← FastAPI app, lifespan, CORS, health check
│   └── routes/
│       ├── agents.py                  ← POST /agents/strategist/run, /eval/run, /eval/status
│       ├── campaigns.py               ← GET/POST campaigns, performance, creatives
│       └── evals.py                   ← GET eval runs, agent scores, trends
│
├── orchestration/
│   └── n8n_workflows/
│       └── campaign_lifecycle.json    ← Import into n8n: Webhook → Strategist → Creative → Eval
│
└── scripts/
    ├── setup.sh                       ← Full bootstrap: Docker → schema → seed → ingest KB
    ├── ingest_knowledge_base.py       ← Loads brands/meta/knowledge_base/ into ChromaDB
    └── run_eval.sh                    ← Wrapper: bash scripts/run_eval.sh strategist
```

---

## What Each Agent Does

| Agent | Role | Key Tools | Output |
|---|---|---|---|
| **Strategist** | Recommends channel mix, budget split, KPIs, and rationale for a Meta SMB campaign | `search_knowledge_base`, `get_campaign_history`, `get_benchmark_data` | `{recommended_channels, budget_split, primary_message_pillar, kpis, rationale, risks}` |
| **Creative** | Writes brand-safe ad copy variants per channel, validated against Meta's prohibited phrases | `search_knowledge_base`, `search_creative_examples`, `check_brand_safety` | `{variants: [{headline, body, cta, tone, safety_check}], rationale}` |
| **Analyst** | Answers marketing analytics questions by generating and executing SQL, then narrating insight | `execute_sql`, `get_schema_info`, `search_knowledge_base` | `{sql, results, narrative_insight, key_finding, recommended_action}` |
| **Optimizer** | Compares live campaign metrics vs Meta benchmarks (ROAS 2.19x, CTR 2.19%) and recommends actions | `get_campaign_performance`, `get_benchmark_data`, `save_recommendation` | `{overall_health, recommendations: [{type, priority, specific_actions, expected_impact}]}` |

All agents inherit from `BaseAgent` which provides: the Claude tool-use agentic loop, Langfuse trace logging per generation, input/output token counting, cost estimation, and structured error handling (never crashes — always returns `AgentResult` with `success=False` on error).

---

## Eval Framework

### How It Works

1. Load a golden dataset (JSON array of labeled `{input, expected_output, quality_dimensions}` examples)
2. For each example, run the agent — get back an `AgentResult`
3. Score the output against each configured metric
4. Aggregate: mean, min, max, p25, p75, pass rate per metric
5. Compare vs last baseline in `eval_runs` table — flag any metric dropping >5%
6. Save results to Postgres; print Rich console report

### Metrics

**Deterministic (zero LLM cost):**

| Metric | Scale | Pass Threshold | What it checks |
|---|---|---|---|
| `CompletenessMetric` | 0–1 | 0.8 | All required output fields present and non-empty |
| `BudgetRealismMetric` | 0–1 | 0.7 | `budget_split` sums to ~1.0, no channel < 5% or > 80% |
| `SqlAccuracyMetric` | 0–1 | 0.6 | Valid SELECT, only allowed tables, executes without error |
| `SafetyMetric` | 0 or 1 | 1.0 | No Meta prohibited phrases in output |

**LLM-as-Judge (uses `claude-haiku-4-5-20251001` — ~$0.05/full eval run):**

| Metric | Scale | Pass Threshold | Full rubric in code? |
|---|---|---|---|
| `StrategicCoherenceMetric` | 1–5 | 3.0 | ✅ What earns 1/2/3/4/5 defined verbatim |
| `BrandVoiceMetric` | 1–5 | 3.0 | ✅ Checks Meta voice: outcome-first, specific numbers, no prohibited phrases |
| `InsightQualityMetric` | 1–5 | 3.0 | ✅ 1=restates numbers, 5=finding+cause+impact+action+tradeoff |

Each judge call logs the model's full reasoning so you can audit why it scored what it did.

### Running Evals

```bash
# Full eval with LLM judge
uv run python evals/runner.py --agent strategist \
  --dataset data/golden_datasets/strategist_golden.json

# Fast eval — deterministic metrics only (free, no API cost)
uv run python evals/runner.py --agent strategist \
  --dataset data/golden_datasets/strategist_golden.json --no-llm-judge

# Shorthand
bash scripts/run_eval.sh strategist
bash scripts/run_eval.sh creative
```

### Eval Dashboard

```bash
uv run streamlit run evals/dashboard/app.py
# → http://localhost:8501
```

Shows: latest scores per agent/metric (bar chart), score trends over time (line chart), failed examples with drill-down, cost per eval run, red regression alert banner.

---

## API Reference

```bash
uv run uvicorn api.main:app --reload --port 8000
# Interactive docs → http://localhost:8000/docs
```

**Health check:**
```bash
curl http://localhost:8000/health
```

**Run Strategist (Meta SMB campaign brief):**
```bash
curl -X POST http://localhost:8000/agents/strategist/run \
  -H "Content-Type: application/json" \
  -d '{
    "campaign_goal": "Acquire 500 new SMB advertisers in the restaurant vertical at under $150 cost-per-new-advertiser, Q4",
    "budget_usd": 75000,
    "timeline_days": 45,
    "target_segment": "Restaurant owners with 1-10 locations who have never run a Meta ad"
  }'
```

**Trigger eval run (async):**
```bash
curl -X POST http://localhost:8000/agents/eval/run \
  -H "Content-Type: application/json" \
  -d '{
    "agent_name": "strategist",
    "dataset_path": "data/golden_datasets/strategist_golden.json",
    "use_llm_judge": false
  }'
# Returns eval_run_id → poll GET /agents/eval/status/{id}
```

**Campaign data:**
```bash
curl "http://localhost:8000/campaigns?status=completed&limit=10"
curl "http://localhost:8000/campaigns/1/performance"
curl "http://localhost:8000/evals/agents/strategist/latest"
```

---

## n8n Workflow

File: `orchestration/n8n_workflows/campaign_lifecycle.json`

```
POST /webhook/campaign-brief-request
  └─▶ Run Strategist Agent  (→ FastAPI :8000)
        └─▶ Success?
              ├─▶ YES: Run Creative Agent → Wait 5s → Trigger Eval → Return full brief
              └─▶  NO: Return 500 with error details
```

To activate:
1. Open `http://localhost:5678`
2. New workflow → Import from file → `campaign_lifecycle.json`
3. Activate, then test:
```bash
curl -X POST http://localhost:5678/webhook/campaign-brief-request \
  -H "Content-Type: application/json" \
  -d '{"campaign_goal":"Acquire new e-commerce SMB advertisers","budget_usd":50000,"timeline_days":30,"target_segment":"E-commerce founders with Shopify stores"}'
```

---

## Success Criteria Checklist

All 6 must pass before this is considered done:

- [ ] **1. `./scripts/setup.sh` completes without errors** — Docker up, schema applied, 50 campaigns seeded, ChromaDB ingested
- [ ] **2. Ingest confirmation** — `python scripts/ingest_knowledge_base.py` prints doc count for `meta_knowledge_base` and `creative_examples` collections
- [ ] **3. Seed confirmation** — `python data/synthetic/seed_db.py` shows 50 campaigns + ~20k performance events inserted
- [ ] **4. Strategist smoke test:**
  ```bash
  uv run python agents/strategist.py
  # Prints a JSON campaign brief for Meta SMB acquisition — no errors
  ```
- [ ] **5. Eval run:**
  ```bash
  uv run python evals/runner.py --agent strategist \
    --dataset data/golden_datasets/strategist_golden.json --no-llm-judge
  # Prints Rich score table — no crashes
  ```
- [ ] **6. Dashboard loads** at `http://localhost:8501` and shows the eval run results

---

## Handover Notes for New AI / Developer

Read this section first if you're picking this project up.

### Current state (as of 2026-04-22)

**Infrastructure & Agents:** 100% complete. All 5 agents working, API wired, evals framework validated.

**User Interface:** In progress. Building new **Meta-styled Streamlit dashboard** (`app.py`) to replace disparate Swagger/old dashboard.

| Layer | Status | Notes |
|---|---|---|
| Brand config system (`brands/`) | ✅ Done | Fully modular |
| Meta knowledge base (4 files) | ✅ Done | Real Meta data + benchmarks |
| Golden datasets | ✅ Done | 57 labeled examples across 4 agents |
| Synthetic data generators | ✅ Done | 50 Meta campaigns + 500 SMB advertiser records |
| Agent system prompts | ✅ Done | All 4 agents call `get_active_brand()` dynamically |
| `ingest_knowledge_base.py` | ✅ Done | Reads from `brands/{ACTIVE_BRAND}/knowledge_base/` |
| `.env.example` | ✅ Done | `ACTIVE_BRAND=meta` configured |
| SMB advertiser database | ✅ Done | 500 records seeded |
| A/B Testing Agent | ✅ Done | Power analysis + stratification validated |
| FastAPI + 9 Endpoints | ✅ Done | All agents + eval runner wired |
| **New Dashboard UI** (`app.py`) | 🚀 IN PROGRESS | Strategist tab complete. Creative, Analyst, Optimizer, A/B tabs pending |
| Old Measurement Dashboard | ⚠️ Deprecated | `evals/dashboard/app.py` replaced by unified `app.py` |

### Step-by-step: what to do next

**Step 1 — Boot infrastructure and seed all data**
```bash
./scripts/setup.sh            # Docker up → schema → campaign data → KB ingest
python data/synthetic/seed_smbs.py   # seed 500 SMB advertiser records
```

**Step 2 — Run A/B experiment smoke test**
```bash
python agents/ab_testing_agent.py
# Uses MockDB — no live Postgres needed
# Prints ExperimentResult with power analysis + balance table
```

**Step 3 — View the measurement dashboard**
```bash
uv run streamlit run evals/dashboard/app.py
# Tab 1: Agent Evals (score trends, regression alerts)
# Tab 2: A/B Testing (SMB pool, experiment balance, power analysis)
```

**Step 4 — Wire remaining agents to API** (`api/routes/agents.py`)

Add endpoints for Creative, Analyst, Optimizer (same pattern as Strategist) and a new A/B endpoint:
```
POST /agents/creative/run
POST /agents/analyst/run
POST /agents/optimizer/run
POST /agents/ab-test/design   ← accepts ExperimentConfig, returns ExperimentResult JSON
```

**Step 5 — Wire all agents to eval CLI**

`evals/runner.py` `__main__` block: add dispatch for creative, analyst, optimizer with correct metric sets.

### Key files to read (in order)

1. `brands/meta/config.json` — understand what Meta is marketing and to whom
2. `brands/meta/knowledge_base/brand_guidelines.md` — the voice rules all copy must follow
3. `agents/base_agent.py` — the agentic loop every agent shares
4. `agents/strategist.py` — most complete agent; reference implementation for the others
5. `evals/runner.py` — the eval harness; understand `EvalReport` and `ExampleResult`
6. `data/golden_datasets/strategist_golden.json` — what good vs mediocre strategy looks like in Meta's SMB context

---

## Tech Decisions

**Why Meta, not a fictional company?**
The role being targeted is Meta's Marketing Technology Manager, AI. A portfolio project that demonstrates understanding of Meta's actual SMB product portfolio, real published benchmarks (ROAS 2.19x, Advantage+ 32% lower CPA), and the real buyer personas Meta targets is more signal-rich than a fictional brand.

**Why multi-agent over one big prompt?**
Discrete agents with narrow roles can be evaluated, improved, and swapped independently. If the Creative agent's brand voice score drops, you fix `agents/creative.py` — not a 5,000-token monolith prompt. The eval framework makes regressions visible immediately.

**Why self-hosted eval instead of LangSmith/Braintrust?**
At CI/CD velocity, external eval services add cost and network dependency that compounds. The local harness with Postgres backend gives full control over thresholds, custom metric logic, and cost tracking — and runs free on every commit.

**Why ChromaDB + Postgres?**
Structured relational data (campaigns, events, eval runs) needs JOINs and aggregations → Postgres. Unstructured document retrieval (brand guidelines, personas, creative examples) needs semantic search → ChromaDB. One tool for both would be worse at both.

**Why n8n for orchestration?**
For a Marketing Technology Manager role, demonstrating a system legible to non-engineers matters. n8n gives a visual execution graph that a marketing ops team can observe, debug, and extend without writing code.

**Why `claude-haiku-4-5-20251001` for LLM-as-judge?**
Running 57 eval examples × 3 judge metrics costs ~$0.05 with Haiku vs ~$0.20 with Sonnet. Over hundreds of eval runs in a CI pipeline, that delta is meaningful. Haiku is fully capable of the 1–5 scoring task with a detailed rubric.

---

## Unified Dashboard UI (In Progress)

### Overview

Built **new `app.py`** (root level) with Meta-inspired styling to replace disparate Swagger API docs + old `evals/dashboard/app.py`.

**Design philosophy:**
- Single entry point for all agent interactions
- Real-time execution visibility (tool calls, tokens, latency)
- Meta-like color scheme (blues, clean typography, card-based layout)
- Sidebar navigation between agents
- Output displays structured JSON + human-readable summaries

**Launch:**
```bash
PYTHONPATH=. STREAMLIT_CLIENT_TELEMETRY_ENABLED=false \
  python -m streamlit run app.py --server.port 8501 --server.headless true
# → http://localhost:8501
```

### Completed: Strategist Tab + Full Observability

File: `app.py` (lines 1–700+)

**Design system:**
- **Gong.io energy + Meta minimalism**: Pure white/light gray surfaces, rounded-2xl/3xl cards, thin borders + soft shadows
- **Typography**: Plus Jakarta Sans (headlines, 900 weight, -0.04em tracking), Inter (body)
- **Gradients**: Indigo → pink → amber on hero text; purple-to-pink on CTAs
- **Glassmorphism navbar**: `backdrop-filter: blur(20px) saturate(180%)`
- **Floating data cards** in hero with `float` animation
- **Bento box grid** for agent selection and telemetry
- **Hover states**: `-translate-y-1` + expanded shadow, 200ms ease transitions
- **Pulse-dot animations** for "live" indicators

**Real-time observability (NEW):**
The agent execution is now fully observable:
- `BaseAgent` has an `event_callback` param that emits events at 7 lifecycle points:
  - `agent_start` — Agent initialized
  - `turn_start` — New agentic loop turn
  - `llm_call_start` / `llm_call_end` — Claude API calls with tokens & stop_reason
  - `tool_call_start` — Tool invoked with input
  - `tool_call_end` — Tool completed with latency + output preview
  - `agent_complete` — Final summary
- UI runs agent in a background thread, streams events via `Queue`
- Live panel shows each event as a timeline card with:
  - Colored icon per event type (LLM=blue, tool=amber, complete=green)
  - Elapsed time `+X.XXs` from start
  - Tool name + input (monospace) on call start
  - Output preview + latency on call end
  - Token counts + stop reason on LLM calls
- Auto-scrolls, max 500px height, polls queue every 300ms

**Features implemented:**
1. **Input Form** (2-column layout)
   - Campaign goal (textarea)
   - Budget (number input with slider)
   - Timeline (0–365 days, slider control)
   - Target segment (text input)

2. **Real-Time Execution** (threaded + queued)
   - Every tool call streams into the UI as it happens
   - Every LLM turn shows token breakdown + latency
   - Timeline grows in real-time with +elapsed timestamps
   - Monospace display of tool args/outputs for debugging

3. **Campaign Brief Output** (on success)
   - **Metrics row**: Tokens (input/output), latency, total
   - **Channel card**: Recommended channels
   - **Budget split card**: $ amounts + percentages
   - **Message pillar card**: Primary marketing message
   - **KPIs section**: Metric cards (lead flow, CAC, ROAS, etc.)
   - **Risks section**: Warning cards for identified risks
   - **Rationale expander**: Full reasoning from agent
   - **Langfuse trace link**: Deep dive link to observability
   - **Raw JSON viewer**: Expander with full output JSON

4. **Error Handling**
   - Displays agent errors if `result.success == False`
   - Shows exception stack trace for debugging

### Pending: Creative Tab

**What to build:**
1. **Input Form**
   - Channel selector (Facebook, Instagram, Email, Search, LinkedIn)
   - Product/service name
   - Persona selector (dropdown from golden dataset or free text)
   - Tone selector (professional, friendly, urgent, educational)
   - Key message (textarea)
   - Num variants slider (1–5)

2. **Execution Display**
   - Tool calls (search creative examples, check brand safety)
   - Brand safety check results

3. **Output Display**
   - **Variants grid** (3 columns): Each card shows:
     - Headline
     - Body copy
     - CTA button text
     - Tone badge (color-coded)
     - Safety indicator (✅ / ⚠️ / ❌)
   - **Safety findings** (table if violations found)
   - **Rationale expander**

### Pending: Analyst Tab

**What to build:**
1. **Input Form**
   - Question textarea: "What is my ROAS by channel in the last 30 days?"
   - Auto-complete suggestions from golden dataset

2. **Execution Display**
   - SQL generation (shows the generated SQL in a code block)
   - SQL execution status (✅ success / ❌ error)

3. **Output Display**
   - **Results table** (markdown table from SQL output)
   - **Insights section**:
     - Key finding (bold)
     - Recommended action
     - Supporting data (bullet points)
   - **Visualization** (Plotly chart if applicable — e.g., ROAS by channel as bar chart)
   - **Raw data expander** (full SQL results JSON)

### Pending: Optimizer Tab

**What to build:**
1. **Input Form**
   - Campaign selector (dropdown from DB: campaign_id + name)
   - Remaining budget (number input)
   - Days remaining (0–365 slider)

2. **Execution Display**
   - Tool calls (fetch performance, benchmarks)

3. **Output Display**
   - **Overall health card** (status badge: Green/Yellow/Red + health score)
   - **Performance table**: Current metrics vs Meta benchmarks
     - Columns: Metric, Current, Benchmark, Delta %, Status
     - Rows: ROAS, CTR, CPC, CAC, COACPC (conversion rate)
   - **Recommendations section** (cards, one per recommendation):
     - Priority badge (High/Medium/Low, color-coded)
     - Type (budget, creative, audience, etc.)
     - Description
     - Expected impact (% uplift, $ savings)
     - Specific actions (bullet points)
   - **Rationale expander**

### Pending: A/B Testing Tab

**What to build:**
1. **Input Form**
   - Experiment name (text)
   - Campaign link (optional dropdown)
   - Filters (optional JSON input for SMB pool filtering)
   - Stratify on (multi-select: industry, size, DMA, ad experience)
   - Test fraction (slider 0.1–0.9)
   - Baseline conversion rate (slider)
   - MDE (minimum detectable effect, slider)
   - MDE type (relative vs absolute, radio)
   - Desired power (slider 0.5–0.99)
   - Significance level (slider 0.01–0.20)
   - Persist to DB (checkbox)

2. **Execution Display**
   - Status: "Validating pool...", "Computing stratification...", etc.
   - Progress: sample size calculations

3. **Output Display** (ExperimentResult)
   - **Power summary card**: n per arm, total n, power achieved, beta, effect size detectable
   - **Sample size breakdown** (table):
     - Control arm: n, expected baseline conversions
     - Test arm: n, expected conversions at MDE
   - **Stratification table**: Groups (industry × size × DMA × experience), counts, balance checks (chi-sq p-value, Welch's t-test p-values)
   - **Covariate balance plots** (Plotly):
     - Histogram of SMB sizes: control vs test
     - Histogram of ad spend: control vs test
   - **Recommended actions** (if imbalance detected)
   - **Raw design JSON** expander

### Style Reference

**Colors (Meta-inspired):**
```
Primary: #0A66C2        (LinkedIn/Meta blue)
Secondary: #1877F2     (Meta brand blue)
Accent: #FF6B6B        (Alert red)
Success: #31A24C       (Green)
BG Light: #F0F2F5      (Sidebar, cards)
BG Darker: #E4E6EB     (Borders)
Text Primary: #050505  (Almost black)
Text Secondary: #65676B (Medium gray)
```

**Components:**
- Headers: Gradient blue backgrounds
- Cards: White background, subtle shadow, rounded corners (8px)
- Buttons: Solid blue, hover darkens
- Inputs: Minimal style, light border
- Status badges: Color-coded (green/yellow/red)
- Tool calls: Monospace, light gray background, left blue border

---

## Known Limitations

- **No API authentication** — all endpoints open. Add API key middleware before any public deployment.
- **Eval result store is in-memory** — background eval results in `api/routes/agents.py` reset on restart. Needs Postgres persistence.
- **ChromaDB uses default embeddings** — the built-in sentence transformer is fine for a portfolio project. For production, use `text-embedding-3-small` via the OpenAI or Anthropic embedding API for better retrieval quality.
- **n8n workflow uses `host.docker.internal`** — works on Mac/Windows Docker Desktop. On Linux, replace with the actual host IP or Docker network service names.
- **API has only Strategist endpoint** — Creative, Analyst, Optimizer, and A/B Testing agent endpoints still need to be wired up.
- **Synthetic data uses `random.seed(42)`** — deterministic and reproducible, but not truly representative of production variance. Real campaign data will produce different agent behavior.
