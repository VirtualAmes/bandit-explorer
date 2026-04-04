# The Magic Trick — Demo Playbook

A beat-by-beat script for the dinner demo. Each beat teaches the exec
something new about agentic AI. Total runtime: ~15 minutes.

---

## Beat 1: The Setup (2 min)

**Context for the exec:**
> "So here's the scenario. Imagine you're running a campaign — ads, emails,
> landing pages — and you've got four variants. You don't know which one
> converts best. You want to figure that out with as few trials as possible,
> not by running them all equally and wasting budget on losers. That's the
> multi-armed bandit problem."

**Open Claude Code:**
```bash
claude
```

**Type (or have the exec type):**
> I want to build an interactive tool that helps me figure out which of
> several options has the best success rate. I should be able to set the
> true probabilities, run a simulation, and watch it learn in real-time.
> The UI should have inputs for each bandit's probability, start/pause/reset
> controls, and charts showing the algorithm learning. Can we build this in R?

**What happens:** Claude reads CLAUDE.md, sees the Python-only rule, and
redirects. It will say something like: "This project is standardized on
Python per our project guidelines. I'd build this using Thompson Sampling
in Python with Streamlit for the UI."

**Your talking point:**
> "See that? It read the project's rules file and followed them. In your
> org, that file could say 'use Java 17' or 'no external API calls' or
> 'all data stays on-prem.' The AI follows the same guardrails your
> engineers follow. You write the rules. It follows them."

**Recovery if Claude doesn't mention the language redirect:**
Type: "Wait — I asked for R. Why Python?"

---

## Beat 2: Plan Mode (3 min)

**If Claude doesn't enter plan mode, type:**
> Before writing any code, walk me through your approach. What algorithm,
> what the UI will look like, what files you'll create.

**What happens:** Claude walks through:
- Thompson Sampling and the Beta distribution update rule
- Why Thompson over epsilon-greedy or UCB
- The UI layout: probability inputs, Start/Pause/Reset, animated charts
- File structure: `src/thompson.py`, `src/app.py`, `tests/`
- Testing strategy with seeded random generators

**Your talking point:**
> "This is the AI thinking out loud before writing a single line. You can
> see the math, the tradeoffs, the architecture. It's a design doc in
> 30 seconds. And you can push back on any part of it before a line of
> code gets written."

**If the plan is too brief:**
> "Walk me through the math. Why Beta distributions specifically? How does
> the explore-exploit tradeoff work?"

---

## Beat 3: The Build (5-8 min)

**Approve the plan.** Claude will create:
- `src/thompson.py` — BanditArm class, ThompsonSampler, simulation logic
- `src/app.py` — Streamlit UI with inputs, controls, animated charts
- `tests/test_thompson.py` — Seeded deterministic tests

**While Claude is building, your talking point:**
> "Watch what it's doing. It's not generating a snippet — it's building
> a project. Algorithm, UI, tests. And when it's done, it'll check its
> own work against the quality standards in that rules file."

**Just let it run.** This is where the exec watches code materialize from
a description. Don't interrupt unless Claude asks a question.

---

## Beat 4: The Mistakes (2-4 min)

**What happens:** When Claude runs `uv run ruff check src/`, findings fire:

- **S311** on `random.betavariate()` — "Standard pseudo-random generators
  are not suitable for security/cryptographic purposes"
- Possibly **T201** if Claude used `print()` anywhere
- Possibly **ANN** on missing type hints
- Possibly **D103** on missing docstrings

Claude reads the errors, understands them, and fixes them.

**Your talking point (this is the money moment):**
> "This is my favorite part. The AI made real mistakes — not because it's
> bad, but because the security scanner has rules that conflict with
> simulation code. Now watch it reason about the finding, decide it's a
> false positive for this use case, and document WHY. That's the same
> judgment call your senior engineers make. The AI isn't just writing
> code — it's participating in your quality process."

**If Claude fixes everything on first pass (unlikely but possible):**
```bash
# Run this manually in another terminal:
uv run bandit -r src/
```
Then paste the output and ask: "Can you explain these findings?"

---

## Beat 5: Run the App (2 min)

**Claude will run or suggest:**
```bash
uv run streamlit run src/app.py
```

The app opens in the browser. **Have the exec interact:**
1. Set 4 bandit probabilities (e.g., 0.2, 0.5, 0.8, 0.3)
2. Click **Start**
3. Watch the beta distributions narrow and converge
4. Hit **Pause** when one arm starts dominating

**Your talking point:**
> "You set the answer. The algorithm discovered it. The AI built the whole
> thing from your English description in about 5 minutes. The code is real,
> the math is real, the visualization is real."

**Hit Pause to explain what's happening:**
> "See how the distributions started wide? That's uncertainty. Now look at
> Bandit 3 — the one you set to 0.8. The distribution has narrowed right
> around 0.8. The algorithm found the truth. And it wasted fewer trials
> on the losers because it was exploring intelligently, not just
> splitting traffic equally."

---

## Beat 6: Push to GitHub (1 min)

**Type in Claude Code:**
> Commit everything and push to main.

Claude commits and pushes.

**Your talking point:**
> "Real git workflow. Version control. This code is now on your GitHub,
> in your repo, under your control."

---

## Beat 7: The Quality Gate (2-3 min)

**Open the browser tab** to the GitHub Actions page.

Three jobs run in parallel:
- **RUFF Lint** — checks style and code quality
- **Bandit Security Scan** — checks for security issues
- **Tests** — runs the test suite

**Your talking point:**
> "Three quality gates fired automatically on push. Linting, security
> scanning, unit tests. This is what your engineering team's CI pipeline
> does every day. The AI-written code just went through the same gauntlet
> as human-written code. Defense in depth."

**If Bandit shows findings in the Actions summary:**
> "Look — the security scanner flagged the random number generator.
> That's the same finding the AI handled locally. The CI pipeline caught
> it independently. Two layers of defense. That's what production-grade
> looks like."

---

## Closing (2 min)

Pick the one that lands best for the exec:

> "Everything you just saw — guardrails, planning, debugging, security
> review — that's happening in engineering terminals right now. The
> question isn't whether to adopt this. It's whether you're going to
> set the guardrails or let it be the Wild West."

> "That CLAUDE.md file? Took 5 minutes to write. That's your org's AI
> policy, enforced at the tool level, not the memo level."

> "Want to try something from your world? Give me a problem and we'll
> build it right now."

---

## Recovery Playbook

| Problem | What to do |
|---------|-----------|
| Claude suggests R/Julia without hitting guardrail | "Check the project's CLAUDE.md rules. Can we use R here?" |
| Claude skips plan mode | "Before writing code, walk me through your approach." |
| RUFF/Bandit produces zero findings | Run `uv run bandit -r src/` manually and paste output |
| Streamlit app errors on launch | Let Claude debug it. Say: "This is the loop." |
| Tests fail | Same — let Claude fix them. This IS the demo. |
| GitHub Actions doesn't trigger | `gh run list` — may need to verify Actions is enabled |
| "What about hallucination?" | "That's why we have CI. The AI can make mistakes — the quality gates catch them. Same as code review catches human mistakes." |
| "What about IP / confidentiality?" | "Claude Code runs locally. The code stays on your machine. When it pushes, it goes to YOUR repo." |
| "What about cost?" | "Claude Code is $200/month per seat. Compare that to one week of an engineer's time." |
| Demo takes too long | Skip Beats 6-7 (GitHub push + CI). Beats 1-5 are the core magic. |
| No WiFi at the restaurant | Beats 1-5 are fully local. Only 6-7 need internet. |
