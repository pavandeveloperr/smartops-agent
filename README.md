# SmartOps Self-Optimizing Support Agent

A technical support agent that answers queries via **RAG** over a local knowledge base,
uses a **ReAct agent loop** (LangGraph) to decide when to call operational tools, and
**learns its own routing strategy** — which LLM and which retrieval depth — online,
via an ε-greedy contextual bandit driven by user feedback and measured latency.

```
POST /query ──► classify (setup|error|how_to) ──► bandit picks arm (LLM × top_k)
                                                        │
                     ┌──────────────────────────────────┘
                     ▼
            ReAct agent (LangGraph)
              ├─ context: top-k chunks from ChromaDB (knowledge_base/*.md)
              ├─ LLM: llama3.2:3b or qwen2.5:3b (local, via Ollama)
              └─ tools: check_server_status() / restart_service() (mocks)
                     │
                     ▼
        {answer, llm_used, latency_seconds, transaction_id, sources}

POST /feedback {transaction_id, score} ──► reward = score·10 − latency
                                       ──► Q(s,a) += (reward − Q(s,a)) / N(s,a)
```

## Setup

Prerequisites: Python 3.12+ and [Ollama](https://ollama.com/download).

```powershell
# 1. Models (one-time, ~4 GB total)
ollama pull llama3.2:3b
ollama pull qwen2.5:3b

# 2. Python environment
python -m venv venv
venv\Scripts\pip install -r requirements.txt          # Linux/macOS: venv/bin/pip

# 3. Build the vector store from knowledge_base/*.md (one-time; rerun if docs change)
venv\Scripts\python -m app.rag.ingest

# 4. Run the API
venv\Scripts\uvicorn app.main:app --reload
# → Swagger UI at http://127.0.0.1:8000/docs
```

## Testing the endpoints

Interactive: open http://127.0.0.1:8000/docs and use *Try it out*. By curl:

```bash
# Ask a question — the bandit chooses the LLM + retrieval depth:
curl -s -X POST http://127.0.0.1:8000/query -H "Content-Type: application/json" \
  -d '{"query": "How do I fix error E-101?"}'

# A question that needs LIVE state — the agent calls the mock tool:
curl -s -X POST http://127.0.0.1:8000/query -H "Content-Type: application/json" \
  -d '{"query": "Is the ingest-api service down right now?"}'

# Close the loop with the transaction_id from a /query response:
curl -s -X POST http://127.0.0.1:8000/feedback -H "Content-Type: application/json" \
  -d '{"transaction_id": "<uuid-from-query>", "score": 1}'

# Watch the learner (debug endpoint — the live Q-table):
curl -s http://127.0.0.1:8000/bandit
```

Optional per-request overrides for manual A/B comparison (these bypass — and do not
train — the bandit): `{"query": "...", "model": "qwen2.5:3b", "top_k": 5}`.

**Demo — watch it learn:** with the server running,

```powershell
venv\Scripts\python scripts\demo.py --rounds 12
```

runs query→feedback rounds with a simulated user (scores 1 when the answer is
substantial and cites the right doc) and prints the Q-table converging.

## The RL strategy (breakdown)

**Framing.** Each query is an independent round — routing one query doesn't change
the next user's question — so this is a *contextual bandit* (one-step RL), not a
sequential MDP. No deep nets, per the assignment: the entire learned model is a
12-cell Q-table (3 states × 4 arms) in [app/rl/bandit.py](app/rl/bandit.py),
persisted to `bandit_state.json`.

| Ingredient | Choice |
|---|---|
| **State** (context) | Query category `setup \| error \| how_to` from a keyword classifier — fast, explainable, no LLM call |
| **Actions** (arms) | `{llama3.2:3b, qwen2.5:3b} × {top_k=2, top_k=5}` = 4 arms |
| **Reward** | `score·10 − latency_seconds` — correctness dominates, latency tiebreaks |
| **Policy** | ε-greedy, ε=0.2: explore a random arm 20% of the time, else exploit `argmax Q(s,·)`; every arm is tried once before any estimate is trusted (cold start) |
| **Update** | Incremental mean: `N←N+1; Q ← Q + (reward − Q)/N` — O(1) memory online learning |

Details that matter:

- **One feedback per transaction** — `/feedback` pops the transaction; replays get 404
  (double-counting would bias the running mean).
- **Manual overrides don't train the bandit** — rewards for caller-pinned arms aren't
  the policy's outcomes (off-policy contamination).
- **Learning persists** across restarts via `bandit_state.json`; delete it to reset.

## Project layout

```
app/
├── main.py          # FastAPI endpoints: /query /feedback /bandit /health
├── schemas.py       # Pydantic request/response contracts
├── pipeline.py      # LLM client cache + shared config (models, prompts)
├── rag/ingest.py    # kb *.md → header+size chunking → embeddings → ChromaDB
├── rag/retriever.py # retrieve(query, top_k) similarity search
├── agent/graph.py   # LangGraph ReAct loop (docs-vs-tools decision)
├── agent/tools.py   # mock ops tools (deterministic, seeded by service name)
└── rl/bandit.py     # ε-greedy contextual bandit + query classifier
knowledge_base/      # 4 mock SmartOps docs (the RAG corpus)
scripts/demo.py      # simulated-feedback loop that shows convergence
docs/                # architecture + one study doc per build slice
```

## Design decisions & limitations

- **RAG runs before the agent loop, not as a tool** — context is cheap and almost
  always relevant; the agent's real decision is "docs vs live state". Fewer required
  tool hops also means fewer reasoning failures on 3B models.
- **Grounded prompting** with an explicit "say you don't know" rule to curb small-model
  hallucination; answers return `sources` (KB sections + tools used) for verifiability.
- **In-memory transaction store** — honest about single-process demo scope (production:
  Redis with TTL). ChromaDB and the Q-table do persist to disk.
- **Known limitation:** 3B models occasionally call a tool for a pure-docs question;
  the latency penalty in the reward naturally pressures the bandit away from
  configurations that do this often.
