"""Shared constants for the SmartOps backend."""

SUPPORTED_MODELS = ("llama3.2:3b", "qwen2.5:3b")
DEFAULT_MODEL = SUPPORTED_MODELS[0]
DEFAULT_TOP_K = 3
CORS_ORIGINS = ("http://localhost:5173", "http://127.0.0.1:5173")
KNOWN_SERVICES = ("ingest-api", "console-web", "metrics-pipeline", "alert-engine")
MAX_AGENT_STEPS = 2
