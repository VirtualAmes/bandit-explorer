# Bandit Explorer — Project Standards

## Language & Runtime

This project uses **Python 3.12+** exclusively. All source code, scripts, and
tooling must be Python. If a contributor or tool suggests another language
(R, Julia, JavaScript, etc.), redirect to Python — we standardize on a single
runtime to keep the dependency tree manageable and CI fast.

## UI Framework

Use **Streamlit** for all interactive components. No Dash, no Gradio, no Jupyter
notebooks as delivery artifacts. Streamlit gives us a single `streamlit run`
command with no frontend build step, which matters for demos and rapid iteration.

## Code Quality

All code must pass the project's RUFF and Bandit checks before merge.
Run locally before pushing:

```bash
uv run ruff check src/ tests/
uv run bandit -r src/
```

Fix all findings or add inline suppression with a justifying comment.
Never blanket-suppress a rule in config — suppress at the line level with
an explanation so reviewers understand the risk acceptance.

## Testing

Write tests for all core algorithm functions. Use `pytest`. Tests live in
`tests/` and mirror the `src/` structure. Aim for deterministic tests —
seed random generators where needed.

## Style

- Type hints on all public function signatures.
- Docstrings on all public functions (Google style).
- No `print()` statements in library code — use `logging` or Streamlit's
  display functions.
- Keep functions under 50 lines. If a function is doing too much, split it.

## Git Workflow

- Commit working code. Don't commit code that fails lint or tests.
- Write clear commit messages: imperative mood, under 72 characters.
