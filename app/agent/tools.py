"""Mock operational tools for the support agent."""

import hashlib

from langchain_core.tools import tool

_KNOWN_SERVICES = ("ingest-api", "console-web", "metrics-pipeline", "alert-engine")


def _stable_choice(name: str, options: tuple) -> str:
    """Choose a deterministic status value for a service name."""
    digest = int(hashlib.sha256(name.encode()).hexdigest(), 16)
    return options[digest % len(options)]


@tool
def check_server_status(service: str) -> str:
    """Report the mock operational status of a SmartOps service."""
    service = service.strip().lower()
    if service not in _KNOWN_SERVICES:
        return (f"Unknown service '{service}'. Known services: {', '.join(_KNOWN_SERVICES)}. "
                "Ask the user which one they mean.")

    status = _stable_choice(service, ("operational", "degraded", "operational", "operational"))
    latency_ms = 20 + int(hashlib.sha256(service.encode()).hexdigest(), 16) % 180
    return (f"Service '{service}': status={status}, p50_latency={latency_ms}ms, "
            f"last_incident={'2026-07-01 (resolved)' if status == 'degraded' else 'none in 30 days'}")


@tool
def restart_service(service: str) -> str:
    """Restart a SmartOps service."""
    service = service.strip().lower()
    if service not in _KNOWN_SERVICES:
        return f"Unknown service '{service}'. Known services: {', '.join(_KNOWN_SERVICES)}."
    return f"Restart of '{service}' initiated. New status: operational (mock)."


ALL_TOOLS = [check_server_status, restart_service]
