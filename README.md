# AI Software Engineer Agent — Planner Agent Platform

Production-grade autonomous **Planner Agent** engine built with **FastAPI**, **LangGraph**, **Ollama**, **PostgreSQL**, **Redis**, and **Qdrant**.

---

## Architecture Overview

```
[ START ] 
   │
   ▼
[ ingest_and_normalize_node ]
   │
   ▼
[ ambiguity_analyzer_node ] ──(Blocking Gap?)──► [ PAUSE: Human-in-the-Loop ]
   │ (Proceed)
   ▼
[ requirement_decomposer_node ]
   │
   ▼
[ module_and_architecture_node ]
   │
   ▼
[ task_breakdown_and_dag_node ]
   │
   ▼
[ risk_and_estimation_node ]
   │
   ▼
[ plan_synthesizer_node ]
   │
   ▼
[ plan_validator_node ] ──(Kahn's Cycle Check)──► [ Invalid / Cycle? ] ──► [ plan_refinement_node ] ──► (Loop)
   │ (Valid & Acyclic)
   ▼
[ END ]
```

---

## Directory Structure

```
Implementation/
├── app/
│   ├── core/
│   │   ├── config.py           # Application settings & environment configuration
│   │   ├── logging.py          # Structured JSON logger
│   │   └── llm.py              # Ollama structured LLM client & fallback logic
│   ├── schemas/
│   │   └── plan.py             # Pydantic schemas (AtomicTask, ModuleSpec, Plan)
│   ├── agents/
│   │   └── planner/
│   │       ├── state.py        # LangGraph PlannerState definition
│   │       ├── prompts.py      # System prompts for 8 discrete planning stages
│   │       ├── validator.py    # Deterministic Kahn's Algorithm DAG cycle checker
│   │       ├── nodes.py        # Discrete LangGraph node implementations
│   │       ├── edges.py        # Conditional routing and validation edges
│   │       └── graph.py        # StateGraph assembly & compilation
│   ├── api/
│   │   └── v1/
│   │       └── planner.py      # FastAPI REST endpoints
│   └── main.py                 # FastAPI application entrypoint
├── tests/
│   ├── test_validator.py       # Unit tests for Kahn's cycle detector & critical path
│   └── test_planner_agent.py   # Full integration tests for LangGraph planner
├── run.py                      # Standalone CLI runner with formatted terminal output
├── requirements.txt            # Dependency specifications
├── Dockerfile                  # Container definition
├── docker-compose.yml          # Local infrastructure stack (API + Ollama + DBs)
└── README.md                   # Platform documentation
```

---

## Quickstart

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the Test Suite
```bash
pytest -v
```

### 3. Run Standalone CLI Planning
```bash
python run.py "Build an e-commerce application with authentication, products, shopping cart, orders and payment."
```

### 4. Start the FastAPI Server
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Interactive API documentation will be available at: `http://localhost:8000/api/v1/docs`

---

## API Usage

### `POST /api/v1/plans/generate`
**Payload:**
```json
{
  "raw_requirement": "Build an e-commerce application with authentication, products, shopping cart, orders and payment.",
  "target_tech_stack": {
    "backend": "FastAPI",
    "database": "PostgreSQL",
    "cache": "Redis",
    "auth": "JWT",
    "payment": "Stripe"
  },
  "project_type": "greenfield",
  "max_tasks": 50
}
```
