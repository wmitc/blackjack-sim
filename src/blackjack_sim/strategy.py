"""Total-dependent basic strategy for multi-deck blackjack.

Encodes the canonical 4-8 deck basic strategy (dealer stands on soft 17, double
after split allowed by default) as a decision function. Decisions are returned
as single-character actions:

    "H" hit   "S" stand   "D" double   "P" split   "R" surrender

The caller passes capability flags (``can_double``, ``can_split``,
``can_surrender``); the function resolves unavailable actions to their standard
fallbacks (e.g. a double becomes a hit, a "double-else-stand" becomes a stand).

Rule-sensitive deviations handled:
- H17: double 11 vs ace, and double soft 19 vs 6.
- No-DAS: tighten the DAS-dependent pair splits (2s, 3s, 4s, 6s).
"""

from __future__ import annotations

from collections.abc import Sequence

from .hand import hand_value
from .rules import Rules

HIT = "H"
STAND = "S"
DOUBLE = "D"
SPLIT = "P"
SURRENDER = "R"


def _hard_action(total: int, up: int) -> str:
    """Action code for a hard total vs dealer upcard (up in 2..11, 11=ace)."""
    if total <= 8:
        return HIT
    if total == 9:
        return DOUBLE if 3 <= up <= 6 else HIT
    if total == 10:
        return DOUBLE if up <= 9 else HIT
    if total == 11:
        return DOUBLE if up <= 10 else HIT  # vs ace: see H17 nuance in caller
    if total == 12:
        return STAND if 4 <= up <= 6 else HIT
    if 13 <= total <= 16:
        return STAND if 2 <= up <= 6 else HIT
    return STAND  # 17+


def _soft_action(total: int, up: int) -> str:
    """Action code for a soft total. Returns "Ds" for double-else-stand."""
    if total in (13, 14):
        return DOUBLE if up in (5, 6) else HIT
    if total in (15, 16):
        return DOUBLE if up in (4, 5, 6) else HIT
    if total == 17:
        return DOUBLE if 3 <= up <= 6 else HIT
    if total == 18:
        if 2 <= up <= 6:
            return "Ds"
        if up in (7, 8):
            return STAND
        return HIT  # vs 9, 10, A
    return STAND  # 19, 20, 21


def _pair_action(card: int, up: int, rules: Rules) -> str | None:
    """Return SPLIT if the pair should be split, else None to fall through."""
    das = rules.double_after_split
    if card == 11:  # aces always split
        return SPLIT
    if card == 10:  # never split tens
        return None
    if card == 9:  # split except vs 7, 10, A (stand on 18)
        return SPLIT if up in (2, 3, 4, 5, 6, 8, 9) else None
    if card == 8:  # always split
        return SPLIT
    if card == 7:
        return SPLIT if 2 <= up <= 7 else None
    if card == 6:
        lo = 2 if das else 3
        return SPLIT if lo <= up <= 6 else None
    if card == 5:  # never split; play as hard 10
        return None
    if card == 4:
        return SPLIT if (das and up in (5, 6)) else None
    if card in (2, 3):
        lo = 2 if das else 4
        return SPLIT if lo <= up <= 7 else None
    return None


def basic_strategy_action(
    cards: Sequence[int],
    dealer_up: int,
    rules: Rules,
    *,
    can_double: bool = True,
    can_split: bool = True,
    can_surrender: bool = False,
) -> str:
    """Return the basic-strategy action for a hand vs the dealer upcard."""
    total, soft = hand_value(cards)

    # Late surrender is only available on the original first two cards.
    if can_surrender and len(cards) == 2 and not soft:
        if total == 16 and dealer_up in (9, 10, 11):
            return SURRENDER
        if total == 15 and dealer_up == 10:
            return SURRENDER

    if can_split and len(cards) == 2 and cards[0] == cards[1]:
        if _pair_action(cards[0], dealer_up, rules) == SPLIT:
            return SPLIT

    if soft:
        code = _soft_action(total, dealer_up)
        if total == 19 and dealer_up == 6 and rules.dealer_hits_soft_17:
            code = "Ds"  # double soft 19 vs 6 under H17
    else:
        code = _hard_action(total, dealer_up)
        if total == 11 and dealer_up == 11 and rules.dealer_hits_soft_17:
            code = DOUBLE  # double 11 vs ace under H17

    if code == DOUBLE:
        return DOUBLE if can_double else HIT
    if code == "Ds":
        return DOUBLE if can_double else STAND
    return code
