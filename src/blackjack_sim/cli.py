"""Command-line entry point for the blackjack simulator.

Examples:
    python -m blackjack_sim.cli --rounds 1000000 --decks 6
    python -m blackjack_sim.cli --strategy counting --spread 1-12 --out results/
"""

from __future__ import annotations

import argparse
from pathlib import Path

from .counting import BetRamp
from .rules import Rules
from .simulator import simulate
from .stats import ev_by_true_count, summarize


def _parse_spread(spread: str) -> tuple[float, float]:
    try:
        lo, hi = spread.split("-")
        return float(lo), float(hi)
    except ValueError as exc:  # pragma: no cover - argparse reports the message
        raise argparse.ArgumentTypeError(
            f"spread must look like 'MIN-MAX', got {spread!r}"
        ) from exc


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="blackjack-sim",
        description="Monte Carlo blackjack: EV & variance of basic strategy vs "
        "Hi-Lo card counting.",
    )
    p.add_argument("--rounds", type=int, default=500_000, help="rounds per run")
    p.add_argument("--decks", type=int, default=6, help="number of decks")
    p.add_argument("--penetration", type=float, default=0.75,
                   help="fraction of shoe dealt before reshuffle")
    p.add_argument("--h17", action="store_true",
                   help="dealer hits soft 17 (default: stands)")
    p.add_argument("--no-das", action="store_true",
                   help="disallow double after split")
    p.add_argument("--strategy", choices=["both", "basic", "counting"],
                   default="both", help="which strategy to simulate")
    p.add_argument("--spread", type=str, default="1-12",
                   help="bet spread MIN-MAX for counting (e.g. 1-12)")
    p.add_argument("--top-tc", type=float, default=6.0,
                   help="true count at which the bet reaches the max spread")
    p.add_argument("--seed", type=int, default=42, help="RNG seed")
    p.add_argument("--out", type=str, default=None,
                   help="directory to write summary and EV-by-true-count CSVs")
    return p


def _fmt_summary(s: dict) -> str:
    return (
        f"  rounds              : {s['rounds']:,}\n"
        f"  avg bet             : {s['avg_bet']:.3f} units\n"
        f"  EV / round          : {s['ev_per_round']:+.4f} units "
        f"(95% CI [{s['ci95_low']:+.4f}, {s['ci95_high']:+.4f}])\n"
        f"  EV / unit wagered   : {s['ev_per_unit_wagered']:+.4%}\n"
        f"  std / round         : {s['std_per_round']:.3f} units\n"
        f"  total net           : {s['total_net']:+,.1f} units"
    )


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    rules = Rules(
        num_decks=args.decks,
        penetration=args.penetration,
        dealer_hits_soft_17=args.h17,
        double_after_split=not args.no_das,
    )
    lo, hi = _parse_spread(args.spread)
    ramp = BetRamp.from_spread(lo, hi, top_tc=args.top_tc)

    runs = ["basic", "counting"] if args.strategy == "both" else [args.strategy]

    print(f"Rules: {args.decks} decks, "
          f"{'H17' if args.h17 else 'S17'}, "
          f"{'no DAS' if args.no_das else 'DAS'}, "
          f"penetration {args.penetration:.0%}, seed {args.seed}\n")

    summaries = {}
    tc_table = None
    for strategy in runs:
        result = simulate(args.rounds, rules, strategy=strategy,
                          ramp=ramp, seed=args.seed)
        s = summarize(result)
        summaries[strategy] = s
        label = strategy.upper()
        if strategy == "counting":
            label += f" (spread {args.spread}, max at TC {args.top_tc:g})"
        print(f"[{label}]")
        print(_fmt_summary(s))
        print()
        if strategy == "counting":
            tc_table = ev_by_true_count(result)
            print("EV by true count (counting):")
            print(tc_table.to_string(index=False,
                                     float_format=lambda x: f"{x:.4f}"))
            print()

    if "basic" in summaries and "counting" in summaries:
        delta = (summaries["counting"]["ev_per_round"]
                 - summaries["basic"]["ev_per_round"])
        print(f"Counting shifts EV/round by {delta:+.4f} units "
              f"({summaries['basic']['ev_per_round']:+.4f} -> "
              f"{summaries['counting']['ev_per_round']:+.4f}).")

    if args.out:
        out = Path(args.out)
        out.mkdir(parents=True, exist_ok=True)
        import pandas as pd

        pd.DataFrame(list(summaries.values())).to_csv(
            out / "summary.csv", index=False)
        if tc_table is not None:
            tc_table.to_csv(out / "ev_by_true_count.csv", index=False)
        print(f"\nWrote CSVs to {out}/")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
