# Agentic Order Management

An end-to-end **agentic order-management assistant** built on the Brazilian E-Commerce
Public Dataset by Olist. The assistant combines a **LangGraph** agent powered by Google
**Gemini**, **RAG** over synthetic demo business policies (via **ChromaDB + Sentence
Transformers**), and deterministic exception/dashboard analytics over a **SQLite** store.
Both a **FastAPI REST API** and a self-contained **Jupyter Notebook** walkthrough are
provided.

> **Disclaimer:** Policy documents and exception rules in this project are *synthetic
> demo business rules* for a portfolio demo. They are **not** official Olist policies.
> Exception evaluations and eligibility answers should always be labelled as such.

---

## Project Highlights

| Capability | How it works |
|---|---|
| 🧠 **LLM Agent** | LangGraph `StateGraph` with tool-calling Gemini; tool-node routing and memory checkpoints |
| 🗂️ **Order tooling** | 10 SQLAlchemy-backed tools for order status, details, items, payments, delivery, reviews, customer orders, search, exception checks, and simulated support tickets |
| 📚 **RAG for policies** | Local ChromaDB + `all-MiniLM-L6-v2` embeddings over 8 synthetic policy documents |
| ⚠️ **Exception engine** | Deterministic rules flag DELIVERY_DELAY, SHIPPED_NOT_DELIVERED, PAYMENT_MISMATCH, APPROVAL_SLOW, etc. |
| 📊 **Dashboard** | Aggregated order counts by status and exception totals |
| 🌐 **REST API** | FastAPI with `/api/chat`, `/api/orders/*`, `/api/support-tickets`, `/api/dashboard` |
| 📒 **Notebook demo** | `Agentic_Order_Management.ipynb` – step-by-step walkthrough with safe execution traces |
| 🧪 **Tests** | Pytest suite covering DB init, row counts, tools, exception rules, and tickets |

---

## Repository Structure

```
Project_order_managment/
├── Agentic_Order_Management.ipynb   # Self-contained end-to-end walkthrough
├── requirements.txt                 # Python dependencies
├── pytest.ini                       # pytest config
├── .env.example                     # Env-var template (copy to .env)
│
├── backend/
│   ├── main.py                      # FastAPI entrypoint (CORS + /health)
│   ├── config.py                    # Pydantic Settings from .env
│   ├── logging_setup.py             # Structured logger factory
│   │
│   ├── agent/
│   │   ├── graph.py                 # LangGraph state graph, run_agent(), safe traces
│   │   ├── llm.py                   # Gemini chat-model builder
│   │   └── prompts.py               # System prompt with guardrails
│   │
│   ├── api/
│   │   └── routes.py                # /api/chat, /api/orders/{id}, /api/dashboard, ...
│   │
│   ├── database/
│   │   ├── base.py                  # Declarative Base
│   │   ├── models.py                # SQLAlchemy ORM models (Order, Customer, Ticket, ...)
│   │   ├── session.py               # Engine / SessionLocal / init helpers
│   │   └── import_data.py           # Repeatable CSV → SQLite import
│   │
│   ├── rag/
│   │   ├── ingest.py                # Markdown chunking + ChromaDB upsert
│   │   └── retriever.py             # search_business_policies_tool + retrieve_policies()
│   │
│   ├── schemas/
│   │   └── api.py                   # Pydantic schemas for REST requests / responses
│   │
│   ├── services/
│   │   ├── order_service.py         # All order/customer/payment/review queries
│   │   ├── exception_service.py     # Deterministic demo exception rules
│   │   ├── ticket_service.py        # Simulated local support tickets
│   │   └── dashboard_service.py     # Aggregated dashboard metrics
│   │
│   └── tools/
│       └── order_tools.py           # 11 LangChain tools + ORDER_TOOLS registry
│
├── dataset/                         # Olist CSV files (9 CSVs)
├── knowledge_base/                  # Synthetic demo policy markdown docs
│   ├── shipping_policy.md
│   ├── return_policy.md
│   ├── refund_policy.md
│   ├── cancellation_policy.md
│   ├── payment_policy.md
│   ├── customer_support_policy.md
│   ├── delivery_sla.md
│   └── exception_handling.md
│
├── tests/
│   ├── conftest.py                  # Sample-order DB fixtures
│   └── test_database_and_tools.py
│
└── docs/
    └── dataset_analysis.md
```

---

## Tech Stack

| Layer | Library |
|---|---|
| Runtime | Python 3.11+ |
| API | **FastAPI** + Uvicorn |
| ORM | **SQLAlchemy 2.x** |
| Database | **SQLite** (file at `data/olist.db`) |
| LLM | **Google Gemini** via `langchain-google-genai` |
| Agent framework | **LangChain Core** + **LangGraph** (StateGraph, ToolNode, MemorySaver) |
| Vector store | **ChromaDB** (persistent, `data/chroma`) |
| Embeddings (local) | **Sentence-Transformers** `all-MiniLM-L6-v2` |
| Data | **Pandas** (CSV ingestion) |
| Validation / config | **Pydantic v2** + `pydantic-settings` + `python-dotenv` |
| Testing | **pytest** |

---

## Installation

### 1. Prerequisites

- **Python 3.11** or newer
- A **Google AI Studio** API key with Gemini access (see `.env.example`)
- The Olist dataset already placed under `dataset/` (the 9 CSVs are included in the repo)

### 2. Clone / navigate

```bash
cd Project_order_managment
```

### 3. Create a virtual environment

**Windows (PowerShell):**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**macOS / Linux (Bash):**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 4. Install dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

> ⏱️ First-time note: `sentence-transformers` and `tf-keras` are large. Subsequent
> imports will use a cached model; the initial embedding-model download runs on the
> first RAG call.

### 5. Configure the environment

Copy the template and set **your own** `GEMINI_API_KEY`:

```bash
# copy template
cp .env.example .env
```

Edit `.env` with your real key:

```dotenv
# .env
GEMINI_API_KEY=your_real_google_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash

# Optional overrides (defaults shown):
# DATABASE_URL=sqlite:///./data/olist.db
# CHROMA_PATH=./data/chroma
# DATASET_DIR=./dataset
# KNOWLEDGE_BASE_DIR=./knowledge_base
# DATASET_AS_OF_DATE=2018-10-17
# LONG_DELIVERY_DAYS=30
# AGENT_RECURSION_LIMIT=12
# LOG_LEVEL=INFO
```

> 🔐 **Security rule:** Never commit `.env` or print keys to logs / notebooks. The
> `.gitignore` already excludes `.env`, `.venv/`, `data/`, and `*.db`.

### 6. Initialize the SQLite database (Olist import)

```bash
python -m backend.database.import_data
```

This:
1. Validates that all 9 required Olist CSVs exist in `dataset/` with correct columns.
2. Drops & recreates tables (idempotent).
3. Loads ~99k orders, ~112k items, ~100k payments, ~100k reviews, etc.
4. Prints row counts per table.

**Partial / dev import** (faster): pass `order_ids` programatically via
`backend.database.import_data.import_dataset(order_ids=[...])`.

### 7. Ingest the policy knowledge base (RAG)

```bash
python -m backend.rag.ingest
```

This:
1. Reads every `*.md` file in `knowledge_base/`.
2. Chunks each doc (`chunk_size=700`, `overlap=80`).
3. Embeds chunks locally with `all-MiniLM-L6-v2`.
4. Persists a ChromaDB collection `demo_policies` under `data/chroma/`.

### 8. Run the smoke tests

```bash
pytest
```

Tests use a small subset of real order IDs to validate the database schema, tool
semantics, exception-detection logic, and ticket creation (see
`tests/conftest.py` and `tests/test_database_and_tools.py`).

---

## Running the Application

### Start the FastAPI server

```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

- **Health check:** http://localhost:8000/health → `{"status":"ok"}`
- **Swagger UI:**   http://localhost:8000/docs
- **ReDoc:**        http://localhost:8000/redoc

### REST API Endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/chat` | Run the agent; returns reply + safe trace (tools/sources/actions). Pass `{ message, session_id? }`. |
| `GET`  | `/api/orders/{order_id}` | Full order details (customer, items, payments, reviews). |
| `GET`  | `/api/orders/{order_id}/status` | Current status + key dates. |
| `GET`  | `/api/orders/{order_id}/items` | Products / sellers / freight on the order. |
| `GET`  | `/api/orders/{order_id}/exceptions` | Run deterministic demo exception rules. |
| `POST` | `/api/support-tickets` | Create a simulated local ticket: `{ order_id, issue, description }`. |
| `GET`  | `/api/dashboard` | Aggregated portfolio metrics (totals, by-status, exception count). |

**Examples** (HTTPie / curl):

```bash
# Ask the agent about an order
curl -X POST http://localhost:8000/api/chat \
  -H 'Content-Type: application/json' \
  -d '{ "message": "What is the status of order e481f51cbdc54678b7cc49136f2d6af7 and was it delivered on time?", "session_id": "demo-1" }'

# Check exceptions on a known-late order
curl http://localhost:8000/api/orders/203096f03d82e0dffbc41ebc2e2bcfb7/exceptions

# Dashboard
curl http://localhost:8000/api/dashboard
```

---

## Jupyter Notebook Demo

`Agentic_Order_Management.ipynb` is the **canonical end-to-end walkthrough**. It:

1. Loads `.env` and configures logging.
2. (Optional.) Re-imports the Olist dataset into SQLite.
3. Ingests the knowledge-base markdown docs into ChromaDB.
4. **Smoke-tests every tool directly** (no LLM) against real order IDs.
5. Runs the Gemini-powered **LangGraph agent** on representative scenarios:
   - Order status + delivery timeline
   - Delivery exception detection (late orders)
   - Policy-based RAG (returns, refunds, cancellation, SLA)
   - Multi-step: combine exception + policy to answer eligibility
   - Create a simulated support ticket
6. Prints **safe execution traces** (tools used, sources, actions taken) without
   exposing internal chain-of-thought.

### Running the notebook

```bash
jupyter lab Agentic_Order_Management.ipynb
# or
jupyter notebook Agentic_Order_Management.ipynb
```

### Troubleshooting the notebook

If you hit `ImportError: cannot import name 'search_business_policies_tool' from 'backend.tools.order_tools'`
*after* pulling source changes, the Jupyter kernel has stale module objects cached. Fix it
with either:

- **Preferred (quick):** Re-run the "Force-reload backend modules" preamble cell at the
  top of the smoke-test section (it evicts every `backend.*` module from `sys.modules`).
- **Full reset:** Kernel → **Restart Kernel and Run All Cells**.

---

## Agent & Tools Deep-Dive

### Architecture (LangGraph)

```
START → agent (Gemini w/ bound tools)
              │
     ┌── tools_condition ──┐
     │                     │
     ▼                     ▼
  ToolNode               END
  (executes any called
   tool, records trace)
     │
     └─────► agent (loop until END)
```

- `StateGraph` state key is `messages: Annotated[list, add_messages]`.
- Checkpointing via `MemorySaver` → multi-turn sessions are keyed by `thread_id`.
- `AGENT_RECURSION_LIMIT` (default `12`) caps tool loops.

### 11 Tools (ORDER_TOOLS registry)

All tools return JSON-serialized strings for LLM-friendly consumption.

| Tool Name | Purpose |
|---|---|
| `get_order_status` | Status + purchase/approval/carrier/delivery/estimated dates |
| `get_order_details` | Full compound view: customer + items + payments + reviews |
| `get_customer_orders` | List orders by `customer_id` or `customer_unique_id` |
| `search_order_by_customer` | Lightweight order IDs + statuses for a customer |
| `get_order_items` | Products, sellers, prices, freight, shipping limits |
| `get_payment_details` | Payment type, installments, total, per-seq breakdown |
| `get_delivery_information` | Full delivery timeline only |
| `check_delivery_exception` | Run deterministic demo exception rules on the order |
| `get_order_reviews` | Review scores + comment title / message |
| `create_support_ticket` | Simulated local ticket (writes to `support_tickets` table) |
| `search_business_policies` | RAG over synthetic policy markdown; returns chunks + sources |

Each tool call is recorded to a thread-local trace bucket (see
`backend/tools/order_tools.py` — `reset_trace / get_trace / _record`). The
`run_agent()` wrapper returns a *safe* trace that surfaces only `tools_used`,
`sources`, and `actions` — **never chain-of-thought**.

### System-prompt guardrails

The prompt in `backend/agent/prompts.py` enforces:

- Always use tools for order facts; **never invent IDs/dates/product names**.
- Exception results = deterministic demo rules, not official policy.
- Policy Q&A *requires* RAG. If retrieval returns empty, say so instead of inventing a rule.
- Combine exception + policy for return/refund/cancel eligibility questions.
- No real money movement — tickets are simulated / local only.
- Do not reveal hidden chain-of-thought.

### Exception Engine (deterministic demo rules)

Implemented in `backend/services/exception_service.py`. Evaluates each order against
an as-of date (`DATASET_AS_OF_DATE=2018-10-17` by default — matches the dataset's
last-modified historical day).

Rules include:
- **DELIVERY_DELAY** – actual delivery > estimated delivery. Severity HIGH if ≥ 7 d.
- **MISSING_DELIVERY_INFO** – status=delivered but timestamp absent.
- **SHIPPED_NOT_DELIVERED** – status=shipped, estimated date has passed, no delivery.
- **IN_TRANSIT** – shipped + carrier scan present but not yet delivered beyond threshold.
- **APPROVAL_SLOW** – purchase → approval took ≥ 3 days.
- **PAYMENT_MISMATCH** – Σ(payments) differs from Σ(items+freight) by > 5%.
- **LONG_STILL_DELIVERING** – purchase-to-as-of exceeds `LONG_DELIVERY_DAYS` (30 d)
  and order is not delivered / cancelled.

A top-level `exception_type / severity` summary is produced from the ranked list.

---

## RAG Knowledge Base

ChromaDB collection: `demo_policies` | Embeddings: `sentence-transformers/all-MiniLM-L6-v2` (local, CPU OK)

8 synthetic policy documents in `knowledge_base/`:

| File | Topics |
|---|---|
| `shipping_policy.md` | Processing window, carrier types, cutoffs, expedited rules |
| `delivery_sla.md` | State-level SLA, rural surcharges, estimated-vs-guaranteed |
| `return_policy.md` | 30-day post-delivery eligibility, non-returnable categories |
| `refund_policy.md` | Refund vs store credit, original-payment-method rules, timelines |
| `cancellation_policy.md` | Cancel windows (pre-approval, pre-shipment, post-shipment exceptions) |
| `payment_policy.md` | Accepted methods, installment rules, boleto deadlines |
| `exception_handling.md` | Delay → auto-compensation grid, chargeback handling |
| `customer_support_policy.md` | Channel SLAs (email 24h, chat 15 min), escalation tiers |

All content is **synthetic demo rules** for the portfolio demo.

---

## Configuration Reference

All settings live in `backend/config.py` (Pydantic Settings), sourced from `.env`.

| Env Var | Default | Meaning |
|---|---|---|
| `GEMINI_API_KEY` | `""` | **(Required.)** Google AI Studio API key. |
| `GEMINI_MODEL` | `gemini-2.5-flash` | Gemini model variant to use. |
| `DATABASE_URL` | `sqlite:///{PROJECT_ROOT}/data/olist.db` | SQLAlchemy DB URL. |
| `CHROMA_PATH` | `{PROJECT_ROOT}/data/chroma` | ChromaDB persist directory. |
| `DATASET_DIR` | `{PROJECT_ROOT}/dataset` | Location of Olist CSVs. |
| `KNOWLEDGE_BASE_DIR` | `{PROJECT_ROOT}/knowledge_base` | Policy markdowns for RAG. |
| `DATASET_AS_OF_DATE` | `2018-10-17` | Historical "today" used by exception rules. |
| `LONG_DELIVERY_DAYS` | `30` | Threshold for the LONG_STILL_DELIVERING exception. |
| `AGENT_RECURSION_LIMIT` | `12` | Max tool-call loop iterations per graph run. |
| `LOG_LEVEL` | `INFO` | One of `DEBUG`, `INFO`, `WARNING`, `ERROR`. |

---

## Testing

```bash
pytest -v
```

Coverage (see `tests/test_database_and_tools.py`):
- `test_database_initialization` – schema tables are created.
- `test_data_loading_row_counts` – sample order rows match fixture count.
- `test_order_status` – lookup returns delivered status for a known order.
- `test_order_lookup_missing` – unknown IDs cleanly return `found=False`.
- `test_order_details_and_items` – compound details join correctly.
- `test_late_delivery_exception` – flags a known late delivery correctly.
- `test_on_time_delivered_no_delay_exception` – on-time orders do *not* flag DELIVERY_DELAY.
- `test_shipped_exception` – shipped-but-not-delivered orders raise SHIPPED_NOT_DELIVERED / IN_TRANSIT.

Add new tests under `tests/`; `pytest.ini` sets `pythonpath=.` and `testpaths=tests`.

---

## Common Recipes

### 1. Run a one-off agent query from the shell

```python
from backend.agent.graph import run_agent

result = run_agent(
    "Order 203096f03d82e0dffbc41ebc2e2bcfb7 — is it eligible for a refund under the demo return policy?",
    session_id="shell-demo"
)
print("REPLY:", result["response"])
print("TOOLS:", [t["tool"] for t in result["tools_used"]])
print("SOURCES:", result["sources"])
```

### 2. Invoke a tool directly (no LLM)

```python
from backend.tools.order_tools import (
    get_order_status_tool,
    check_delivery_exception_tool,
    search_business_policies_tool as policy_tool,
)

print(get_order_status_tool.invoke({"order_id": "e481f51cbdc54678b7cc49136f2d6af7"}))
print(check_delivery_exception_tool.invoke({"order_id": "203096f03d82e0dffbc41ebc2e2bcfb7"}))
print(policy_tool.invoke({"query": "return eligibility window after delivery"}))
```

### 3. Re-initialize everything from scratch

```powershell
# Windows PowerShell
Remove-Item -Recurse -Force data -ErrorAction SilentlyContinue
python -m backend.database.import_data
python -m backend.rag.ingest
```

### 4. Example order IDs to try

| Order ID | Known Trait |
|---|---|
| `e481f51cbdc54678b7cc49136f2d6af7` | Delivered on time, standard flow |
| `203096f03d82e0dffbc41ebc2e2bcfb7` | DELIVERY_DELAY exception (late delivery) |
| `ee64d42b8cf066f35eac1cf57de1aa85` | SHIPPED_NOT_DELIVERED / IN_TRANSIT exception |

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| `RuntimeError: GEMINI_API_KEY is not configured` | Double-check `.env` is at the repo root and contains a valid key. `config.py` auto-loads `.env` via `SettingsConfigDict`. |
| `ModuleNotFoundError: No module named 'langchain_core'` | Activate the venv (`.venv\Scripts\Activate.ps1` / `source .venv/bin/activate`) before running. |
| `ImportError: cannot import name 'search_business_policies_tool'` | 1) ensure the code is up to date; 2) run the reload-preamble cell or restart the Jupyter kernel. |
| `Policy knowledge base is empty. Run RAG ingestion first.` | Run `python -m backend.rag.ingest`. |
| ChromaDB `sqlite3`-related errors on Windows | Ensure the venv uses the Python.org or official Windows distribution (not a stripped Store build). |
| Slow first RAG call | Normal: `all-MiniLM-L6-v2` is downloaded once and cached. |
| Test failures | Ensure SQLite DB was imported (step 6). The tests use a dedicated in-memory/`tmp_path` DB via fixtures in `conftest.py`. |

---

## License / Data Credits

- Olist Brazilian E-Commerce Public Dataset — used here under its public release terms
  (originally published on Kaggle by Olist). This project is a portfolio demo and is not
  affiliated with or endorsed by Olist.
- Policy documents bundled in `knowledge_base/` are synthetic demo rules, not Olist
  policies.
