"""Round engine: deals a hand, plays it under basic strategy, settles payouts.

A single call to :func:`play_round` plays one full round (which may include
splits) and returns the net result in bet units. Counting affects *betting*,
not *playing*, in this project, so the engine always plays basic strategy; the
caller (simulator) reads the count off the shoe and sets ``bet`` accordingly.
"""

from __future__ import annotations

from dataclasses import dataclass

from .cards import Shoe
from .hand import hand_value, is_blackjack
from .rules import Rules
from .strategy import basic_strategy_action


@dataclass
class Hand:
    """A single player hand within a round."""

    cards: list[int]
    bet: float
    is_split: bool = False
    split_aces: bool = False
    doubled: bool = False
    surrendered: bool = False


def _play_hand(
    hand: Hand,
    hands: list[Hand],
    shoe: Shoe,
    rules: Rules,
    dealer_up: int,
    splits: dict[str, int],
) -> None:
    """Play one hand to completion, appending new hands when it splits."""
    while True:
        # Split aces normally receive exactly one card, then stand.
        if hand.split_aces and not rules.hit_split_aces:
            return

        total, _ = hand_value(hand.cards)
        if total >= 21:
            return  # 21 or bust: nothing more to decide

        first_decision = len(hand.cards) == 2
        is_pair = first_decision and hand.cards[0] == hand.cards[1]
        can_split = (
            is_pair
            and splits["count"] < rules.max_splits
            and (hand.cards[0] != 11 or rules.resplit_aces or not hand.is_split)
        )
        can_double = (
            first_decision
            and rules.double_any
            and (not hand.is_split or rules.double_after_split)
        )
        can_surrender = first_decision and not hand.is_split and rules.late_surrender

        action = basic_strategy_action(
            hand.cards,
            dealer_up,
            rules,
            can_double=can_double,
            can_split=can_split,
            can_surrender=can_surrender,
        )

        if action == "R":
            hand.surrendered = True
            return
        if action == "S":
            return
        if action == "H":
            hand.cards.append(shoe.deal())
            continue
        if action == "D":
            hand.bet *= 2
            hand.doubled = True
            hand.cards.append(shoe.deal())
            return
        if action == "P":
            splits["count"] += 1
            rank = hand.cards[0]
            is_ace = rank == 11
            new = Hand(
                cards=[rank, shoe.deal()],
                bet=hand.bet,
                is_split=True,
                split_aces=is_ace,
            )
            hand.cards = [rank, shoe.deal()]
            hand.is_split = True
            hand.split_aces = is_ace
            hands.append(new)
            continue
        raise AssertionError(f"unknown action: {action}")


def _play_dealer(dealer: list[int], shoe: Shoe, rules: Rules) -> None:
    """Draw dealer cards per the S17/H17 rule."""
    while True:
        total, soft = hand_value(dealer)
        if total < 17 or (total == 17 and soft and rules.dealer_hits_soft_17):
            dealer.append(shoe.deal())
            continue
        return


def play_round(shoe: Shoe, rules: Rules, bet: float = 1.0) -> float:
    """Play one round and return the net result in bet units."""
    player = [shoe.deal(), shoe.deal()]
    dealer = [shoe.deal(), shoe.deal()]
    dealer_up = dealer[0]

    player_natural = is_blackjack(player)

    # Dealer peeks for blackjack only on a ten or ace upcard.
    if dealer_up in (10, 11) and is_blackjack(dealer):
        return 0.0 if player_natural else -bet
    if player_natural:
        return rules.blackjack_payout * bet

    hands = [Hand(cards=player, bet=bet)]
    splits = {"count": 0}
    i = 0
    while i < len(hands):
        _play_hand(hands[i], hands, shoe, rules, dealer_up, splits)
        i += 1

    # Dealer only draws if at least one player hand can still win.
    live = any(
        not h.surrendered and hand_value(h.cards)[0] <= 21 for h in hands
    )
    if live:
        _play_dealer(dealer, shoe, rules)
    dealer_total = hand_value(dealer)[0]

    result = 0.0
    for h in hands:
        if h.surrendered:
            result -= h.bet / 2
            continue
        player_total = hand_value(h.cards)[0]
        if player_total > 21:
            result -= h.bet
        elif dealer_total > 21 or player_total > dealer_total:
            result += h.bet
        elif player_total < dealer_total:
            result -= h.bet
        # equal totals push
    return result
