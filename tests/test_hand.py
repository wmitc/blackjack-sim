"""Tests for hand evaluation."""

from blackjack_sim.hand import hand_value, is_blackjack, is_busted, is_soft


def test_hard_total():
    assert hand_value([10, 7]) == (17, False)
    assert hand_value([5, 4, 3]) == (12, False)


def test_soft_total():
    # Ace + 6 = soft 17
    assert hand_value([11, 6]) == (17, True)
    # Ace counted as 11 with room to spare
    assert hand_value([11, 2]) == (13, True)


def test_ace_demotes_to_avoid_bust():
    # Ace + 6 + 10 -> 17 hard (ace demoted)
    assert hand_value([11, 6, 10]) == (17, False)


def test_multiple_aces():
    # Two aces = 12, one counted as 11 -> soft
    assert hand_value([11, 11]) == (12, True)
    # Three aces stay <= 21, exactly one as 11 -> soft 13
    assert hand_value([11, 11, 11]) == (13, True)
    # A + A + 9 = 21 soft
    assert hand_value([11, 11, 9]) == (21, True)


def test_blackjack_detection():
    assert is_blackjack([11, 10])
    assert is_blackjack([10, 11])
    # 21 on three cards is not a natural
    assert not is_blackjack([7, 7, 7])
    assert not is_blackjack([11, 9])


def test_bust():
    assert is_busted([10, 10, 5])
    assert not is_busted([10, 10])  # 20 is not a bust
    assert is_busted([11, 11, 11, 10, 10])  # all aces hard -> bust


def test_is_soft_helper():
    assert is_soft([11, 5])
    assert not is_soft([10, 5, 6])
