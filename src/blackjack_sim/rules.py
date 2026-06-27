"""Configurable blackjack table rules.

Each field corresponds to a rule that materially affects the house edge, so
the simulator can quantify EV/variance under different rule sets.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Rules:
    """Table rules for a blackjack game.

    Attributes:
        num_decks: Number of 52-card decks in the shoe.
        dealer_hits_soft_17: If True the dealer hits soft 17 (H17), else S17.
        blackjack_payout: Payout multiple on a natural (1.5 == 3:2, 1.2 == 6:5).
        double_after_split: Whether doubling is allowed after a split (DAS).
        double_any: If True, doubling is allowed on any first two cards.
        max_splits: Maximum number of split operations per round (3 => 4 hands).
        resplit_aces: Whether split aces may be re-split.
        hit_split_aces: If False, split aces receive exactly one card each.
        late_surrender: Whether late surrender is offered.
        penetration: Fraction of the shoe dealt before reshuffling (0-1).
    """

    num_decks: int = 6
    dealer_hits_soft_17: bool = False
    blackjack_payout: float = 1.5
    double_after_split: bool = True
    double_any: bool = True
    max_splits: int = 3
    resplit_aces: bool = False
    hit_split_aces: bool = False
    late_surrender: bool = False
    penetration: float = 0.75

    def __post_init__(self) -> None:
        if self.num_decks < 1:
            raise ValueError("num_decks must be >= 1")
        if not 0.0 < self.penetration <= 1.0:
            raise ValueError("penetration must be in (0, 1]")
        if self.blackjack_payout <= 0:
            raise ValueError("blackjack_payout must be positive")
