"""LangGraph ReAct agent for tool-augmented support responses."""

import time

from langgraph.prebuilt import create_react_agent

from app.agent.tools import ALL_TOOLS
from app.pipeline import PipelineResult, _get_llm
from app.rag.retriever import RetrievedChunk, format_context, retrieve
from app.shared.constants import MAX_AGENT_STEPS

AGENT_SYSTEM_PROMPT = """\
You are the SmartOps technical support agent.

Rules:
- Be concise and actionable: steps, commands, config snippets over prose.
- If neither the docs nor the tools can answer, say so plainly. Never invent
  SmartOps features, services, or status information.
- Tools (check_server_status, restart_service) are ONLY for checking the CURRENT 
  live state of a service or requesting a restart.

CRITICAL INSTRUCTION: If the user asks about an ERROR CODE (e.g., E-101) or a general 
setup/how-to question, you MUST NOT use any tools. You must read the documentation 
excerpts below and answer directly from the text.

Documentation excerpts:
{context}
"""


def _build_system_prompt(chunks: list[RetrievedChunk]) -> str:
    return AGENT_SYSTEM_PROMPT.format(context=format_context(chunks))


def _collect_sources(chunks: list[RetrievedChunk], tools_used: list[str]) -> list[str]:
    sources = list(dict.fromkeys(f"{c.source} § {c.section}" for c in chunks))
    if tools_used:
        sources += [f"tool: {name}" for name in tools_used]
    return sources


def run_agent(query: str, model: str, top_k: int) -> PipelineResult:
    """Run a ReAct agent and return the generated answer."""
    started = time.perf_counter()

    chunks = retrieve(query, top_k=top_k)
    system_prompt = _build_system_prompt(chunks)

    agent = create_react_agent(_get_llm(model), tools=ALL_TOOLS, prompt=system_prompt)

    final_state = agent.invoke(
        {"messages": [("human", query)]},
        {"recursion_limit": 2 * MAX_AGENT_STEPS},
    )

    messages = final_state["messages"]
    answer = messages[-1].content
    tools_used = list(dict.fromkeys(message.name for message in messages if message.type == "tool"))
    sources = _collect_sources(chunks, tools_used)

    return PipelineResult(
        answer=answer,
        llm_used=model,
        top_k=top_k,
        latency_seconds=round(time.perf_counter() - started, 3),
        sources=sources,
        is_cached=False
    )