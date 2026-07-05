"""Small shared helpers for the backend."""

import hashlib


def stable_choice(name: str, options: tuple[str, ...]) -> str:
    """Pick a deterministic value from options for a given name."""
    digest = int(hashlib.sha256(name.encode()).hexdigest(), 16)
    return options[digest % len(options)]


def dedupe_preserve_order(items: list[str]) -> list[str]:
    """Remove duplicates while preserving the original order."""
    return list(dict.fromkeys(items))
