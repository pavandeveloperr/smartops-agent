"""Query pipeline for retrieval-augmented generation."""

import time
from dataclasses import dataclass

from langchain_ollama import ChatOllama

from app.config import OLLAMA_BASE_URL
from app.rag.retriever import RetrievedChunk, format_context, retrieve
from app.shared.constants import DEFAULT_MODEL, DEFAULT_TOP_K

SYSTEM_PROMPT = """\
You are the SmartOps support agent. Answer the user's question using ONLY the
documentation excerpts provided below.

Rules:
- Be concise and actionable: steps, commands, and config snippets over prose.
- If the excerpts don't contain the answer, say so plainly and suggest the
  closest relevant topic they cover. Never invent SmartOps features.

Documentation excerpts:
{context}
"""

# Cache to prevent rebuilding the LangChain LLM object on every request
_llm_cache: dict[str, ChatOllama] = {}


def _build_prompt(chunks: list[RetrievedChunk], query: str) -> list[tuple[str, str]]:
    """Format the system instructions and user query for the LLM."""
    return [
        ("system", SYSTEM_PROMPT.format(context=format_context(chunks))),
        ("human", query),
    ]


def _collect_sources(chunks: list[RetrievedChunk]) -> list[str]:
    """Extract and deduplicate unique document sources."""
    return list(dict.fromkeys(f"{c.source} § {c.section}" for c in chunks))


def _get_llm(model: str) -> ChatOllama:
    """
    Factory function to initialize and cache the LLM connection.
    Used by both the simple pipeline and the ReAct graph agent.
    """
    if model not in _llm_cache:
        _llm_cache[model] = ChatOllama(
            model=model,
            base_url=OLLAMA_BASE_URL,
            temperature=0.0
        )
    return _llm_cache[model]


@dataclass
class PipelineResult:
    """The output shape used by the API layer."""
    answer: str
    llm_used: str
    top_k: int
    latency_seconds: float
    sources: list[str]
    is_cached: bool


def answer_query(query: str, model: str = DEFAULT_MODEL, top_k: int = DEFAULT_TOP_K) -> PipelineResult:
    """Run retrieve → generate and time the whole request (Simple RAG Path)."""
    started = time.perf_counter()
    
    chunks = retrieve(query, top_k=top_k)
    llm = _get_llm(model)
    
    response = llm.invoke(_build_prompt(chunks, query))
    
    final_answer = response.content
    sources = _collect_sources(chunks)
    
    return PipelineResult(
        answer=final_answer,
        llm_used=model,
        top_k=top_k,
        latency_seconds=round(time.perf_counter() - started, 3),
        sources=sources,
        is_cached=False 
    )