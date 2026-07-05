# SmartOps Self-Optimizing Support Agent

SmartOps is a local-first support assistant that combines retrieval-augmented generation, tool-using agent reasoning, and online learning to improve how it answers technical support questions.

The system is designed to:
- answer questions using a local knowledge base
- decide when live operational context is needed
- learn which model and retrieval settings work best over time
- expose a simple API and a lightweight frontend for interaction

## Architecture at a glance

```text
User → Frontend → API /query → Query classifier
                                  ↓
                           Contextual bandit
                                  ↓
                           RAG retrieval
                                  ↓
                           ReAct agent loop
                                  ↓
                           Response + sources
                                  ↓
                           Feedback / reward update
```

## Core capabilities

- Grounded answers from documentation using RAG
- Tool-aware reasoning for operational questions
- Online policy learning from user feedback
- Fast local deployment with Ollama and ChromaDB

## Technology stack

- Backend: FastAPI, Pydantic, LangGraph, ChromaDB, Ollama
- Frontend: React + Vite
- Learning: contextual epsilon-greedy bandit

## Prerequisites

- Python 3.12+
- Node.js 18+
- Ollama installed and running

## Quick start

### 1. Install the required models

```powershell
ollama pull llama3.2:3b
ollama pull qwen2.5:3b
```

### 2. Create and activate a Python environment

```powershell
python -m venv venv
venv\Scripts\Activate.ps1
venv\Scripts\pip install -r requirements.txt
```

### 3. Build the local knowledge base index

```powershell
venv\Scripts\python -m app.rag.ingest
```

### 4. Start the backend

```powershell
venv\Scripts\uvicorn app.main:app --reload
```

The API will be available at:
- http://127.0.0.1:8000/docs

### 5. Start the frontend

In a second terminal:

```powershell
cd ui
npm install
npm run dev
```

The frontend will be available at:
- http://127.0.0.1:5173

For a short local startup guide, see [docs/07-running-locally.md](docs/07-running-locally.md).

## API overview

The backend exposes the following main endpoints:

- GET /health — health check
- POST /query — run retrieval and generation for a user question
- POST /feedback — submit a score for a previous query response
- GET /bandit — inspect the current learning state

Example:

```powershell
curl -X POST http://127.0.0.1:8000/query -H "Content-Type: application/json" -d "{\"query\": \"How do I fix error E-101?\"}"
```

## Demo

To run the built-in demonstration flow:

```powershell
venv\Scripts\python scripts\demo.py --rounds 12
```

This script simulates user feedback and shows the bandit improving its routing choices over time.

## Project structure

```text
app/
├── main.py                # FastAPI entrypoints and request handling
├── schemas.py             # Pydantic request and response models
├── pipeline.py            # Retrieval and generation pipeline
├── rag/                   # Ingestion and retrieval logic
├── agent/                 # ReAct agent loop and mock tools
├── rl/                    # Contextual bandit logic
knowledge_base/            # Knowledge base documents used for RAG
scripts/                   # Demo and utility scripts
ui/                        # React frontend
```

## Learning strategy

The routing layer uses a lightweight contextual bandit.

- State: query category such as setup, error, or how_to
- Actions: model choice and retrieval depth combinations
- Reward: a value based on answer quality and response time

The reward is computed as:

$$reward = score \times 10 - latency$$

The bandit updates its estimate using:

$$Q(s, a) \leftarrow Q(s, a) + \alpha (reward - Q(s, a))$$

This allows the system to learn better routing decisions over time without needing a heavy training pipeline.

## Design notes and limitations

- RAG runs before the agent loop so the model receives grounded context first.
- The agent is encouraged to answer from documentation and only use tools when needed.
- The transaction store is in-memory for demo purposes; production would require a more durable store.
- Smaller 3B models can be faster and lighter, but may sometimes overuse tools or produce weaker answers.
