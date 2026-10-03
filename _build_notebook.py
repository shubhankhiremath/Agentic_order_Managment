"""Generator for Agentic_Order_Management.ipynb with 19 sections. Not part of the app."""
from pathlib import Path

import nbformat as nbf

nb = nbf.v4.new_notebook()
nb.metadata["kernelspec"] = {
    "display_name": "Python 3",
    "language": "python",
    "name": "python3",
}
nb.metadata["language_info"] = {"name": "python", "pygments_lexer": "ipython3"}

md = lambda s: nbf.v4.new_markdown_cell(s)
code = lambda s: nbf.v4.new_code_cell(s)

nb.cells = [
    md(
        """# 1. Project Introduction

**Agentic Order Management** — a self-contained notebook demo of an LLM-powered order-automation assistant built on the **Olist Brazilian E-Commerce public dataset**.

This notebook reuses the existing Python backend:
- SQLite + SQLAlchemy data layer (`backend/database`, `backend/services`)
- Deterministic delivery/payment exception rules (`backend/services/exception_service.py`)
- Simulated local support tickets
- ChromaDB + Sentence-Transformer RAG over synthetic demo policies (`knowledge_base/`, `backend/rag`)
- Google Gemini via LangChain + LangGraph agent with tool calling and memory (`backend/agent`)

> ⚠️ **Demo-only disclaimer**
> The exception rules in `exception_service.py` and every markdown file in `knowledge_base/` are **synthetic business rules created for this portfolio demo**. They are **NOT official Olist policies**, and the system does **not** connect to a live commerce platform.
>
> Original CSV files in `dataset/` are never modified."""
    ),
    md("## 2. Imports and Configuration"),
    code(
        r"""from __future__ import annotations

from pathlib import Path
import importlib.util
import json
import os
import site
import subprocess
import sys

# --- Anti-pollution guards: prevent system Keras 3 / TF / FLAX from being
# --- probed by transformers/sentence_transformers (we only need PyTorch).
_GUARD_ENV = {
    "TRANSFORMERS_NO_TF": "1",
    "TRANSFORMERS_NO_FLAX": "1",
    "USE_TF": "0",
    "DISABLE_TELEMETRY": "YES",
    "HF_HUB_DISABLE_TELEMETRY": "1",
}
for _gk, _gv in _GUARD_ENV.items():
    os.environ[_gk] = _gv
del _gk, _gv, _GUARD_ENV

ROOT = Path.cwd().resolve()
if not (ROOT / "backend" / "config.py").exists():
    for cand in [ROOT, *ROOT.parents]:
        if (cand / "backend" / "config.py").exists():
            ROOT = cand
            break
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

VENV = ROOT / ".venv"
VENV_OK = False
if VENV.exists():
    venv_site = (VENV / "Lib" / "site-packages").as_posix() if os.name == "nt" \
        else (VENV / "lib" / f"python{sys.version_info.major}.{sys.version_info.minor}" / "site-packages").as_posix()
    if Path(venv_site).exists() and venv_site not in sys.path and venv_site not in site.getsitepackages():
        sys.path.insert(0, venv_site)
    VENV_OK = importlib.util.find_spec("chromadb") is not None

PY = sys.executable
print(f"kernel python     : {PY}")
print(f"kernel version    : {sys.version.split()[0]}")
print(f"project .venv OK  : {VENV_OK}")

REQUIRED = [
    "pandas", "sqlalchemy", "pydantic", "pydantic_settings", "dotenv",
    "chromadb", "langchain", "langchain_core", "langchain_google_genai",
    "langgraph", "sentence_transformers",
]
missing = [m for m in REQUIRED if importlib.util.find_spec(m) is None]
if missing:
    print(f"[bootstrap] Missing: {missing}. Installing via {PY} -m pip ...")
    rc = subprocess.call(
        [PY, "-m", "pip", "install", "-r", str(ROOT / "requirements.txt"), "--quiet"],
        stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT,
    )
    still = [m for m in REQUIRED if importlib.util.find_spec(m) is None]
    if still:
        raise RuntimeError(
            f"Kernel {PY} cannot import: {still}.\n"
            f"Fix: switch the Jupyter kernel to '{VENV / 'Scripts' / 'python.exe' if os.name=='nt' else VENV/'bin'/'python'}' "
            f"(in VS Code click the top-right kernel picker → Select Another Kernel → Python Environments → .venv)."
        )

from dotenv import load_dotenv

env_path = ROOT / ".env"
if env_path.exists():
    load_dotenv(env_path)
else:
    print("[note] .env not found at project root — create it with GEMINI_API_KEY=<key> to enable live Gemini queries")

from backend.config import PROJECT_ROOT, get_settings
from backend.database.import_data import import_dataset, validate_dataset
from backend.database.models import Order
from backend.database.session import SessionLocal, configure_engine
from backend.rag.ingest import ingest_knowledge_base, retrieve_policies
from backend.services.exception_service import evaluate_order_exceptions
from backend.services.order_service import (
    get_customer_orders,
    get_delivery_information,
    get_order_details,
    get_order_items,
    get_order_reviews,
    get_order_status,
    get_payment_details,
    search_order_by_customer,
)
from backend.services.ticket_service import create_support_ticket
from backend.agent.graph import get_graph, reset_agent_graph, run_agent
from backend.agent.llm import build_chat_model, get_gemini_model_name
from backend.agent.prompts import SYSTEM_PROMPT  # noqa: F401
from backend.tools.order_tools import ORDER_TOOLS
from backend.rag.retriever import search_business_policies_tool

get_settings.cache_clear()
settings = get_settings()

print("\nproject_root     :", PROJECT_ROOT)
print("dataset_dir      :", settings.dataset_dir, "exists:", Path(settings.dataset_dir).exists())
print("database_url     :", settings.database_url)
print("chroma_path      :", settings.chroma_path)
print("knowledge_base   :", settings.knowledge_base_dir, "exists:", Path(settings.knowledge_base_dir).exists())
print("gemini_model     :", get_gemini_model_name())
has_key = bool(os.getenv("GEMINI_API_KEY") or settings.gemini_api_key)
print("gemini_api_key   :", "configured" if has_key else "MISSING — live agent queries will be skipped")"""
    ),
    md("## 3. Load the Existing Olist Dataset from `dataset/`"),
    code(
        r"""from pathlib import Path
import pandas as pd

DATASET_DIR = Path(settings.dataset_dir)
print("Using dataset dir:", DATASET_DIR.resolve())
validate_dataset(DATASET_DIR)

csv_files = sorted(DATASET_DIR.glob("*.csv"))
print("\nCSV files:", len(csv_files))
for p in csv_files:
    print("  -", p.name)

rows_summary = []
for path in csv_files:
    header = pd.read_csv(path, nrows=0)
    n = sum(1 for _ in open(path, "r", encoding="utf-8", errors="replace")) - 1
    rows_summary.append({
        "file": path.name,
        "rows": max(n, 0),
        "columns": len(header.columns),
    })

pd.DataFrame(rows_summary).style.set_caption("Dataset files")"""
    ),
    md("## 4. Basic Dataset Inspection (real order IDs preview)"),
    code(
        r"""orders_df = pd.read_csv(DATASET_DIR / "olist_orders_dataset.csv", parse_dates=[
    "order_purchase_timestamp","order_approved_at","order_delivered_carrier_date",
    "order_delivered_customer_date","order_estimated_delivery_date",
])
status_dist = orders_df["order_status"].value_counts().to_frame(name="count")
status_dist["pct"] = (status_dist["count"] / len(orders_df) * 100).round(1).astype(str) + " %"
print("Orders:", len(orders_df))
print("Customers:", pd.read_csv(DATASET_DIR / "olist_customers_dataset.csv", nrows=0).shape[0] == 0 or
      len(pd.read_csv(DATASET_DIR / "olist_customers_dataset.csv")))
status_dist"""
    ),
    code(
        r"""orders_df["actual_minus_est_days"] = (
    orders_df["order_delivered_customer_date"] - orders_df["order_estimated_delivery_date"]
).dt.total_seconds() / 86400

delivered = orders_df[orders_df["order_status"] == "delivered"].dropna(subset=["actual_minus_est_days"])
late_mask = delivered["actual_minus_est_days"] > 0
print("Delivered orders:", len(delivered))
print("Late deliveries :", int(late_mask.sum()), f"({late_mask.mean()*100:.1f}%)")
print("Max delay (days):", delivered["actual_minus_est_days"].max())
print("Avg delay if late (days):", delivered.loc[late_mask, "actual_minus_est_days"].mean().round(1))

ON_TIME_ORDER_ID = delivered.loc[~late_mask, "order_id"].iloc[0]
LATE_ORDER_ID    = delivered.loc[late_mask, "order_id"].iloc[0]
SHIPPED_ORDER_ID = orders_df.loc[orders_df["order_status"] == "shipped", "order_id"].iloc[0] \
    if (orders_df["order_status"] == "shipped").any() else LATE_ORDER_ID

CUSTOMER_ID_LATE = orders_df.loc[orders_df["order_id"] == LATE_ORDER_ID, "customer_id"].iloc[0]

print("\nREAL ORDER IDS FOR EXAMPLES:")
print("  ON_TIME  =", ON_TIME_ORDER_ID)
print("  LATE     =", LATE_ORDER_ID)
print("  SHIPPED  =", SHIPPED_ORDER_ID)
print("  CUSTOMER =", CUSTOMER_ID_LATE)"""
    ),
    code(
        r"""print("Sample order rows (status + dates):")
cols = ["order_id","order_status","order_purchase_timestamp",
        "order_estimated_delivery_date","order_delivered_customer_date"]
orders_df[cols].head(3)"""
    ),
    md("## 5. SQLite / Database Access (CSV → SQLAlchemy one-shot import)"),
    code(
        r"""from pathlib import Path
from backend.database.models import Customer, OrderItem, OrderPayment

DB_PATH = PROJECT_ROOT / "data" / "olist.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

if not DB_PATH.exists():
    print("[import] Building SQLite DB from Dataset/ CSVs (one-time)...")
    counts = import_dataset()
    for k, v in sorted(counts.items()):
        print(f"  {k}: {v}")
else:
    print("[import] Reusing existing SQLite at", DB_PATH)

configure_engine(settings.database_url)

quick = SessionLocal()
print("\norders table      :", quick.query(Order).count())
print("customers table   :", quick.query(Customer).count())
print("order_items table :", quick.query(OrderItem).count())
print("payments table    :", quick.query(OrderPayment).count())
quick.close()"""
    ),
    md("## 6. Order-Management Functions / Tools (direct service layer)"),
    code(
        r"""session = SessionLocal()
print("▶ get_order_status(LATE)")
print(json.dumps(get_order_status(session, LATE_ORDER_ID), indent=2, default=str))"""
    ),
    code(
        r"""print("▶ get_order_items(LATE)")
items_res = get_order_items(session, LATE_ORDER_ID)
print(json.dumps(items_res, indent=2, default=str))"""
    ),
    code(
        r"""print("▶ get_payment_details(LATE)")
pay_res = get_payment_details(session, LATE_ORDER_ID)
print(json.dumps(pay_res, indent=2, default=str))

print("\n▶ get_delivery_information(LATE)")
del_res = get_delivery_information(session, LATE_ORDER_ID)
print(json.dumps(del_res, indent=2, default=str))"""
    ),
    code(
        r"""print("▶ get_order_reviews(LATE)")
rev_res = get_order_reviews(session, LATE_ORDER_ID)
print(json.dumps(rev_res, indent=2, default=str))

print("\n▶ get_order_details(LATE) — top-level keys:")
details = get_order_details(session, LATE_ORDER_ID)
print(sorted(details.keys()))
print("  customer city/state:", details["customer"]["city"], "/", details["customer"]["state"])
print("  item_count         :", len(details["items"]))
print("  payment_count      :", len(details["payments"]))"""
    ),
    code(
        r"""print("▶ search_order_by_customer(CUSTOMER_ID_LATE)")
sr = search_order_by_customer(session, CUSTOMER_ID_LATE)
print("order_count:", sr.get("order_count"))
for o in sr.get("orders", [])[:5]:
    print("  -", o["order_id"], o["order_status"])

print("\n▶ get_customer_orders same customer, full status rows:",
      get_customer_orders(session, CUSTOMER_ID_LATE).get("order_count"))
session.close()"""
    ),
    md("## 7. Delivery / Exception Detection"),
    md(
        """Deterministic rules in `backend/services/exception_service.py`:
- `DELIVERY_DELAY` (HIGH/MEDIUM): actual delivery after estimated date
- `SHIPPED_NOT_DELIVERED` (HIGH): shipped + estimate passed dataset as-of date
- `APPROVED_NOT_SHIPPED` (MEDIUM/HIGH): approved/invoiced with no carrier handoff
- `LONG_DELIVERY_DURATION` (MEDIUM): purchase→delivery ≥ `long_delivery_days` (30 default)
- `PAYMENT_MISSING`, `PAYMENT_UNDEFINED`, `PAYMENT_ZERO_VALUE`

These are **demo rules**, not official Olist policy."""
    ),
    code(
        r"""session = SessionLocal()
late_ex    = evaluate_order_exceptions(session, LATE_ORDER_ID)
ontime_ex  = evaluate_order_exceptions(session, ON_TIME_ORDER_ID)
shipped_ex = evaluate_order_exceptions(session, SHIPPED_ORDER_ID)
session.close()

print("=== LATE ORDER ===")
print(json.dumps({k: late_ex[k] for k in ["has_exception","exception_type","severity","message"]}, indent=2))
for e in late_ex["exceptions"]:
    print("  •", e["exception_type"], "| severity:", e["severity"], "|", e["message"])

print("\n=== ON-TIME ORDER ===")
print("has_exception:", ontime_ex["has_exception"],
      "| types:", [e["exception_type"] for e in ontime_ex["exceptions"]])

print("\n=== SHIPPED ORDER ===")
print("has_exception:", shipped_ex["has_exception"])
for e in shipped_ex["exceptions"]:
    print("  •", e["exception_type"], "| severity:", e["severity"], "|", e["message"])"""
    ),
    md("## 8. Support-Ticket Creation (simulated / local SQLite)"),
    code(
        r"""session = SessionLocal()
ticket = create_support_ticket(
    session,
    LATE_ORDER_ID,
    issue="delivery_delay",
    description="Customer reports order arrived after the estimated delivery date and is asking about next steps.",
)
session.close()
print(json.dumps(ticket, indent=2, default=str))
assert ticket.get("simulated") is True, "ticket should be marked simulated/demo"
print("\n✅ Ticket stored locally in support_tickets table.")"""
    ),
    md("## 9. Demo Policy Documents (`knowledge_base/`)"),
    code(
        r"""from pathlib import Path

KB_DIR = Path(settings.knowledge_base_dir)
policy_files = sorted(KB_DIR.glob("*.md"))
print("Synthetic demo policy files (" + str(len(policy_files)) + "):")
for p in policy_files:
    size_kb = p.stat().st_size / 1024
    print(f"  - {p.name}  ({size_kb:.1f} KB)")

print("\n⚠️  All files are synthetic demo policies — NOT official Olist policy.\n")

print("▶ Sample: return_policy.md (first 600 chars)")
print((KB_DIR / "return_policy.md").read_text(encoding="utf-8")[:600])"""
    ),
    code(
        r"""print("▶ Sample: delivery_sla.md (first 600 chars)")
print((KB_DIR / "delivery_sla.md").read_text(encoding="utf-8")[:600])"""
    ),
    md("## 10. RAG with ChromaDB (persistent local vector store)"),
    code(
        r"""from backend.rag.ingest import COLLECTION, _client

client = _client()
try:
    existing_count = client.get_collection(COLLECTION).count()
except Exception:
    existing_count = 0

if existing_count == 0:
    print("[rag] Ingesting knowledge_base/ into ChromaDB for the first time...")
    n_chunks = ingest_knowledge_base()
    print("[rag] Chunks ingested:", n_chunks)
else:
    print("[rag] Reusing existing ChromaDB collection with", existing_count, "chunks")

col = client.get_collection(COLLECTION)
print("[rag] collection :", col.name)
print("[rag] chunks     :", col.count())"""
    ),
    code(
        r"""queries_rag = [
    "What is the return eligibility period after delivery?",
    "When can an order be cancelled?",
    "What happens if a delivery is delayed past the SLA?",
]

for q in queries_rag:
    print("\nQ:", q)
    hits = retrieve_policies(q, k=3)
    sources = sorted({h["source"] for h in hits})
    top = hits[0] if hits else None
    print("  sources:", sources)
    if top:
        print("  top match:", top["source"],
              "| distance:", round(top["distance"], 3),
              "| excerpt:", top["content"][:140].replace("\n", " "), "...")"""
    ),
    md("## 11. Local Sentence-Transformer Embeddings (all-MiniLM-L6-v2)"),
    code(
        r"""from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

ef = SentenceTransformerEmbeddingFunction(model_name="sentence-transformers/all-MiniLM-L6-v2")
sample_texts = [
    "Returns are accepted within 30 days of delivery for unused items.",
    "Delivery delays longer than 7 days may qualify for a partial refund.",
    "Payment methods accepted: credit card, boleto, voucher.",
]
embeddings = ef(sample_texts)
print("Embedding dims :", len(embeddings[0]))
print("Number of vecs :", len(embeddings))
print("First 5 values of first vector:", [round(x, 4) for x in embeddings[0][:5]])

import numpy as np
a, b = np.array(embeddings[0]), np.array(embeddings[1])
cos_sim = float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))
print(f"\nCosine sim (return text ↔ delay text): {cos_sim:.3f}")"""
    ),
    md("## 12. Gemini Configuration"),
    code(
        r"""GEMINI_KEY = os.getenv("GEMINI_API_KEY") or settings.gemini_api_key
print("model_name      :", get_gemini_model_name())
print("api_key_loaded  :", "yes (value never printed)" if GEMINI_KEY else "NO — set GEMINI_API_KEY in .env to enable live LLM")
print("temperature     : 0.2 (hard-coded in build_chat_model for deterministic outputs)")

if GEMINI_KEY:
    llm = build_chat_model()
    print("llm_class       :", type(llm).__module__ + "." + type(llm).__name__)
    try:
        probe = llm.invoke("Reply with exactly: PONG")
        print("connectivity    :", "OK" if "PONG" in (probe.content or "") else "UNEXPECTED RESPONSE")
    except Exception as ex:
        print("connectivity    : FAILED —", type(ex).__name__, str(ex)[:200])
else:
    print("connectivity    : SKIPPED (no key)")
    llm = None"""
    ),
    md("## 13. LangChain Tools"),
    code(
        r"""print("Order / database tools:")
for t in ORDER_TOOLS:
    schema = t.args_schema
    fields = sorted(schema.model_fields.keys()) if schema else []
    print(f"  - {t.name:30s} fields={fields}")

print("\nRAG policy tool:")
t = search_business_policies_tool
fields = sorted(t.args_schema.model_fields.keys())
print(f"  - {t.name:30s} fields={fields}")

ALL_TOOLS = ORDER_TOOLS + [search_business_policies_tool]
print("\nTotal tools:", len(ALL_TOOLS))"""
    ),
    code(
        r"""# Direct tool smoke test (no LLM involved):
from backend.tools.order_tools import (
    get_order_status_tool, get_payment_details_tool, check_delivery_exception_tool,
    search_business_policies_tool as policy_tool,
)
print("▶ get_order_status_tool(LATE_ORDER_ID) → first 200 chars:")
print(get_order_status_tool.invoke({"order_id": LATE_ORDER_ID})[:200])

print("\n▶ check_delivery_exception_tool(LATE_ORDER_ID) → first 300 chars:")
print(check_delivery_exception_tool.invoke({"order_id": LATE_ORDER_ID})[:300])

print("\n▶ search_business_policies_tool('return eligibility') → first 300 chars:")
print(policy_tool.invoke({"query": "return eligibility"})[:300])"""
    ),
    md("## 14. LangGraph Agent (model → tools → model loop with MemorySaver)"),
    code(
        r"""reset_agent_graph()

if GEMINI_KEY:
    agent_graph = get_graph(llm=llm)
    print("agent_graph :", type(agent_graph).__name__)
    print("nodes       :", list(agent_graph.get_graph().nodes.keys()))
    print("edges       :", [(e.source, e.target) for e in agent_graph.get_graph().edges])
    print("checkpointer:", type(agent_graph.checkpointer).__name__ if agent_graph.checkpointer else "none")
else:
    agent_graph = None
    print("[skip] No GEMINI_API_KEY — LangGraph agent will be instantiated later only inside chat().")"""
    ),
    md("## 15. Conversation / Session Context (thread_id memory)"),
    md(
        """`run_agent` wraps LangGraph `MemorySaver(checkpointer)` with a `configurable.thread_id = session_id`.
- Same `session_id` → multi-turn memory (the agent remembers "this order").
- Different `session_id` → blank context.
- No API calls are made outside the loop. We'll demonstrate two sessions in the next cell."""
    ),
    code(
        r"""# MemorySaver state inspection (no LLM call):
from langgraph.checkpoint.memory import MemorySaver
from uuid import uuid4

saver = MemorySaver()
print("checkpointer type :", type(saver).__name__)
tid_a, tid_b = "session-A-" + uuid4().hex[:6], "session-B-" + uuid4().hex[:6]
print("thread-A :", tid_a)
print("thread-B :", tid_b)
print("\nMemorySaver supports independent threads: messages written under thread-A are not visible to thread-B.")"""
    ),
    md("## 16. Safe Agent Execution Trace (tools + sources + actions only)"),
    code(
        r"""from backend.tools.order_tools import (
    reset_trace, get_trace,
    get_order_status_tool, check_delivery_exception_tool,
    search_business_policies_tool, create_support_ticket_tool,
)

reset_trace()
_ = get_order_status_tool.invoke({"order_id": LATE_ORDER_ID})
_ = check_delivery_exception_tool.invoke({"order_id": LATE_ORDER_ID})
_ = search_business_policies_tool.invoke({"query": "late delivery policy"})
ticket_result_json = create_support_ticket_tool.invoke({
    "order_id": LATE_ORDER_ID,
    "issue": "trace_demo",
    "description": "Safe trace demo — ticket created locally.",
})

from backend.agent.graph import _safe_trace
tools_used, sources, actions = _safe_trace(get_trace())

print("▶ Tools used:")
if not tools_used:
    print("  - (none)")
for t in tools_used:
    print(f"  - {t['tool']:30s} | {t['purpose']:45s} | {t['status']}")

print("\n▶ Sources (policy filenames):")
if not sources:
    print("  - (none)")
for s in sources:
    print("  -", s)

print("\n▶ Actions (side effects like ticket creation):")
if not actions:
    print("  - (none)")
for a in actions:
    print(f"  - {a.get('action')} ticket_id={a.get('ticket_id')} status={a.get('status')}")"""
    ),
    md("## 17. End-to-End Example Queries (real order IDs via Gemini)"),
    code(
        r"""DEMO_SESSION = "e2e-notebook-demo-" + LATE_ORDER_ID[-8:]

def show_trace(result: dict) -> None:
    print("\n🤖 Agent response:")
    print(result.get("response", "(no response)"))
    print("\n🛠  Tools used:")
    tools = result.get("tools_used") or []
    if not tools:
        print("  - (none)")
    for t in tools:
        print(f"  - {t.get('tool')}")
    print("\n📚 Sources (policies):")
    sources = result.get("sources") or []
    if not sources:
        print("  - (none)")
    for s in sources:
        print("  -", s)
    actions = result.get("actions") or []
    if actions:
        print("\n✅ Actions performed:")
        for a in actions:
            print(f"  - {a.get('action')} ticket_id={a.get('ticket_id')} status={a.get('status')}")

E2E_QUERIES = [
    f"Check the status of order {LATE_ORDER_ID}.",
    "Show me the details of this order.",
    "Was this order delivered late?",
    "Why was this order delayed?",
    "What payment method was used?",
    "What is the return policy?",
    "Can this order be returned?",
    "Create a support ticket for this order because it is delayed.",
]

turn_results = []
if not GEMINI_KEY:
    print("=" * 72)
    print("SKIPPED live Gemini e2e queries: GEMINI_API_KEY is not configured.")
    print("To run these cells, add GEMINI_API_KEY=<your-key> to .env and re-run from cell 12 onward.")
    print("=" * 72)
    # Dry-run the non-LLM equivalent so readers still see expected data:
    print("\n🔧 Dry-run (no LLM) of the underlying data that the agent would retrieve:")
    s = SessionLocal()
    for i, q in enumerate(E2E_QUERIES):
        print(f"\n[{i+1}] {q}")
        if i == 0: print("  →", json.dumps(get_order_status(s, LATE_ORDER_ID))[:200])
        elif i == 1: print("  → details keys:", sorted(get_order_details(s, LATE_ORDER_ID).keys()))
        elif i in (2, 3): print("  →", evaluate_order_exceptions(s, LATE_ORDER_ID)["message"])
        elif i == 4: print("  → payment types:", [p["payment_type"] for p in get_payment_details(s, LATE_ORDER_ID)["payments"]])
        elif i == 5: print("  → sources:", sorted({h["source"] for h in retrieve_policies("return policy", k=3)}))
        elif i == 6:
            print("  → exception:", evaluate_order_exceptions(s, LATE_ORDER_ID)["exception_type"])
            print("  → rag sources:", sorted({h["source"] for h in retrieve_policies("return eligibility late delivery", k=3)}))
        elif i == 7:
            t = create_support_ticket(s, LATE_ORDER_ID, "delay_e2e_dry", "Dry run ticket")
            print("  → simulated ticket created:", t.get("ticket_id"), t.get("created"))
    s.close()
else:
    for i, q in enumerate(E2E_QUERIES):
        print("\n" + "=" * 72)
        print(f"[{i+1}/{len(E2E_QUERIES)}] USER: {q}")
        print("-" * 72)
        r = run_agent(q, session_id=DEMO_SESSION)
        turn_results.append(r)
        show_trace(r)
    if turn_results:
        print("\n" + "=" * 72)
        print(f"✅ Completed {len(turn_results)} turns in session {turn_results[0]['session_id']}")
        print("✅ All sessions share the same thread_id → context preserved.")"""
    ),
    md("## 18. Simple Interactive `chat()` Function"),
    code(
        r'''SESSION_INTERACTIVE = "interactive-chat-" + LATE_ORDER_ID[-8:]

def chat(message: str, session_id: str = SESSION_INTERACTIVE, show: bool = True) -> dict:
    """One-line interactive helper. Type chat('…') to continue the conversation."""
    key = os.getenv("GEMINI_API_KEY") or settings.gemini_api_key
    if not key:
        raise RuntimeError(
            "GEMINI_API_KEY not set. Add it to .env and re-run the config cell before using chat().\n"
            "Key value is NEVER printed by this notebook."
        )
    result = run_agent(message, session_id=session_id)
    if show:
        show_trace(result)
    return result

print("chat(message, session_id=SESSION_INTERACTIVE) is ready.")
print(f"   Default session: {SESSION_INTERACTIVE}")
print()
print("Try:")
print(f"   chat(f'Why was order {LATE_ORDER_ID} delayed?')")
print("   chat('Can it be returned or refunded?')")
print("   chat('Summarize this case in 3 bullets.')")'''
    ),
    md("## 19. Final Project Summary"),
    md(
        """### What this notebook demonstrated (19 sections)

| # | Section | Artifacts reused |
|---|---|---|
| 1 | Project intro | `knowledge_base/`, disclaimer |
| 2 | Imports & config | `backend/config.py`, `.env` |
| 3 | Dataset load | `dataset/olist_*.csv` |
| 4 | Dataset inspection | real order IDs (on-time / late / shipped) |
| 5 | SQLite access | `backend/database/import_data.py`, `models.py`, `session.py` |
| 6 | Order functions | `backend/services/order_service.py` (10 functions) |
| 7 | Exception detection | `backend/services/exception_service.py` (7 demo rules) |
| 8 | Support tickets | `backend/services/ticket_service.py` → `support_tickets` table |
| 9 | Policy documents | `knowledge_base/*.md` (8 synthetic files) |
| 10 | RAG (ChromaDB) | `backend/rag/ingest.py`, `retrieve_policies()` |
| 11 | Local embeddings | `sentence-transformers/all-MiniLM-L6-v2` via ChromaDB |
| 12 | Gemini setup | `backend/agent/llm.py` (`build_chat_model`) |
| 13 | LangChain tools | `backend/tools/order_tools.py` (10) + `backend/rag/retriever.py` (1) |
| 14 | LangGraph agent | `backend/agent/graph.py` (StateGraph, MemorySaver, ToolNode loop) |
| 15 | Session context | LangGraph `thread_id` → multi-turn memory |
| 16 | Safe trace | `trace_var` + `_safe_trace` (tools / sources / actions only) |
| 17 | E2E queries | 8 real queries on a real late order ID |
| 18 | Interactive `chat()` | Reusable one-liner for further exploration |
| 19 | Summary | This table |

### Key capabilities
- ✅ get_order_status / get_order_details / get_customer_orders / get_order_items
- ✅ get_payment_details / get_delivery_information / get_reviews
- ✅ search_by_customer (customer_id OR customer_unique_id)
- ✅ check_delivery_exception (7 deterministic demo rules, severity ranked)
- ✅ create_support_ticket (simulated, stored locally)
- ✅ RAG over 8 demo policy docs with source citations
- ✅ Combined reasoning (DB facts + RAG policy → grounded answers)
- ✅ Gemini natural-language responses with tool calling
- ✅ LangGraph loop with `tools_condition` branching
- ✅ Conversation memory (thread_id) — "this order" works after first turn
- ✅ Safe execution trace (no hidden CoT; only tools / sources / actions)

### Guardrails & disclaimers (always active)
- Synthetic exception rules always labeled "demo rule"
- Policy tool always labels results as demo policies
- No real refunds / cancellations / commerce-platform writes
- Ticket writes are explicitly marked `simulated: true`
- API key **never** printed or logged"""
    ),
]

out = Path("Agentic_Order_Management.ipynb")
out.write_text(nbf.writes(nb), encoding="utf-8")
print("✅ Wrote", out.resolve())
print("   cells:", len(nb.cells))
md_count = sum(1 for c in nb.cells if c["cell_type"] == "markdown")
co_count = sum(1 for c in nb.cells if c["cell_type"] == "code")
print("   markdown cells:", md_count)
print("   code cells    :", co_count)
