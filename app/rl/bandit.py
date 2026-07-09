"""Contextual epsilon-greedy bandit for routing decisions."""

import json
import random
import threading
from dataclasses import dataclass
from pathlib import Path

from app.config import (
    BANDIT_STATE_FILE,
    EPSILON,
    AVAILABLE_MODELS,
    TOP_K_OPTIONS,
    STATE_KEYWORDS,
    DEFAULT_STATE
)

STATES = tuple(STATE_KEYWORDS.keys()) + (DEFAULT_STATE,)


def classify_query(query: str) -> str:
    """Map a query to a routing category."""
    q = query.lower()
    for state, keywords in STATE_KEYWORDS.items():
        if any(kw in q for kw in keywords):
            return state
    return DEFAULT_STATE


@dataclass(frozen=True)
class Arm:
    """A routing configuration the bandit can choose."""
    model: str
    top_k: int

    @property
    def key(self) -> str:
        return f"{self.model}|k={self.top_k}"


ARMS = tuple(
    Arm(model=m, top_k=k)
    for m in AVAILABLE_MODELS
    for k in TOP_K_OPTIONS
)


class EpsilonGreedyBandit:
    """
    A simple contextual bandit with a persisted Q-table.
    NOTE: Uses threading.Lock for local MVP. 
    For multi-worker production, migrate state to Redis or SQLite.
    """

    def __init__(self, epsilon: float = EPSILON, state_file: Path | None = BANDIT_STATE_FILE):
        self.epsilon = epsilon
        self.state_file = state_file
        self._lock = threading.Lock()
        
        self.q_table: dict[str, dict[str, dict]] = {
            s: {a.key: {"q": 0.0, "n": 0} for a in ARMS} for s in STATES
        }
        
        if self.state_file and self.state_file.exists():
            try:
                loaded_state = json.loads(self.state_file.read_text())
                # Only update keys that exist to prevent outdated arms from crashing the app
                for state, arms in loaded_state.items():
                    if state in self.q_table:
                        self.q_table[state].update(arms)
            except json.JSONDecodeError:
                # If file is corrupted, fall back to empty  state instead of crashing
                pass

    def select(self, state: str) -> tuple[Arm, str]:
        """Choose an arm for the given query state."""
        with self._lock:
            # Fallback to DEFAULT_STATE if an unknown state is passed
            row = self.q_table.get(state, self.q_table[DEFAULT_STATE])
            untried = [a for a in ARMS if row[a.key]["n"] == 0]
            
            if untried:
                return random.choice(untried), "explore"
            
            if random.random() < self.epsilon:
                return random.choice(ARMS), "explore"
            
            best_key = max(row, key=lambda k: row[k]["q"])
            return next(a for a in ARMS if a.key == best_key), "exploit"

    def update(self, state: str, arm_key: str, reward: float) -> dict:
        """Update the Q-value for a state-arm pair."""
        with self._lock:
            if state not in self.q_table or arm_key not in self.q_table[state]:
                return {} # Prevent KeyError on invalid state/arm combinations
                
            cell = self.q_table[state][arm_key]
            cell["n"] += 1
            cell["q"] += (reward - cell["q"]) / cell["n"]
            cell["q"] = round(cell["q"], 4)
            
            if self.state_file:
                self.state_file.write_text(json.dumps(self.q_table, indent=2))
            return dict(cell)

    def snapshot(self) -> dict:
        """Return a copy of the current Q-table."""
        with self._lock:
            return json.loads(json.dumps(self.q_table))


bandit = EpsilonGreedyBandit()