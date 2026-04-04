# Bandit Explorer

An interactive **Thompson Sampling** simulator that discovers which option
has the highest payout — built entirely by AI from a natural language
description.

## The Problem

You have four slot machines (bandits). Each has an unknown probability of
paying out. You want to find the best one with as few trials as possible,
without wasting budget on losers.

**Thompson Sampling** solves this by maintaining a belief distribution
(Beta distribution) for each arm, sampling from each, and pulling the one
with the highest sample. Over time, it naturally balances exploration
(trying uncertain options) and exploitation (pulling known winners).

## Quick Start

```bash
# Install dependencies
uv sync --extra dev

# Run the app
uv run streamlit run src/app.py

# Run quality checks
uv run ruff check src/ tests/
uv run bandit -r src/
uv run pytest tests/
```

## What You'll See

**Set the truth** — enter hidden probabilities for each bandit (0.0 to 1.0).

**Watch it learn** — the Beta distributions start flat (total uncertainty)
and narrow toward the true probabilities as evidence accumulates.

**See the regret flatten** — cumulative regret measures the cost of not
always picking the best arm. It flattens as the algorithm locks on.

## How It Works

```
For each trial:
    1. Sample from each arm's Beta(alpha, beta) distribution
    2. Pull the arm with the highest sample
    3. If success: alpha += 1  (distribution shifts right)
       If failure: beta += 1   (distribution shifts left)
    4. Repeat — uncertainty collapses, best arm emerges
```

No tuning parameters. No configuration. Provably optimal.

## Project Structure

```
src/thompson.py     # Thompson Sampling engine
src/app.py          # Streamlit UI (simulator + explainer)
tests/              # Deterministic seeded tests
.github/workflows/  # CI: RUFF lint + Bandit security + pytest
CLAUDE.md           # Project standards (guardrails for AI tooling)
```

## Quality Gates

Every push triggers three parallel CI checks:

| Gate | What it checks |
|------|---------------|
| **RUFF Lint** | Code style, imports, type hints, docstrings |
| **Bandit Security** | Security anti-patterns in Python code |
| **pytest** | Algorithm correctness with seeded random generators |

## Built With

This entire application — algorithm, UI, tests, CI pipeline — was described
in English and built by [Claude Code](https://claude.ai/code) (Opus 4.6)
in a single session.

The `CLAUDE.md` file defined the rules: Python only, Streamlit for UI,
RUFF + Bandit quality gates. The AI followed those guardrails, planned
the approach, wrote the code, fixed its own lint findings, and shipped.
