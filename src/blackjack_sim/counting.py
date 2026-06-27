"""Hi-Lo card counting and true-count bet ramp.

Hi-Lo tags by card base value (see :mod:`blackjack_sim.cards`):

    2-6  -> +1   (low cards, good for the player when gone)
    7-9  ->  0
    10,A -> -1   (high cards)

The *running count* is the sum of tags over the cards already dealt; the
*true count* normalises it by the number of decks remaining, which is what
drives bet sizing. :class:`HiLoCounter` tracks the running count incrementally
off a live :class:`~blackjack_sim.cards.Shoe`.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .cards import Shoe


def tag_array(values) -> np.ndarray:
    """Vectorised Hi-Lo tags for an array of card values."""
    v = np.asarray(values)
    return np.where(v <= 6, 1, np.where(v <= 9, 0, -1))


def hi_lo_tag(card: int) -> int:
    """Hi-Lo tag for a single card value."""
    if card <= 6:
        return 1
    if card <= 9:
        return 0
    return -1


def running_count(cards) -> int:
    """Running count over an iterable/array of card values."""
    arr = cards if isinstance(cards, np.ndarray) else np.fromiter(cards, dtype=int)
    return int(tag_array(arr).sum())


def true_count(running: int, decks_remaining: float) -> float:
    """Convert a running count to a true count; 0 when no decks remain."""
    return running / decks_remaining if decks_remaining > 0 else 0.0


class HiLoCounter:
    """Tracks the Hi-Lo running/true count for a shoe as cards are dealt.

    The counter reads newly dealt cards straight off the shoe, so the engine
    needs no instrumentation. Call :meth:`sync` after a round (when every card,
    including the dealer hole card, is exposed) and :meth:`reset` on reshuffle.
    """

    def __init__(self, shoe: Shoe) -> None:
        self.shoe = shoe
        self.running = 0
        self._seen = 0

    def sync(self) -> None:
        """Fold cards dealt since the last sync into the running count."""
        new = self.shoe.cards[self._seen:self.shoe.pos]
        if new.size:
            self.running += int(tag_array(new).sum())
            self._seen = self.shoe.pos

    def reset(self) -> None:
        """Reset for a freshly shuffled shoe."""
        self.running = 0
        self._seen = 0

    @property
    def true_count(self) -> float:
        return true_count(self.running, self.shoe.decks_remaining)


@dataclass
class BetRamp:
    """Maps the true count to a bet size in units.

    Flat ``min_bet`` at or below ``tc_threshold``, then rises linearly by
    ``units_per_tc`` per additional point of true count, capped at ``max_bet``.
    """

    min_bet: float = 1.0
    max_bet: float = 12.0
    tc_threshold: float = 1.0
    units_per_tc: float = 2.0

    def bet(self, tc: float) -> float:
        if tc <= self.tc_threshold:
            return self.min_bet
        sized = self.min_bet + (tc - self.tc_threshold) * self.units_per_tc
        return min(sized, self.max_bet)

    @classmethod
    def from_spread(
        cls,
        min_bet: float,
        max_bet: float,
        tc_threshold: float = 1.0,
        top_tc: float = 6.0,
    ) -> "BetRamp":
        """Build a ramp that reaches ``max_bet`` at true count ``top_tc``."""
        span = max(top_tc - tc_threshold, 1e-9)
        return cls(
            min_bet=min_bet,
            max_bet=max_bet,
            tc_threshold=tc_threshold,
            units_per_tc=(max_bet - min_bet) / span,
        )
