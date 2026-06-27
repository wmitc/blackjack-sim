"""Tests for the shoe."""

import numpy as np

from blackjack_sim.cards import Shoe, _SINGLE_DECK


def test_single_deck_composition():
    assert _SINGLE_DECK.size == 52
    values, counts = np.unique(_SINGLE_DECK, return_counts=True)
    comp = dict(zip(values.tolist(), counts.tolist()))
    for v in range(2, 10):
        assert comp[v] == 4
    assert comp[10] == 16
    assert comp[11] == 4


def test_shoe_size_and_dealing():
    shoe = Shoe(num_decks=6, rng=np.random.default_rng(0))
    assert shoe.total == 6 * 52
    assert shoe.cards_remaining == 312
    first = shoe.deal()
    assert 2 <= first <= 11
    assert shoe.cards_dealt == 1
    assert shoe.cards_remaining == 311


def test_shoe_preserves_composition():
    shoe = Shoe(num_decks=2, rng=np.random.default_rng(42))
    dealt = sorted(shoe.deal() for _ in range(shoe.total))
    assert dealt == sorted(np.tile(_SINGLE_DECK, 2).tolist())


def test_reshuffle_and_penetration():
    shoe = Shoe(num_decks=1, penetration=0.5, rng=np.random.default_rng(1))
    for _ in range(25):
        shoe.deal()
    assert not shoe.needs_reshuffle()
    shoe.deal()  # 26th of 52 -> reaches cut
    assert shoe.needs_reshuffle()
    shoe.reshuffle()
    assert shoe.cards_dealt == 0
    assert not shoe.needs_reshuffle()


def test_decks_remaining():
    shoe = Shoe(num_decks=6, rng=np.random.default_rng(7))
    assert shoe.decks_remaining == 6.0
    for _ in range(52):
        shoe.deal()
    assert shoe.decks_remaining == 5.0
