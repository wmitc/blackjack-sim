"""Tests for Hi-Lo counting and the bet ramp."""

import numpy as np

from blackjack_sim.cards import Shoe, _SINGLE_DECK
from blackjack_sim.counting import (
    BetRamp,
    HiLoCounter,
    hi_lo_tag,
    running_count,
    true_count,
)


def test_tag_values():
    for v in range(2, 7):
        assert hi_lo_tag(v) == 1
    for v in (7, 8, 9):
        assert hi_lo_tag(v) == 0
    assert hi_lo_tag(10) == -1
    assert hi_lo_tag(11) == -1  # ace


def test_full_deck_is_balanced():
    # A balanced count: a complete deck/shoe sums to zero.
    assert running_count(_SINGLE_DECK) == 0
    assert running_count(np.tile(_SINGLE_DECK, 6)) == 0


def test_running_count_accumulates():
    assert running_count([2, 3, 4]) == 3      # three low cards
    assert running_count([10, 11]) == -2      # ten + ace
    assert running_count([7, 8, 9]) == 0


def test_true_count_normalises_by_decks():
    assert true_count(10, 5.0) == 2.0
    assert true_count(-6, 3.0) == -2.0
    assert true_count(5, 0.0) == 0.0


def test_hilo_counter_tracks_shoe():
    rng = np.random.default_rng(0)
    shoe = Shoe(num_decks=2, rng=rng)
    counter = HiLoCounter(shoe)
    dealt = [shoe.deal() for _ in range(20)]
    counter.sync()
    assert counter.running == running_count(dealt)
    # True count = running / decks remaining
    assert counter.true_count == counter.running / shoe.decks_remaining


def test_counter_reset_on_reshuffle():
    shoe = Shoe(num_decks=1, rng=np.random.default_rng(1))
    counter = HiLoCounter(shoe)
    for _ in range(10):
        shoe.deal()
    counter.sync()
    shoe.reshuffle()
    counter.reset()
    assert counter.running == 0
    assert counter._seen == 0


def test_bet_ramp_flat_below_threshold():
    ramp = BetRamp(min_bet=1, max_bet=12, tc_threshold=1, units_per_tc=2)
    assert ramp.bet(-3) == 1
    assert ramp.bet(1) == 1
    assert ramp.bet(2) == 3      # 1 + (2-1)*2
    assert ramp.bet(100) == 12   # capped


def test_bet_ramp_from_spread_reaches_max():
    ramp = BetRamp.from_spread(min_bet=1, max_bet=12, tc_threshold=1, top_tc=6)
    assert ramp.bet(1) == 1
    assert ramp.bet(6) == 12
    assert ramp.bet(10) == 12  # capped beyond top_tc
