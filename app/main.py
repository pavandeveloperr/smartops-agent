"""SmartOps Support Agent API."""

import uuid

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.agent.graph import run_agent
from app.pipeline import SUPPORTED_MODELS
from app.rl.bandit import Arm, bandit, classify_query
from app.schemas import FeedbackRequest, FeedbackResponse, QueryRequest, QueryResponse
from app.shared.constants import CORS_ORIGINS

app = FastAPI(
    title="SmartOps Support Agent",
    description="Self-optimizing technical support agent: RAG + ReAct agent + contextual-bandit routing.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(CORS_ORIGINS),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check() -> dict:
    """Health check endpoint."""
    return {"status": "ok", "service": "smartops-agent"}


TRANSACTIONS: dict[str, dict[str, object]] = {}


def _resolve_arm(query: str, requested_model: str | None, requested_top_k: int | None) -> tuple[str, Arm, str]:
    state = classify_query(query)

    if requested_model or requested_top_k:
        if requested_model and requested_model not in SUPPORTED_MODELS:
            raise HTTPException(422, f"Unknown model {requested_model!r}. Supported: {list(SUPPORTED_MODELS)}")
        arm = Arm(model=requested_model or SUPPORTED_MODELS[0], top_k=requested_top_k or 3)
        return state, arm, "manual"

    arm, mode = bandit.select(state)
    return state, arm, mode


def _store_transaction(state: str, arm: Arm, mode: str, latency_seconds: float) -> str:
    txn_id = str(uuid.uuid4())
    TRANSACTIONS[txn_id] = {
        "state": state,
        "arm_key": arm.key,
        "mode": mode,
        "latency_seconds": latency_seconds,
    }
    return txn_id


@app.post("/query", response_model=QueryResponse)
def query(request: QueryRequest) -> QueryResponse:
    """Answer a support question using the selected bandit arm and agent."""
    state, arm, mode = _resolve_arm(request.query, request.model, request.top_k)

    try:
        result = run_agent(request.query, model=arm.model, top_k=arm.top_k)
    except ConnectionError as exc:
        raise HTTPException(503, f"LLM backend unreachable — is Ollama running? ({exc})")

    txn_id = _store_transaction(state, arm, mode, result.latency_seconds)

    return QueryResponse(
        answer=result.answer,
        llm_used=result.llm_used,
        latency_seconds=result.latency_seconds,
        transaction_id=txn_id,
        sources=result.sources,
    )


@app.post("/feedback", response_model=FeedbackResponse)
def feedback(request: FeedbackRequest) -> FeedbackResponse:
    """Record feedback and update the bandit."""
    txn = TRANSACTIONS.pop(request.transaction_id, None)
    if txn is None:
        raise HTTPException(404, "Unknown or already-scored transaction_id.")

    reward = request.score * 10 - float(txn["latency_seconds"])

    if txn["mode"] != "manual":
        bandit.update(str(txn["state"]), str(txn["arm_key"]), reward)

    return FeedbackResponse(transaction_id=request.transaction_id, reward=round(reward, 3))


@app.get("/bandit")
def bandit_snapshot() -> dict:
    """Return the current bandit state."""
    return bandit.snapshot()
