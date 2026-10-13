# Agentic Order Management

An end-to-end order intelligence and customer-support assistant built using the Brazilian E-Commerce Public Dataset by Olist. The project combines a Gemini-powered conversational agent, deterministic exception detection, and Retrieval-Augmented Generation (RAG) to answer operational questions about orders, deliveries, payments, and support policies.

The application uses **LangGraph, LangChain, FastAPI, SQLAlchemy, SQLite, ChromaDB, Sentence Transformers, and pytest** to demonstrate how an LLM can interact with structured business data, retrieve relevant policy documents, and support order-related workflows.

> **Disclaimer:** The knowledge base and exception rules are synthetic demo policies created for this portfolio project. They are not official Olist policies or recommendations for real business operations. Policy-related answers and exception results should be interpreted as demo outputs.

---

## Table of Contents

- [Project Overview](#project-overview)
- [Key Features](#key-features)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Dataset and Database](#dataset-and-database)
- [Technology Stack](#technology-stack)
- [How the Agent Works](#how-the-agent-works)
- [Tool Registry](#tool-registry)
- [Exception Detection Engine](#exception-detection-engine)
- [RAG Knowledge Base](#rag-knowledge-base)
- [API Endpoints](#api-endpoints)
- [Installation and Setup](#installation-and-setup)
- [Running the Application](#running-the-application)
- [Testing](#testing)
- [Dashboard and Analytics](#dashboard-and-analytics)
- [Configuration Reference](#configuration-reference)
- [Troubleshooting](#troubleshooting)
- [Limitations and Future Improvements](#limitations-and-future-improvements)

---

## Project Overview

Traditional order-management systems often require users to navigate multiple screens or manually query databases to investigate an order.

This project provides a conversational interface that allows users to ask questions in natural language, such as:

- What is the current status of this order?
- Was the order delivered on time?
- Are there any delivery or payment exceptions?
- What does the demo return policy say?
- Should a support ticket be created for this issue?

The system combines three capabilities:

1. **Structured data access:** Retrieves order, customer, payment, item, and review information from SQLite.
2. **Deterministic exception detection:** Uses Python rules to identify delivery and payment anomalies.
3. **Policy-aware question answering:** Uses RAG to retrieve relevant policy information before generating an answer.

A LangGraph agent coordinates these capabilities and exposes them through a FastAPI backend.

## Key Features

### 1. Structured order intelligence

- Order status and delivery timeline lookup
- Customer order history
- Order item, seller, and freight details
- Payment breakdowns
- Review summaries
- Aggregated operational metrics

### 2. Deterministic exception detection

The exception engine evaluates order records against predefined rules, identifies potential issues, and returns evidence such as delivery dates and delay duration.

### 3. Retrieval-Augmented Generation (RAG)

Synthetic Markdown policy documents are converted into embeddings and stored in ChromaDB. The agent retrieves relevant document chunks to ground policy-related answers.

### 4. Tool-using AI agent

The Gemini model can select from a registry of structured tools. Python executes the selected tools, and the results are returned to the model for response generation.

### 5. REST API

FastAPI exposes endpoints for chatting with the agent, retrieving order information, evaluating exceptions, creating simulated support tickets, and accessing dashboard metrics.

### 6. Automated testing

A pytest suite validates database initialization, data loading, order queries, exception rules, and support-ticket behavior, including negative test cases.

---

## Architecture

The application follows a layered architecture with a clear separation between the LLM, business logic, data access, and retrieval.

```text
                         User
                          |
                          v
                  FastAPI REST API
                          |
                          v
                  LangGraph Agent
                          |
                  Gemini + Tool Calling
                          |
                  +-------+--------+
                  |                |
                  v                v
             Order Tools       Policy Tool
                  |                |
                  v                v
             Service Layer     RAG Retriever
                  |                |
                  v                v
          SQLite + SQLAlchemy  ChromaDB
                  |
                  v
            Olist Order Data

       Deterministic Exception Engine
       validates order data using rules

       Pytest validates database,
       service, tool, and rule behavior
```

### Architectural layers

| Layer | Responsibility |
|---|---|
| Data layer | Stores Olist data in SQLite using SQLAlchemy |
| Service layer | Implements order queries, exception rules, tickets, and dashboard metrics |
| Agent layer | Uses Gemini and LangGraph to coordinate tool calls |
| Retrieval layer | Retrieves relevant policy chunks using embeddings and ChromaDB |
| API layer | Exposes application functionality through FastAPI |
| Testing layer | Validates database, service, and tool behavior using pytest |

This separation allows deterministic business logic to be tested independently of the LLM.

---

## Project Structure

```text
Agentic_order_Managment/
├── README.md
├── requirements.txt
├── pytest.ini
├── Agentic_Order_Management.ipynb
├── _build_notebook.py
│
├── backend/
│   ├── main.py
│   ├── config.py
│   ├── logging_setup.py
│   │
│   ├── agent/
│   │   ├── graph.py
│   │   ├── llm.py
│   │   └── prompts.py
│   │
│   ├── api/
│   │   └── routes.py
│   │
│   ├── database/
│   │   ├── base.py
│   │   ├── models.py
│   │   ├── session.py
│   │   └── import_data.py
│   │
│   ├── rag/
│   │   ├── ingest.py
│   │   └── retriever.py
│   │
│   ├── schemas/
│   │   └── api.py
│   │
│   ├── services/
│   │   ├── order_service.py
│   │   ├── exception_service.py
│   │   ├── ticket_service.py
│   │   └── dashboard_service.py
│   │
│   └── tools/
│       └── order_tools.py
│
├── dataset/
│   └── *.csv
│
├── knowledge_base/
│   ├── shipping_policy.md
│   ├── return_policy.md
│   ├── refund_policy.md
│   ├── cancellation_policy.md
│   ├── payment_policy.md
│   ├── customer_support_policy.md
│   ├── delivery_sla.md
│   └── exception_handling.md
│
├── data/
│   ├── olist.db
│   └── chroma/
│
├── tests/
│   ├── conftest.py
│   └── test_database_and_tools.py
│
└── docs/
    └── dataset_analysis.md
```

*The tree above describes the expected layout. Generated database files and local vector-store contents may be ignored by Git and created during setup.*

---

## Dataset and Database

The project uses the **Brazilian E-Commerce Public Dataset by Olist**, containing historical e-commerce order information.

The CSV files are imported into a local SQLite database using SQLAlchemy.

### Core tables

- `customers`
- `orders`
- `order_items`
- `products`
- `sellers`
- `order_payments`
- `order_reviews`
- `product_category_translations`
- `support_tickets`

The `support_tickets` table supports locally simulated ticket creation.

### Important order fields

The `orders` table contains fields such as:

- `order_id`
- `customer_id`
- `order_status`
- `order_purchase_timestamp`
- `order_approved_at`
- `order_delivered_carrier_date`
- `order_delivered_customer_date`
- `order_estimated_delivery_date`

These fields support order tracking, delivery-delay calculations, and exception detection.

### Important data distinction

The dataset distinguishes between `customer_id`, which identifies a customer record associated with an order, and `customer_unique_id`, which identifies the customer across orders.

The agent prompt accounts for this distinction when retrieving customer order history.

---

## Technology Stack

| Component | Technology |
|---|---|
| Language | Python 3.11+ |
| LLM | Google Gemini |
| Agent orchestration | LangGraph |
| Tool integration | LangChain Core |
| API | FastAPI and Uvicorn |
| Database | SQLite |
| ORM | SQLAlchemy 2.x |
| Vector database | ChromaDB |
| Embeddings | Sentence Transformers (`all-MiniLM-L6-v2`) |
| Data processing | pandas |
| Validation and settings | Pydantic and pydantic-settings |
| Testing | pytest |

---

## How the Agent Works

The agent uses a LangGraph `StateGraph` to coordinate the conversation and tool execution.

### Agent execution flow

1. The user sends a natural-language question to the API.
2. The Gemini model receives the conversation and the available tool definitions.
3. The model decides whether to call a tool or provide a final response.
4. LangGraph routes tool calls to the appropriate tool executor.
5. Python executes the selected tool, which calls the relevant service or retriever.
6. The tool result is added to the conversation.
7. The model can call additional tools if required.
8. The process ends when the model produces a final response or reaches the configured recursion limit.

### Function calling

Function calling allows the model to request a structured operation, such as retrieving an order's status.

The model selects the tool and supplies its arguments. The application executes the function and returns the result.

**The LLM chooses; Python executes.** The model does not directly query the database.

### LangGraph memory

The graph uses `MemorySaver` with a session identifier (`thread_id`) to retain conversation state across requests within the running application.

For example:

- User: "What is the status of order X?"
- User: "Was it delivered late?"

The agent can use the previous conversation to understand which order the follow-up refers to.

This memory is in-process and is not persistent across application restarts.

### Error handling and execution traces

The agent wrapper handles execution errors and returns a controlled response rather than exposing internal errors directly to the user.

It also records a safe execution trace, including tool usage, policy sources, and simulated actions. Hidden internal reasoning is not included in the trace.

---

## Tool Registry

The project registers 11 tools in `backend/tools/order_tools.py`.

| Tool | Purpose |
|---|---|
| `get_order_status` | Retrieves order status and key dates |
| `get_order_details` | Retrieves detailed order information |
| `get_customer_orders` | Retrieves orders associated with a customer |
| `search_order_by_customer` | Searches for orders using customer information |
| `get_order_items` | Retrieves item, seller, and freight details |
| `get_payment_details` | Retrieves payment records and breakdowns |
| `get_delivery_information` | Retrieves delivery timeline information |
| `check_delivery_exception` | Evaluates an order against demo exception rules |
| `get_order_reviews` | Retrieves review information |
| `create_support_ticket` | Creates a local simulated support ticket |
| `search_business_policies` | Retrieves relevant policy chunks through RAG |

Tool arguments are validated using Pydantic schemas. Tool results are returned to the agent, and execution metadata is recorded for the response trace.

---

## Exception Detection Engine

The exception engine is implemented in:

`backend/services/exception_service.py`

It uses deterministic Python rules rather than asking the LLM to decide whether an order violates a rule.

### Implemented rules

| Rule | Purpose |
|---|---|
| `DELIVERY_DELAY` | Detects delivery after the estimated delivery date |
| `MISSING_DELIVERY_INFO` | Detects a delivered status without an actual delivery timestamp |
| `SHIPPED_NOT_DELIVERED` | Detects shipped orders past their estimated delivery date that have not been delivered |
| `IN_TRANSIT` | Identifies shipped orders that have not yet passed their estimated delivery date |
| `APPROVED_NOT_SHIPPED` | Identifies approved, invoiced, or processing orders without carrier handoff |
| `LONG_DELIVERY_DURATION` | Detects delivery durations exceeding the configured threshold |
| `PAYMENT_MISSING` | Detects orders without payment records |
| `PAYMENT_UNDEFINED` | Detects payment records with an undefined payment type |
| `PAYMENT_ZERO_VALUE` | Detects payment records with a zero payment value |

The engine can return detected exceptions, severity, and supporting evidence. When multiple exceptions are present, it prioritizes the more severe finding.

### Historical dataset date

The project uses a configurable `DATASET_AS_OF_DATE`, defaulting to `2018-10-17`.

Because the Olist dataset is historical, using the current date for undelivered orders could incorrectly classify old records as currently overdue. A fixed reference date makes the demo behavior more reproducible.

### Why use deterministic rules?

Delivery dates and payment records are structured facts. Calculations and comparisons are easier to test, explain, and reproduce in Python than through unconstrained LLM reasoning.

The LLM's role is to interpret the user's question, request the relevant tool, and explain the returned result.

---

## RAG Knowledge Base

The synthetic Markdown policies are stored under `knowledge_base/`.

They cover:

- Shipping
- Delivery service-level expectations
- Returns
- Refunds
- Cancellations
- Payment handling
- Customer support
- Exception handling

### RAG pipeline

**1. Ingestion**

The ingestion script reads the policy documents, splits them into chunks, generates embeddings using `all-MiniLM-L6-v2`, and stores them in ChromaDB.

**2. Retrieval**

The user's policy question is embedded and compared against the stored chunks. The retriever returns the top four matching chunks.

**3. Generation**

The relevant retrieved text is passed back through the policy-search tool to the agent, which uses it to construct a contextual answer.

The agent can decide when to use the policy-search tool, making this an agentic RAG workflow.

> **Limitation:** The policies are synthetic demo documents, not verified company policies. Retrieval uses a top-four strategy, so relevance thresholds and better chunking are potential improvements.

---

## API Endpoints

The FastAPI application exposes the following endpoints.

| Method | Endpoint | Purpose |
|---|---|---|
| `POST` | `/api/chat` | Sends a natural-language question to the agent |
| `GET` | `/api/orders/{order_id}` | Retrieves order details |
| `GET` | `/api/orders/{order_id}/status` | Retrieves order status and key dates |
| `GET` | `/api/orders/{order_id}/items` | Retrieves order items, sellers, and freight information |
| `GET` | `/api/orders/{order_id}/exceptions` | Evaluates demo exceptions |
| `POST` | `/api/support-tickets` | Creates a local simulated support ticket |
| `GET` | `/api/dashboard` | Retrieves dashboard metrics |

The actual HTTP response codes depend on the route implementation and request outcome.

### Example: Chat request

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is the status of order e481f51cbdc54678b7cc49136f2d6af7 and was it delivered on time?",
    "session_id": "demo-1"
  }'
```

### Example: Check exceptions

```bash
curl http://localhost:8000/api/orders/203096f03d82e0dffbc41ebc2e2bcfb7/exceptions
```

### Example: Dashboard metrics

```bash
curl http://localhost:8000/api/dashboard
```

Interactive API documentation is available at `/docs` when the application is running.

---

## Installation and Setup

### Prerequisites

- Python 3.11 or newer
- A Google AI Studio API key with Gemini access
- The required Olist CSV files in `dataset/`

### 1. Clone the repository

```bash
git clone https://github.com/shubhankhiremath/Agentic_order_Managment.git
cd Agentic_order_Managment
```

### 2. Create a virtual environment

**Windows PowerShell**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**macOS / Linux**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file in the project root with the following settings, adjusting values if required by your local setup:

```dotenv
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-2.5-flash
DATABASE_URL=sqlite:///./data/olist.db
CHROMA_PATH=./data/chroma
DATASET_DIR=./dataset
KNOWLEDGE_BASE_DIR=./knowledge_base
DATASET_AS_OF_DATE=2018-10-17
LONG_DELIVERY_DAYS=30
AGENT_RECURSION_LIMIT=12
LOG_LEVEL=INFO
```

Use the variable names and defaults supported by `backend/config.py` in the checked-out version of the project.

**Security**

- Never commit `.env`.
- Never publish API keys in source code or notebooks.
- Keep credentials out of logs.
- Treat generated databases and local vector-store contents as local demo data.

---

## Initializing the Project

### Step 1: Import the dataset

```bash
python -m backend.database.import_data
```

The importer validates required files and columns, initializes the database schema, loads the CSV data, and reports row counts.

**Caution:** The importer rebuilds the schema. Back up any local database contents you need to retain before running it.

### Step 2: Ingest the policy documents

```bash
python -m backend.rag.ingest
```

This builds the vector-store collection from the policy documents. Re-running ingestion rebuilds the collection according to the implementation.

---

## Running the Application

Start the FastAPI server:

```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

Open the following URLs in your browser:

- Health check: `http://localhost:8000/health`
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Notebook walkthrough

The project includes `Agentic_Order_Management.ipynb`, which demonstrates dataset initialization, database tools, exception evaluation, RAG ingestion, agent interactions, and execution traces.

Launch it with:

```bash
jupyter lab Agentic_Order_Management.ipynb
```

Alternatively:

```bash
jupyter notebook Agentic_Order_Management.ipynb
```

---

## Testing

The project includes a pytest suite for database, service, and tool behavior.

Run the tests from the repository root:

```bash
pytest -v
```

The current test suite covers scenarios including:

- Database schema initialization
- Imported-data row-count validation
- Successful order-status lookups
- Unknown order IDs returning `found=False`
- Order details, items, and payment queries
- Detection of a known late-delivery case
- Verification that an on-time order does not trigger the late-delivery rule
- Shipped-order exception detection
- Missing-payment detection
- Approved-but-not-shipped detection
- Support-ticket creation for an existing order
- Clean handling of a ticket request for a missing order

These are focused tests for the implemented database, service, and tool functionality. They should not be interpreted as complete end-to-end coverage of the LLM agent, HTTP API, or RAG relevance.

---

## Dashboard and Analytics

The dashboard service provides high-level operational metrics, including order totals, order-status breakdowns, and delivery-related exception counts.

These metrics provide a quick summary of the historical dataset without requiring users to write SQL queries manually.

**Note:** Dashboard exception counts may use a narrower set of delivery-related conditions than the full exception engine. They should not automatically be interpreted as counts of every payment and delivery exception.

---

## Configuration Reference

| Variable | Purpose |
|---|---|
| `GEMINI_API_KEY` | Authenticates requests to Gemini |
| `GEMINI_MODEL` | Selects the configured Gemini model |
| `DATABASE_URL` | Configures the SQLAlchemy database connection |
| `CHROMA_PATH` | Specifies the local ChromaDB storage location |
| `DATASET_DIR` | Specifies the Olist CSV directory |
| `KNOWLEDGE_BASE_DIR` | Specifies the policy-document directory |
| `DATASET_AS_OF_DATE` | Sets the historical reference date for exception evaluation |
| `LONG_DELIVERY_DAYS` | Sets the long-delivery threshold |
| `AGENT_RECURSION_LIMIT` | Limits graph execution steps to reduce runaway loops |
| `LOG_LEVEL` | Configures application logging verbosity |

Confirm the supported variables and default values in `backend/config.py` before relying on this table for deployment.

---

## Troubleshooting

| Problem | Suggested action |
|---|---|
| Missing Gemini API key | Check that `.env` exists, the key is valid, and the configuration loads correctly |
| Dataset import fails | Verify the required Olist CSV files and expected columns are present |
| Policy search returns no results | Run the ingestion command and check that the vector-store directory is accessible |
| Notebook import error after code changes | Restart the kernel and rerun the notebook from the beginning |
| Stale module imports | Restart the Python process or notebook kernel to clear cached modules |
| Unexpected exception counts | Check the historical reference date and compare dashboard aggregation rules with the exception engine |
| API fails to start | Check installed dependencies, configuration, database initialization, and application logs |

---

## Limitations and Future Improvements

The project is a portfolio demonstration rather than production-ready infrastructure.

Potential improvements include:

1. **Authentication and authorization:** Verify that users can access only orders they are authorized to view.
2. **Persistent conversation memory:** Replace in-memory `MemorySaver` with a persistent checkpointer for sessions that must survive restarts.
3. **Improved RAG retrieval:** Use semantic chunk boundaries, relevance thresholds, and retrieval evaluation to reduce irrelevant context.
4. **Agent and API testing:** Add mocked-LLM tests, route-level tests, and end-to-end workflow tests.
5. **LLM evaluation:** Maintain a test dataset of questions, expected tool calls, and facts that should appear in answers.
6. **Observability:** Add structured logs, metrics, and monitoring for failures, latency, and tool usage.
7. **Concurrency and reliability:** Add appropriate transaction handling, retry policies, and safeguards for simultaneous requests.
8. **Production policy integration:** Replace synthetic demo documents with approved, versioned business policies.
9. **Dashboard consistency:** Align dashboard aggregation rules with the complete exception engine where full exception totals are required.

---

## Summary

Agentic Order Management demonstrates how to combine structured data access, deterministic business rules, retrieval-augmented generation, and an LLM-powered agent in a single application.

The core design principle is:

**Use Python for deterministic business logic, database tools for factual order data, RAG for policy retrieval, and the LLM to coordinate these capabilities and communicate the results.**

The project also demonstrates the importance of validation and testing through Pydantic schemas, isolated service logic, and pytest-based checks.

