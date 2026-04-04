"""Thompson Sampling engine for multi-armed bandit exploration."""

from __future__ import annotations

import random
from dataclasses import dataclass, field


@dataclass
class BanditArm:
    """A single bandit arm with Beta distribution tracking.

    Args:
        true_probability: The hidden true payout probability (0.0 to 1.0).
        name: Display name for this arm.
    """

    true_probability: float
    name: str = ""
    alpha: float = 1.0
    beta_param: float = 1.0
    pulls: int = 0
    wins: int = 0

    @property
    def estimated_probability(self) -> float:
        """Current estimated probability based on observed results."""
        if self.pulls == 0:
            return 0.5
        return self.wins / self.pulls

    def sample(self) -> float:
        """Draw a sample from this arm's Beta distribution."""
        return random.betavariate(self.alpha, self.beta_param)

    def pull(self) -> bool:
        """Simulate pulling this arm. Returns True on success."""
        success = random.random() < self.true_probability  # noqa: S311
        self.pulls += 1
        if success:
            self.wins += 1
            self.alpha += 1
        else:
            self.beta_param += 1
        return success


@dataclass
class SimulationStep:
    """Record of a single simulation step."""

    trial: int
    chosen_arm: int
    reward: bool
    regret: float
    cumulative_regret: float
    arm_states: list[ArmSnapshot]


@dataclass
class ArmSnapshot:
    """Snapshot of an arm's state at a point in time."""

    alpha: float
    beta_param: float
    pulls: int
    wins: int
    estimated_probability: float


@dataclass
class ThompsonSampler:
    """Thompson Sampling simulator for multi-armed bandits.

    Args:
        arms: List of BanditArm instances to explore.
    """

    arms: list[BanditArm] = field(default_factory=list)
    history: list[SimulationStep] = field(default_factory=list)
    total_regret: float = 0.0

    @property
    def best_true_probability(self) -> float:
        """The highest true probability among all arms."""
        return max(arm.true_probability for arm in self.arms)

    @property
    def total_pulls(self) -> int:
        """Total number of pulls across all arms."""
        return sum(arm.pulls for arm in self.arms)

    def step(self) -> SimulationStep:
        """Run one step of Thompson Sampling.

        Samples from each arm's Beta distribution, pulls the arm with
        the highest sample, updates the arm's state, and records the step.
        """
        samples = [arm.sample() for arm in self.arms]
        chosen = samples.index(max(samples))

        reward = self.arms[chosen].pull()

        step_regret = self.best_true_probability - self.arms[chosen].true_probability
        self.total_regret += step_regret

        arm_states = [
            ArmSnapshot(
                alpha=arm.alpha,
                beta_param=arm.beta_param,
                pulls=arm.pulls,
                wins=arm.wins,
                estimated_probability=arm.estimated_probability,
            )
            for arm in self.arms
        ]

        record = SimulationStep(
            trial=self.total_pulls,
            chosen_arm=chosen,
            reward=reward,
            regret=step_regret,
            cumulative_regret=self.total_regret,
            arm_states=arm_states,
        )
        self.history.append(record)
        return record

    def run(self, n_trials: int) -> list[SimulationStep]:
        """Run n_trials steps of Thompson Sampling."""
        return [self.step() for _ in range(n_trials)]

    def reset(self) -> None:
        """Reset all arms and history to initial state."""
        for arm in self.arms:
            arm.alpha = 1.0
            arm.beta_param = 1.0
            arm.pulls = 0
            arm.wins = 0
        self.history.clear()
        self.total_regret = 0.0


def create_sampler(probabilities: list[float]) -> ThompsonSampler:
    """Create a ThompsonSampler from a list of true probabilities.

    Args:
        probabilities: List of true payout probabilities for each arm.

    Returns:
        A configured ThompsonSampler ready to run.
    """
    arms = [
        BanditArm(
            true_probability=p,
            name=f"Bandit {i + 1}",
        )
        for i, p in enumerate(probabilities)
    ]
    return ThompsonSampler(arms=arms)
