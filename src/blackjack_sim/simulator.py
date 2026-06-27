"""Monte Carlo driver: play many rounds and record per-round outcomes.

Records, for every round, the net result (already scaled by the wager), the
bet placed, and the true count at the moment the bet was made. Those three
arrays are everything the EV/variance analysis in :mod:`blackjack_sim.stats`
needs, including expected value conditioned on the true count.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .cards import Shoe
from .counting import BetRamp, HiLoCounter
from .engine import play_round
from .rules import Rules

# Safety margin: reshuffle if fewer than this many cards remain, so a round
# near the cut card can never exhaust the shoe (matters for small decks).
_MIN_CARDS = 15


@dataclass
class SimResult:
    """Per-round outcomes of a simulation run."""

    net: np.ndarray          # net result per round, in bet units
    bet: np.ndarray          # amount wagered per round
    true_count: np.ndarray   # true count when the bet was placed
    strategy: str
    rules: Rules


def simulate(
    n_rounds: int,
    rules: Rules | None = None,
    strategy: str = "basic",
    ramp: BetRamp | None = None,
    seed: int | None = None,
) -> SimResult:
    """Simulate ``n_rounds`` rounds under ``strategy`` ("basic" or "counting")."""
    if strategy not in ("basic", "counting"):
        raise ValueError("strategy must be 'basic' or 'counting'")
    rules = rules or Rules()
    counting = strategy == "counting"
    if counting and ramp is None:
        ramp = BetRamp()

    rng = np.random.default_rng(seed)
    shoe = Shoe(rules.num_decks, rules.penetration, rng)
    counter = HiLoCounter(shoe)

    net = np.empty(n_rounds)
    bet = np.empty(n_rounds)
    tcs = np.empty(n_rounds)

    for i in range(n_rounds):
        if shoe.needs_reshuffle() or shoe.cards_remaining < _MIN_CARDS:
            shoe.reshuffle()
            counter.reset()
        tc = counter.true_count
        wager = ramp.bet(tc) if counting else 1.0
        result = play_round(shoe, rules, wager)
        counter.sync()
        net[i] = result
        bet[i] = wager
        tcs[i] = tc

    return SimResult(net=net, bet=bet, true_count=tcs, strategy=strategy, rules=rules)
