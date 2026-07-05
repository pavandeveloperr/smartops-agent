"""Contextual epsilon-greedy bandit for routing decisions."""

import json
import random
import threading
from dataclasses import dataclass
from pathlib import Path

STATES = ("setup", "error", "how_to")

_STATE_KEYWORDS = {
    "error": ("error", "e-1", "e-2", "e-3", "e-4", "e-5", "fail", "failed", "broken",
              "down", "unreachable", "crash", "not reporting", "not working", "grey",
              "gray", "timeout", "denied", "rejected", "429", "503"),
    "setup": ("install", "setup", "set up", "register", "configure", "configuration",
              "upgrade", "requirements", "getting started", "onboard", "msi", "agent.yaml"),
}


def classify_query(query: str) -> str:
    """Map a query to a routing category."""
    q = query.lower()
    for state, keywords in _STATE_KEYWORDS.items():
        if any(kw in q for kw in keywords):
            return state
    return "how_to"


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
    for m in ("llama3.2:3b", "qwen2.5:3b")
    for k in (2, 5)
)


class EpsilonGreedyBandit:
    """A simple contextual bandit with a persisted Q-table."""

    def __init__(self, epsilon: float = 0.2, state_file: Path | None = None):
        self.epsilon = epsilon
        self.state_file = state_file
        self._lock = threading.Lock()
        self.q_table: dict[str, dict[str, dict]] = {
            s: {a.key: {"q": 0.0, "n": 0} for a in ARMS} for s in STATES
        }
        if state_file and state_file.exists():
            self.q_table = json.loads(state_file.read_text())

    def select(self, state: str) -> tuple[Arm, str]:
        """Choose an arm for the given query state."""
        with self._lock:
            row = self.q_table[state]
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


REPO_ROOT = Path(__file__).resolve().parents[2]
bandit = EpsilonGreedyBandit(epsilon=0.2, state_file=REPO_ROOT / "bandit_state.json")
