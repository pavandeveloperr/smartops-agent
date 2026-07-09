"""Pydantic request and response models for the API."""

from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    """Body for POST /query."""
    query: str = Field(..., min_length=1, description="The user's support question.")
    model: str | None = Field(None, description="Force a specific Ollama model, e.g. 'qwen2.5:3b'.")
    top_k: int | None = Field(None, ge=1, le=10, description="Force a retrieval depth.")


class QueryResponse(BaseModel):
    """Response returned by POST /query."""
    answer: str
    llm_used: str
    latency_seconds: float
    transaction_id: str
    sources: list[str] = Field(
        default_factory=list,
        description="Knowledge-base sections the answer was grounded in.",
    )
    is_cached: bool = Field(
        default=False, 
        description="True if the response was served instantly from the semantic cache."
    )


class FeedbackRequest(BaseModel):
    """Body for POST /feedback."""
    transaction_id: str
    score: int = Field(..., ge=0, le=1, description="1 = helpful, 0 = unhelpful.")


class FeedbackResponse(BaseModel):
    transaction_id: str
    reward: float = Field(..., description="score*10 − latency_seconds, as fed to the bandit.")