"""Hand evaluation: totals, soft/hard detection, busts, and naturals.

A hand is a sequence of card base values (see :mod:`blackjack_sim.cards`).
Aces enter as 11 and are demoted to 1 as needed to avoid busting.
"""

from __future__ import annotations

from collections.abc import Sequence


def hand_value(cards: Sequence[int]) -> tuple[int, bool]:
    """Return the best total for a hand and whether it is soft.

    A hand is *soft* when it contains an ace still counted as 11 (i.e. the
    total could be reduced by 10 without going below the count).

    Returns:
        (total, is_soft). If the hand busts, total > 21 and is_soft is False.
    """
    total = sum(cards)
    aces = sum(1 for c in cards if c == 11)
    while total > 21 and aces:
        total -= 10
        aces -= 1
    return total, aces > 0


def is_soft(cards: Sequence[int]) -> bool:
    return hand_value(cards)[1]


def is_busted(cards: Sequence[int]) -> bool:
    return hand_value(cards)[0] > 21


def is_blackjack(cards: Sequence[int]) -> bool:
    """True for a two-card natural 21."""
    return len(cards) == 2 and hand_value(cards)[0] == 21
