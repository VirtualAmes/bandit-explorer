"""Bandit Explorer — Thompson Sampling interactive simulator."""

from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import streamlit as st
from scipy import stats  # type: ignore[import-untyped]

# Allow imports from src/
sys.path.insert(0, str(Path(__file__).resolve().parent))

from thompson import ArmSnapshot, ThompsonSampler, create_sampler  # noqa: E402

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Bandit Explorer",
    page_icon="🎰",
    layout="wide",
)

COLORS = ["#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", "#FFEAA7", "#DDA0DD"]


# ===========================================================================
# PLAN PAGE
# ===========================================================================


def render_plan_page() -> None:
    """Render the Plan & Logic explainer page."""
    st.title("The Plan")
    st.markdown("---")

    st.header("What Is This?")
    st.markdown(
        """
This is a **Thompson Sampling** simulator for the
**Multi-Armed Bandit** problem — one of the most important
frameworks in decision science.

**The scenario:** You have several options (ad variants, landing pages,
drug treatments, pricing tiers). Each has an unknown success rate.
You want to find the best one with as few trials as possible,
without wasting budget on losers.
"""
    )

    st.header("How Thompson Sampling Works")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("The Algorithm")
        st.markdown(
            """
1. **Start with ignorance.** Each arm gets a Beta(1,1)
   distribution — a flat line. We know nothing.

2. **Sample.** Draw a random number from each arm's current
   Beta distribution.

3. **Pick the winner.** Pull the arm with the highest sample.

4. **Learn.** If it paid out, increase alpha (successes).
   If not, increase beta (failures). The distribution narrows.

5. **Repeat.** Over time, the best arm's distribution
   concentrates around its true probability. The algorithm
   naturally explores uncertain arms and exploits known winners.
"""
        )

    with col2:
        st.subheader("Why It's Elegant")
        st.markdown(
            """
- **No tuning parameters.** Unlike epsilon-greedy (pick epsilon)
  or UCB (pick confidence bound), Thompson Sampling is
  parameter-free.

- **Naturally balances explore vs exploit.** Uncertain arms
  have wide distributions — more likely to produce high
  samples — more likely to be explored.

- **Provably optimal.** Achieves logarithmic regret — the
  theoretical lower bound.

- **Dead simple to implement.** ~30 lines of Python.
"""
        )

    st.header("What You're Watching in the Simulator")

    st.markdown(
        """
**Beta Distributions** — Each arm's belief distribution.
Starts flat (uncertain), narrows toward the true probability
as evidence accumulates.

**Cumulative Regret** — The total cost of not always picking
the best arm. Flattens as the algorithm locks onto the winner.

**Pull Counts** — How many times each arm was pulled.
The best arm dominates as confidence grows.

**Scoreboard** — Estimated vs actual probability, plus pull
counts. The "reveal" at the end.
"""
    )

    st.header("How This Was Built")
    st.markdown(
        """
This entire application — algorithm, UI, tests, CI pipeline — was
described in English and built by **Claude Code (Opus 4.6)** in a
single session. The project's `CLAUDE.md` file defined the guardrails:
Python only, Streamlit for UI, RUFF + Bandit quality gates.

The AI followed those rules, planned the approach in plan mode,
built the code, caught and fixed its own lint/security findings,
pushed to GitHub, and passed CI — all from a natural language
description.

**[View the source on GitHub](https://github.com/brianames/bandit-explorer)**
"""
    )

    st.header("The Multi-Armed Bandit in Business")
    st.markdown(
        """
This isn't an academic exercise. Thompson Sampling is used in
production at:

- **Google** — ad placement optimization
- **Netflix** — thumbnail selection (which image gets more clicks?)
- **Microsoft** — Bing search ranking experiments
- **Clinical trials** — adaptive allocation to more promising treatments

Any time you're choosing between options and want to minimize wasted
trials, this is the framework.
"""
    )


# ===========================================================================
# CHART RENDERING
# ===========================================================================


def render_beta_distributions(
    arm_states: list[ArmSnapshot],
    true_probs: list[float],
    colors: list[str],
) -> plt.Figure:
    """Render overlapping Beta distribution curves for each arm."""
    fig, ax = plt.subplots(figsize=(10, 4))
    x = np.linspace(0, 1, 200)

    for i, (state, true_p) in enumerate(
        zip(arm_states, true_probs, strict=True),
    ):
        color = colors[i % len(colors)]
        y = stats.beta.pdf(x, state.alpha, state.beta_param)
        ax.plot(x, y, color=color, linewidth=2, label=f"Bandit {i + 1}")
        ax.axvline(
            true_p, color=color, linestyle="--", alpha=0.5, linewidth=1,
        )

    ax.set_xlabel("Probability of Success")
    ax.set_ylabel("Density")
    ax.set_title("Beta Distributions (dashed lines = true probability)")
    ax.legend(loc="upper right")
    ax.set_xlim(0, 1)
    fig.tight_layout()
    return fig


def render_regret_chart(history: list[dict[str, Any]]) -> plt.Figure:
    """Render cumulative regret over trials."""
    fig, ax = plt.subplots(figsize=(10, 3))
    trials = [h["trial"] for h in history]
    regret = [h["cumulative_regret"] for h in history]

    ax.plot(trials, regret, color="#FF6B6B", linewidth=2)
    ax.fill_between(trials, regret, alpha=0.15, color="#FF6B6B")
    ax.set_xlabel("Trial")
    ax.set_ylabel("Cumulative Regret")
    ax.set_title("Cumulative Regret (flattening = algorithm is learning)")
    fig.tight_layout()
    return fig


def render_pull_counts(
    arm_states: list[ArmSnapshot],
    colors: list[str],
) -> plt.Figure:
    """Render horizontal bar chart of pull counts per arm."""
    fig, ax = plt.subplots(figsize=(10, 2.5))
    names = [f"Bandit {i + 1}" for i in range(len(arm_states))]
    pulls = [s.pulls for s in arm_states]
    bar_colors = [colors[i % len(colors)] for i in range(len(arm_states))]

    ax.barh(names, pulls, color=bar_colors, height=0.5)
    ax.set_xlabel("Pull Count")
    ax.set_title("Arm Selection Frequency")
    for i, v in enumerate(pulls):
        ax.text(v + 0.5, i, str(v), va="center", fontsize=10)
    fig.tight_layout()
    return fig


# ===========================================================================
# STATE RENDERER
# ===========================================================================


def render_current_state(
    sampler: ThompsonSampler,
    probs: list[float],
    history: list[dict[str, Any]],
    beta_ph: Any,  # noqa: ANN401 — Streamlit placeholder type
    score_ph: Any,  # noqa: ANN401 — Streamlit placeholder type
    regret_ph: Any,  # noqa: ANN401 — Streamlit placeholder type
    pulls_ph: Any,  # noqa: ANN401 — Streamlit placeholder type
) -> None:
    """Render the current simulation state into the placeholders."""
    arm_states = [
        ArmSnapshot(
            alpha=arm.alpha,
            beta_param=arm.beta_param,
            pulls=arm.pulls,
            wins=arm.wins,
            estimated_probability=arm.estimated_probability,
        )
        for arm in sampler.arms
    ]

    # Beta distributions
    fig_beta = render_beta_distributions(arm_states, probs, COLORS)
    beta_ph.pyplot(fig_beta)
    plt.close(fig_beta)

    # Scoreboard
    with score_ph.container():
        cols = st.columns(len(sampler.arms))
        for i, (arm, state) in enumerate(
            zip(sampler.arms, arm_states, strict=True),
        ):
            with cols[i]:
                color = COLORS[i % len(COLORS)]
                st.markdown(
                    f"**<span style='color:{color}'>Bandit {i + 1}</span>**",
                    unsafe_allow_html=True,
                )
                st.metric(
                    "Estimated",
                    f"{state.estimated_probability:.3f}",
                    delta=f"{state.estimated_probability - arm.true_probability:+.3f}",
                )
                st.caption(
                    f"True: {arm.true_probability:.2f} | "
                    f"Pulls: {state.pulls} | "
                    f"Wins: {state.wins}"
                )

    # Regret
    if history:
        fig_regret = render_regret_chart(history)
        regret_ph.pyplot(fig_regret)
        plt.close(fig_regret)

    # Pull counts
    if arm_states:
        fig_pulls = render_pull_counts(arm_states, COLORS)
        pulls_ph.pyplot(fig_pulls)
        plt.close(fig_pulls)


# ===========================================================================
# SIMULATOR PAGE
# ===========================================================================


def run_simulator_page() -> None:
    """Main simulator page logic."""
    st.title("Bandit Explorer")
    st.markdown(
        "*Set the hidden probabilities. "
        "Watch Thompson Sampling discover the best arm.*"
    )

    # --- Sidebar controls ---
    st.sidebar.markdown("## Bandit Setup")

    if st.sidebar.button("Randomize"):
        for i in range(4):
            st.session_state[f"prob_{i}"] = round(
                float(np.random.uniform(0.1, 0.9)), 2
            )
        st.rerun()

    probs: list[float] = []
    defaults = [0.2, 0.5, 0.8, 0.3]
    for i in range(4):
        key = f"prob_{i}"
        val = st.sidebar.number_input(
            f"Bandit {i + 1} probability",
            min_value=0.0,
            max_value=1.0,
            value=st.session_state.get(key, defaults[i]),
            step=0.05,
            key=key,
        )
        probs.append(float(val))

    st.sidebar.markdown("## Simulation")
    total_trials = st.sidebar.slider(
        "Total trials",
        min_value=100,
        max_value=10000,
        value=1000,
        step=100,
    )
    batch_size = st.sidebar.slider(
        "Animation speed (trials per frame)",
        min_value=1,
        max_value=100,
        value=10,
        step=1,
    )

    # --- Session state ---
    if "sampler" not in st.session_state:
        st.session_state.sampler = None
        st.session_state.running = False
        st.session_state.history = []
        st.session_state.completed = False

    # --- Action buttons ---
    col1, col2, col3 = st.columns(3)

    with col1:
        start = st.button(
            "Start", type="primary", use_container_width=True,
        )
    with col2:
        is_paused = (
            not st.session_state.running and st.session_state.sampler is not None
        )
        pause_resume = st.button(
            "Resume" if is_paused else "Pause",
            use_container_width=True,
            disabled=st.session_state.sampler is None,
        )
    with col3:
        reset = st.button("Reset", use_container_width=True)

    if reset:
        st.session_state.sampler = None
        st.session_state.running = False
        st.session_state.history = []
        st.session_state.completed = False
        st.rerun()

    if start:
        st.session_state.sampler = create_sampler(probs)
        st.session_state.running = True
        st.session_state.history = []
        st.session_state.completed = False
        st.rerun()

    if pause_resume and st.session_state.sampler:
        st.session_state.running = not st.session_state.running
        st.rerun()

    # --- Visualization placeholders ---
    beta_placeholder = st.empty()
    scoreboard_placeholder = st.empty()
    regret_placeholder = st.empty()
    pulls_placeholder = st.empty()

    sampler: ThompsonSampler | None = st.session_state.sampler

    # Static display when paused
    if sampler and not st.session_state.running:
        render_current_state(
            sampler, probs, st.session_state.history,
            beta_placeholder, scoreboard_placeholder,
            regret_placeholder, pulls_placeholder,
        )
        if st.session_state.completed:
            st.success(
                f"Simulation complete — {sampler.total_pulls} trials. "
                f"Total regret: {sampler.total_regret:.2f}"
            )
        return

    if not sampler or not st.session_state.running:
        st.info(
            "Set the probabilities in the sidebar and click **Start** to begin."
        )
        return

    # --- Animation loop ---
    trials_remaining = total_trials - sampler.total_pulls
    while trials_remaining > 0 and st.session_state.running:
        batch = min(batch_size, trials_remaining)
        steps = sampler.run(batch)

        for step in steps:
            st.session_state.history.append(
                {
                    "trial": step.trial,
                    "cumulative_regret": step.cumulative_regret,
                    "arm_states": step.arm_states,
                }
            )

        render_current_state(
            sampler, probs, st.session_state.history,
            beta_placeholder, scoreboard_placeholder,
            regret_placeholder, pulls_placeholder,
        )

        trials_remaining = total_trials - sampler.total_pulls
        time.sleep(0.05)

    st.session_state.running = False
    st.session_state.completed = True
    st.rerun()


# ===========================================================================
# Router
# ===========================================================================

page = st.sidebar.radio("Navigate", ["Simulator", "The Plan"], index=0)

if page == "The Plan":
    render_plan_page()
else:
    run_simulator_page()
