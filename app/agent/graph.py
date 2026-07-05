"""LangGraph ReAct agent for tool-augmented support responses."""

import time

from langgraph.prebuilt import create_react_agent

from app.agent.tools import ALL_TOOLS
from app.pipeline import PipelineResult, _get_llm
from app.rag.retriever import format_context, retrieve

AGENT_SYSTEM_PROMPT = """\
You are the SmartOps technical support agent.

You have two sources of truth:
1. The documentation excerpts below — use them for how-to, setup, configuration,
   and error-code questions.
2. Tools (check_server_status, restart_service) — use them ONLY when the user asks
   about the CURRENT state of a service (is it down/slow right now?) or requests a
   restart. Never call a tool for questions the documentation already answers.

Rules:
- Be concise and actionable: steps, commands, config snippets over prose.
- If neither the docs nor the tools can answer, say so plainly. Never invent
  SmartOps features, services, or status information.

Documentation excerpts:
{context}
"""

MAX_AGENT_STEPS = 6


def run_agent(query: str, model: str, top_k: int) -> PipelineResult:
    """Run a ReAct agent and return the generated answer."""
    started = time.perf_counter()

    chunks = retrieve(query, top_k=top_k)
    system_prompt = AGENT_SYSTEM_PROMPT.format(context=format_context(chunks))

    agent = create_react_agent(_get_llm(model), tools=ALL_TOOLS, prompt=system_prompt)

    final_state = agent.invoke(
        {"messages": [("human", query)]},
        {"recursion_limit": 2 * MAX_AGENT_STEPS},
    )

    answer = final_state["messages"][-1].content

    tools_used = list(dict.fromkeys(
        m.name for m in final_state["messages"] if m.type == "tool"
    ))

    sources = list(dict.fromkeys(f"{c.source} § {c.section}" for c in chunks))
    if tools_used:
        sources += [f"tool: {name}" for name in tools_used]

    return PipelineResult(
        answer=answer,
        llm_used=model,
        top_k=top_k,
        latency_seconds=round(time.perf_counter() - started, 3),
        sources=sources,
    )
