"""Mock operational tools for the support agent."""

from langchain_core.tools import tool

from app.shared.constants import KNOWN_SERVICES
from app.shared.helpers import stable_choice


@tool
def check_server_status(service: str) -> str:
    """
    Report the mock operational status of a SmartOps service.
    
    CRITICAL RULE: DO NOT use this tool if the user is asking about an 
    ERROR CODE (like E-101) or a setup/configuration question. Only use this 
    tool if the user explicitly asks if a service is down, slow, or running.
    """
    service = service.strip().lower()
    if service not in KNOWN_SERVICES:
        return (f"Unknown service '{service}'. Known services: {', '.join(KNOWN_SERVICES)}. "
                "Ask the user which one they mean.")

    status = stable_choice(service, ("operational", "degraded", "operational", "operational"))
    latency_ms = 20 + int(__import__("hashlib").sha256(service.encode()).hexdigest(), 16) % 180
    return (f"Service '{service}': status={status}, p50_latency={latency_ms}ms, "
            f"last_incident={'2026-07-01 (resolved)' if status == 'degraded' else 'none in 30 days'}")


@tool
def restart_service(service: str) -> str:
    """
    Restart a SmartOps service.
    
    CRITICAL RULE: ONLY use this tool if the user explicitly asks to restart 
    a service, OR if the service is currently 'degraded' and needs fixing. 
    Never use this to answer general documentation or error code questions.
    """
    service = service.strip().lower()
    if service not in KNOWN_SERVICES:
        return f"Unknown service '{service}'. Known services: {', '.join(KNOWN_SERVICES)}."
    return f"Restart of '{service}' initiated. New status: operational (mock)."


ALL_TOOLS = [check_server_status, restart_service]