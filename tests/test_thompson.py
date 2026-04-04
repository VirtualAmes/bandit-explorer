"""Tests for Thompson Sampling engine."""

import random

from thompson import BanditArm, create_sampler


def test_bandit_arm_initial_state():
    arm = BanditArm(true_probability=0.7, name="Test")
    assert arm.alpha == 1.0
    assert arm.beta_param == 1.0
    assert arm.pulls == 0
    assert arm.wins == 0
    assert arm.estimated_probability == 0.5


def test_bandit_arm_pull_updates_state():
    random.seed(42)
    arm = BanditArm(true_probability=1.0, name="Always wins")
    result = arm.pull()
    assert result is True
    assert arm.pulls == 1
    assert arm.wins == 1
    assert arm.alpha == 2.0
    assert arm.beta_param == 1.0


def test_bandit_arm_loss_updates_beta():
    random.seed(42)
    arm = BanditArm(true_probability=0.0, name="Always loses")
    result = arm.pull()
    assert result is False
    assert arm.pulls == 1
    assert arm.wins == 0
    assert arm.alpha == 1.0
    assert arm.beta_param == 2.0


def test_bandit_arm_sample_returns_float():
    random.seed(42)
    arm = BanditArm(true_probability=0.5)
    sample = arm.sample()
    assert isinstance(sample, float)
    assert 0.0 <= sample <= 1.0


def test_create_sampler():
    sampler = create_sampler([0.2, 0.5, 0.8])
    assert len(sampler.arms) == 3
    assert sampler.arms[0].true_probability == 0.2
    assert sampler.arms[1].true_probability == 0.5
    assert sampler.arms[2].true_probability == 0.8
    assert sampler.arms[0].name == "Bandit 1"


def test_sampler_step_records_history():
    random.seed(42)
    sampler = create_sampler([0.3, 0.7])
    step = sampler.step()
    assert step.trial == 1
    assert step.chosen_arm in (0, 1)
    assert isinstance(step.reward, bool)
    assert len(sampler.history) == 1


def test_sampler_run_multiple_steps():
    random.seed(42)
    sampler = create_sampler([0.3, 0.7])
    steps = sampler.run(100)
    assert len(steps) == 100
    assert sampler.total_pulls == 100
    assert len(sampler.history) == 100


def test_sampler_converges_to_best_arm():
    """After many trials, the best arm should get the most pulls."""
    random.seed(42)
    sampler = create_sampler([0.1, 0.9])
    sampler.run(1000)
    # Arm 1 (p=0.9) should have significantly more pulls
    assert sampler.arms[1].pulls > sampler.arms[0].pulls


def test_sampler_reset():
    random.seed(42)
    sampler = create_sampler([0.3, 0.7])
    sampler.run(50)
    assert sampler.total_pulls == 50
    sampler.reset()
    assert sampler.total_pulls == 0
    assert len(sampler.history) == 0
    assert sampler.total_regret == 0.0
    for arm in sampler.arms:
        assert arm.alpha == 1.0
        assert arm.beta_param == 1.0
        assert arm.pulls == 0
        assert arm.wins == 0


def test_best_true_probability():
    sampler = create_sampler([0.2, 0.5, 0.8])
    assert sampler.best_true_probability == 0.8


def test_cumulative_regret_non_negative():
    random.seed(42)
    sampler = create_sampler([0.3, 0.5, 0.7])
    sampler.run(200)
    assert sampler.total_regret >= 0.0
    for step in sampler.history:
        assert step.cumulative_regret >= 0.0


def test_arm_snapshot_in_step():
    random.seed(42)
    sampler = create_sampler([0.4, 0.6])
    step = sampler.step()
    assert len(step.arm_states) == 2
    for snapshot in step.arm_states:
        assert snapshot.alpha >= 1.0
        assert snapshot.beta_param >= 1.0
