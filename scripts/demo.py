"""
Demo: watch the bandit learn.

Runs N rounds against a running server (start it first!):
    round = POST /query (no overrides → the BANDIT picks the arm)
          → simulated user feedback → POST /feedback → bandit updates.

The simulated user is a simple heuristic, not a canned reward: it scores 1 when the
answer is non-trivial AND cites the knowledge-base file that actually covers the
question. So the reward reflects real retrieval + generation behavior, and latency
is the real measured latency. Expect the Q-table to separate the arms after a few
rounds per category — run `curl http://127.0.0.1:8000/bandit` any time to peek.

Usage:
    venv\\Scripts\\python scripts\\demo.py --rounds 12
(Stdlib only — no extra dependencies.)
"""

import argparse
import json
import random
import sys
import urllib.request

BASE = "http://127.0.0.1:8000"

# (query, KB file a helpful answer should be grounded in)
DEMO_QUERIES = [
    # error
    ("How do I fix error E-101 authentication failed?", "02-troubleshooting"),
    ("The agent can't reach the ingest endpoint, error E-201", "02-troubleshooting"),
    ("My host shows a grey not-reporting badge in the console", "02-troubleshooting"),
    ("The smartops agent is using very high CPU", "02-troubleshooting"),
    # setup
    ("How do I install the SmartOps agent on Ubuntu?", "01-installation"),
    ("What are the system requirements for the agent?", "01-installation"),
    ("How do I register a new agent with the console?", "01-installation"),
    # how_to
    ("How do I create a CPU alert with Slack notifications?", "03-alerts"),
    ("How can I mute alerts during planned maintenance?", "03-alerts"),
    ("How do I submit custom metrics from my Python app?", "03-alerts"),
    ("What are the API rate limits?", "04-api"),
    ("How do I authenticate against the REST API?", "04-api"),
]


def post(path: str, body: dict) -> dict:
    req = urllib.request.Request(
        BASE + path,
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=600) as resp:
        return json.loads(resp.read())


def get(path: str) -> dict:
    with urllib.request.urlopen(BASE + path, timeout=30) as resp:
        return json.loads(resp.read())


def simulated_user_score(answer: str, sources: list[str], expected_file: str) -> int:
    """1 = 'helpful': a real answer, grounded where it should be."""
    grounded = any(expected_file in s for s in sources)
    substantial = len(answer.strip()) > 80 and "don't know" not in answer.lower()
    return 1 if (grounded and substantial) else 0


def print_q_table(q_table: dict) -> None:
    for state, row in q_table.items():
        cells = "  ".join(
            f"{key:<18} q={cell['q']:>7.2f} n={cell['n']:>2}" for key, cell in row.items()
        )
        print(f"  {state:<7} {cells}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rounds", type=int, default=12, help="query/feedback rounds to run")
    args = parser.parse_args()

    try:
        get("/health")
    except OSError:
        sys.exit("Server not reachable — start it first: venv\\Scripts\\uvicorn app.main:app")

    print(f"Running {args.rounds} rounds (each = /query with bandit routing + /feedback)\n")

    for i in range(1, args.rounds + 1):
        query, expected_file = random.choice(DEMO_QUERIES)
        result = post("/query", {"query": query})

        score = simulated_user_score(result["answer"], result["sources"], expected_file)
        fb = post("/feedback", {"transaction_id": result["transaction_id"], "score": score})

        print(f"[{i:>2}] {result['llm_used']:<13} {result['latency_seconds']:>6.1f}s  "
              f"score={score}  reward={fb['reward']:>7.2f}  {query[:55]!r}")

    print("\nFinal Q-table (highest q per row = the learned best arm for that category):")
    print_q_table(get("/bandit"))


if __name__ == "__main__":
    main()
