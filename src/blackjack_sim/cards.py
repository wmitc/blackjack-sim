"""Shoe construction and dealing.

Cards are represented purely by their blackjack base value, which is all the
engine and the Hi-Lo counter need:

    2-9   -> the pip value
    10    -> any ten-value card (10, J, Q, K)
    11    -> ace (counted as 11, demoted to 1 by hand-value logic)

A single deck therefore contains four each of 2..9, sixteen tens, and four
aces (52 cards total).
"""

from __future__ import annotations

import numpy as np

# Card values present in one deck, with their per-deck multiplicities.
_SINGLE_DECK = np.array(
    [v for v in range(2, 10) for _ in range(4)]  # 2..9, four each
    + [10] * 16                                   # 10, J, Q, K
    + [11] * 4,                                    # aces
    dtype=np.int8,
)
assert _SINGLE_DECK.size == 52


class Shoe:
    """A shuffled multi-deck shoe dealt from the top with a cut card."""

    def __init__(
        self,
        num_decks: int = 6,
        penetration: float = 0.75,
        rng: np.random.Generator | None = None,
    ) -> None:
        self.num_decks = num_decks
        self.penetration = penetration
        self.rng = rng if rng is not None else np.random.default_rng()
        self._base = np.tile(_SINGLE_DECK, num_decks)
        self.total = int(self._base.size)
        self._cut = int(self.penetration * self.total)
        self.reshuffle()

    def reshuffle(self) -> None:
        """Reset to a full, freshly shuffled shoe."""
        self.cards = self._base.copy()
        self.rng.shuffle(self.cards)
        self.pos = 0

    def deal(self) -> int:
        """Deal and return the next card value."""
        if self.pos >= self.total:
            raise IndexError("shoe exhausted")
        card = int(self.cards[self.pos])
        self.pos += 1
        return card

    @property
    def cards_dealt(self) -> int:
        return self.pos

    @property
    def cards_remaining(self) -> int:
        return self.total - self.pos

    @property
    def decks_remaining(self) -> float:
        """Decks left, used to convert running count to true count."""
        return self.cards_remaining / 52.0

    def needs_reshuffle(self) -> bool:
        """True once the cut card (penetration point) has been reached."""
        return self.pos >= self._cut
