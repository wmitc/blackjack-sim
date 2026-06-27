"""Tests for the Monte Carlo driver and statistics."""

import numpy as np

from blackjack_sim.counting import BetRamp
from blackjack_sim.rules import Rules
from blackjack_sim.simulator import simulate
from blackjack_sim.stats import bankroll_curve, ev_by_true_count, summarize


def test_basic_run_shapes_and_flat_bets():
    res = simulate(5000, strategy="basic", seed=1)
    assert res.net.shape == res.bet.shape == res.true_count.shape == (5000,)
    assert np.all(res.bet == 1.0)


def test_counting_run_varies_bets():
    ramp = BetRamp.from_spread(1, 12, top_tc=6)
    res = simulate(5000, strategy="counting", ramp=ramp, seed=1)
    assert res.bet.min() >= 1.0
    assert res.bet.max() > 1.0  # ramps up at positive counts
    assert res.bet.max() <= 12.0


def test_reproducible_with_seed():
    a = simulate(3000, strategy="basic", seed=7)
    b = simulate(3000, strategy="basic", seed=7)
    assert np.array_equal(a.net, b.net)


def test_summary_basic_is_small_negative_edge():
    res = simulate(200_000, strategy="basic", seed=3)
    s = summarize(res)
    assert s["rounds"] == 200_000
    assert s["avg_bet"] == 1.0
    assert -0.015 < s["ev_per_round"] < 0.005
    assert s["ci95_low"] < s["ev_per_round"] < s["ci95_high"]


def test_ev_rises_with_true_count():
    ramp = BetRamp.from_spread(1, 12, top_tc=6)
    res = simulate(300_000, strategy="counting", ramp=ramp, seed=5)
    table = ev_by_true_count(res)
    # EV per unit wagered should trend upward with the true count.
    low = table.loc[table["true_count"] <= 0, "ev_per_unit"].mean()
    high = table.loc[table["true_count"] >= 3, "ev_per_unit"].mean()
    assert high > low


def test_bankroll_curve_matches_cumsum():
    res = simulate(1000, strategy="basic", seed=2)
    curve = bankroll_curve(res)
    assert curve.shape == (1000,)
    assert np.isclose(curve[-1], res.net.sum())


def test_h17_is_worse_than_s17_for_player():
    s17 = summarize(simulate(300_000, Rules(dealer_hits_soft_17=False),
                             strategy="basic", seed=11))
    h17 = summarize(simulate(300_000, Rules(dealer_hits_soft_17=True),
                             strategy="basic", seed=11))
    assert h17["ev_per_round"] < s17["ev_per_round"]
