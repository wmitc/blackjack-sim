"""Tests for the round engine: dealer rules, payouts, and EV sanity."""

import numpy as np

from blackjack_sim.cards import Shoe
from blackjack_sim.engine import _play_dealer, play_round
from blackjack_sim.rules import Rules

S17 = Rules(dealer_hits_soft_17=False)
H17 = Rules(dealer_hits_soft_17=True)


class FakeShoe:
    """Deterministic shoe that deals from a fixed queue (engine only calls deal)."""

    def __init__(self, cards):
        self._cards = list(cards)
        self.i = 0

    def deal(self):
        card = self._cards[self.i]
        self.i += 1
        return card


def test_dealer_stands_soft_17_under_s17():
    dealer = [11, 6]  # soft 17
    _play_dealer(dealer, FakeShoe([]), S17)
    assert dealer == [11, 6]


def test_dealer_hits_soft_17_under_h17():
    dealer = [11, 6]  # soft 17 -> must draw under H17
    _play_dealer(dealer, FakeShoe([5, 10]), H17)
    assert len(dealer) > 2


def test_dealer_hits_hard_16_and_stands_on_17():
    dealer = [10, 6]  # hard 16 -> draw
    _play_dealer(dealer, FakeShoe([5]), S17)  # -> 21
    assert dealer == [10, 6, 5]

    standing = [10, 7]  # hard 17 -> no draw
    _play_dealer(standing, FakeShoe([]), S17)
    assert standing == [10, 7]


def test_player_natural_pays_three_to_two():
    # player A,10 ; dealer up 9 (no peek), hole 5
    shoe = FakeShoe([11, 10, 9, 5])
    assert play_round(shoe, S17, bet=1.0) == 1.5


def test_dealer_blackjack_beats_non_natural():
    # player 10,7 ; dealer up A, hole 10 -> dealer natural
    shoe = FakeShoe([10, 7, 11, 10])
    assert play_round(shoe, S17, bet=1.0) == -1.0


def test_both_naturals_push():
    shoe = FakeShoe([11, 10, 11, 10])
    assert play_round(shoe, S17, bet=1.0) == 0.0


def test_player_bust_loses():
    # player 10,6 vs dealer up 10 (peek, hole 5 -> no dealer bj); hit -> 10 busts
    shoe = FakeShoe([10, 6, 10, 5, 10])
    assert play_round(shoe, S17, bet=1.0) == -1.0


def test_player_beats_dealer():
    # player 10,10 (20, stand) vs dealer 10,7 (17)
    shoe = FakeShoe([10, 10, 10, 7])
    assert play_round(shoe, S17, bet=1.0) == 1.0


def test_double_wins_double_stake():
    # player 5,6 (11) doubles to 21 vs dealer 5,6 -> draws 9 -> 20
    shoe = FakeShoe([5, 6, 5, 6, 10, 9])
    assert play_round(shoe, S17, bet=1.0) == 2.0


def test_split_returns_per_hand_results():
    # player 8,8 vs dealer up 6 (no peek), hole 10.
    # hand A: 8 + 5 = 13 (stand vs 6); hand B: 8 + 5 = 13 (stand vs 6).
    # dealer 6,10 = 16 -> draws 10 -> 26 bust. Both hands win -> +2.
    shoe = FakeShoe([8, 8, 6, 10, 5, 5, 10])
    assert play_round(shoe, S17, bet=1.0) == 2.0


def test_flat_bet_basic_strategy_ev_is_small_house_edge():
    """Simulated EV for 6-deck S17 basic strategy should sit near -0.5%."""
    rng = np.random.default_rng(2024)
    shoe = Shoe(num_decks=6, penetration=0.75, rng=rng)
    n = 300_000
    total = 0.0
    for _ in range(n):
        if shoe.needs_reshuffle():
            shoe.reshuffle()
        total += play_round(shoe, S17, bet=1.0)
    ev = total / n
    # Loose bound: clearly a small negative edge, not a coding error.
    assert -0.012 < ev < 0.002, f"EV out of expected range: {ev:.4%}"
