"""Spot checks against known basic-strategy decisions (4-8 deck, S17, DAS)."""

from blackjack_sim.rules import Rules
from blackjack_sim.strategy import basic_strategy_action

S17 = Rules(dealer_hits_soft_17=False)
H17 = Rules(dealer_hits_soft_17=True)
NO_DAS = Rules(double_after_split=False)


def act(cards, up, rules=S17, **kw):
    return basic_strategy_action(cards, up, rules, **kw)


def test_hard_totals():
    assert act([10, 6], 10) == "H"   # 16 vs 10 -> hit
    assert act([10, 6], 6) == "S"    # 16 vs 6 -> stand
    assert act([10, 2], 4) == "S"    # 12 vs 4 -> stand
    assert act([10, 2], 3) == "H"    # 12 vs 3 -> hit
    assert act([10, 7], 10) == "S"   # 17 -> stand


def test_doubles():
    assert act([5, 6], 5) == "D"     # 11 -> double
    assert act([5, 4], 6) == "D"     # 9 vs 6 -> double
    assert act([5, 4], 7) == "H"     # 9 vs 7 -> hit
    # Double unavailable -> falls back to hit
    assert act([5, 6], 5, can_double=False) == "H"


def test_soft_hands():
    assert act([11, 6], 3) == "D"    # soft 17 vs 3 -> double
    assert act([11, 7], 9) == "H"    # soft 18 vs 9 -> hit
    assert act([11, 7], 2) == "D"    # soft 18 vs 2 -> double
    # soft 18 "double else stand" falls back to stand
    assert act([11, 7], 2, can_double=False) == "S"
    assert act([11, 8], 6) == "S"    # soft 19 vs 6 (S17) -> stand


def test_pairs():
    assert act([8, 8], 10) == "P"    # always split eights
    assert act([11, 11], 5) == "P"   # always split aces
    assert act([10, 10], 6) == "S"   # never split tens -> stand 20
    assert act([5, 5], 6) == "D"     # never split fives -> double (hard 10)
    assert act([9, 9], 7) == "S"     # nines stand vs 7
    assert act([9, 9], 9) == "P"     # nines split vs 9
    # Split unavailable -> play as the total
    assert act([8, 8], 10, can_split=False) == "H"  # hard 16 vs 10


def test_surrender():
    assert act([10, 6], 10, can_surrender=True) == "R"  # 16 vs 10
    assert act([10, 5], 10, can_surrender=True) == "R"  # 15 vs 10
    assert act([10, 6], 7, can_surrender=True) == "H"   # 16 vs 7 -> hit
    # Without the option, play normally
    assert act([10, 6], 10) == "H"


def test_h17_deviations():
    assert act([5, 6], 11, H17) == "D"   # double 11 vs A under H17
    assert act([5, 6], 11, S17) == "H"   # but only hit under S17
    assert act([11, 8], 6, H17) == "D"   # double soft 19 vs 6 under H17


def test_no_das_tightens_splits():
    # 4,4 splits only with DAS
    assert act([4, 4], 5, S17) == "P"
    assert act([4, 4], 5, NO_DAS) == "H"
