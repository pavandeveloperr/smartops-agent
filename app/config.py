"""Centralized configuration for SmartOps."""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

BANDIT_STATE_FILE = BASE_DIR / "bandit_state.json"
EPSILON = 0.2
AVAILABLE_MODELS = ("llama3.2:3b", "qwen2.5:3b")
TOP_K_OPTIONS = (1, 3)

STATE_KEYWORDS = {
    "error": ("error", "e-1", "e-2", "e-3", "e-4", "e-5", "fail", "failed", "broken",
              "down", "unreachable", "crash", "not reporting", "not working", "grey",
              "gray", "timeout", "denied", "rejected", "429", "503"),
    "setup": ("install", "setup", "set up", "register", "configure", "configuration",
              "upgrade", "requirements", "getting started", "onboard", "msi", "agent.yaml"),
}
DEFAULT_STATE = "how_to"

CHROMA_DIR = BASE_DIR / ".chroma"
COLLECTION_NAME = "smartops_kb"
RAG_SEPARATOR = "\n\n---\n\n"

KNOWLEDGE_BASE_DIR = BASE_DIR / "knowledge_base"

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 150

OLLAMA_BASE_URL = "http://localhost:11434"

CACHE_COLLECTION_NAME = "smartops_cache"
CACHE_SIMILARITY_THRESHOLD = 0.15  
CACHE_TTL_HOURS = 24               