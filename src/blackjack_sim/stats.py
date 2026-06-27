"""Expected value and variance statistics over simulation results."""

from __future__ import annotations

import numpy as np
import pandas as pd

from .simulator import SimResult

_Z95 = 1.959964  # two-sided 95% normal quantile


def summarize(result: SimResult) -> dict:
    """Headline EV/variance figures for a run.

    ``ev_per_round`` is the mean net result per round (the bottom line a
    player experiences). ``ev_per_unit_wagered`` divides total net by total
    amount bet — the edge per dollar risked, which is comparable across flat
    and ramped betting.
    """
    net = result.net
    bet = result.bet
    n = net.size
    ev = float(net.mean())
    std = float(net.std(ddof=1))
    se = std / np.sqrt(n)
    total_wagered = float(bet.sum())
    return {
        "strategy": result.strategy,
        "rounds": n,
        "ev_per_round": ev,
        "std_per_round": std,
        "ci95_low": ev - _Z95 * se,
        "ci95_high": ev + _Z95 * se,
        "avg_bet": float(bet.mean()),
        "ev_per_unit_wagered": float(net.sum() / total_wagered),
        "total_net": float(net.sum()),
    }


def ev_by_true_count(result: SimResult, lo: int = -5, hi: int = 10) -> pd.DataFrame:
    """EV per round and per unit wagered, bucketed by rounded true count."""
    buckets = np.clip(np.round(result.true_count).astype(int), lo, hi)
    rows = []
    for k in range(lo, hi + 1):
        mask = buckets == k
        count = int(mask.sum())
        if count == 0:
            continue
        wagered = float(result.bet[mask].sum())
        rows.append(
            {
                "true_count": k,
                "n": count,
                "frequency": count / buckets.size,
                "avg_bet": float(result.bet[mask].mean()),
                "ev_per_round": float(result.net[mask].mean()),
                "ev_per_unit": float(result.net[mask].sum() / wagered),
            }
        )
    return pd.DataFrame(rows)


def bankroll_curve(result: SimResult) -> np.ndarray:
    """Cumulative net result over the run (a single bankroll trajectory)."""
    return np.cumsum(result.net)
