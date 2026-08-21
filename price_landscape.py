"""Price distribution and brand mix for a category, per market.

Deciles rather than an average: a category with a €40 median and a €900 tail is a
different business from one with a €400 median, and the mean hides both.

    python3 price_landscape.py "espresso machine" --countries us gb de --max 60
"""
from __future__ import annotations

import argparse
import statistics
from collections import Counter

from research import collect


def deciles(values: list[float]) -> list[float]:
    return statistics.quantiles(sorted(values), n=10) if len(values) >= 10 else []


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("query")
    ap.add_argument("--countries", nargs="+", default=["us"])
    ap.add_argument("--max", type=int, default=60)
    args = ap.parse_args()

    for country in args.countries:
        try:
            shopping = collect("google_shopping", query=args.query, country=country,
                               max_results=args.max)
        except RuntimeError as exc:
            print(f"{country}: !! {exc}")
            continue

        priced = [r for r in shopping if r.get("price_value")]
        values = [r["price_value"] for r in priced]
        currencies = Counter(r.get("currency") for r in priced if r.get("currency"))
        currency = currencies.most_common(1)[0][0] if currencies else "?"

        print(f"\n=== {country.upper()} — {len(priced)} priced offers ({currency}) ===")
        if not values:
            continue

        print(f"min {min(values):,.2f}   median {statistics.median(values):,.2f}   "
              f"max {max(values):,.2f}")
        d = deciles(values)
        if d:
            print("deciles: " + "  ".join(f"{v:,.0f}" for v in d))

        buckets = Counter()
        top = max(values)
        step = max(top / 8, 1)
        for v in values:
            buckets[int(v // step)] += 1
        for index in sorted(buckets):
            low, high = index * step, (index + 1) * step
            bar = "#" * min(40, buckets[index] * 40 // max(buckets.values()))
            print(f"  {low:>8,.0f}–{high:<8,.0f} {buckets[index]:>4}  {bar}")

        print("\n  sellers")
        for seller, n in Counter(r.get("seller") for r in priced).most_common(8):
            of_theirs = [r["price_value"] for r in priced if r.get("seller") == seller]
            print(f"    {n:>3}  {str(seller)[:28]:<30} median {statistics.median(of_theirs):,.0f}")

        try:
            amazon = collect("amazon_search", query=args.query, country=country, max_results=40)
        except RuntimeError:
            continue
        organic = [r for r in amazon if not r.get("sponsored") and r.get("price_value")]
        if organic:
            print(f"\n  Amazon {country.upper()}: {len(organic)} organic results, "
                  f"median {statistics.median([r['price_value'] for r in organic]):,.2f}")
            for brand, n in Counter(r.get("brand") for r in organic if r.get("brand")).most_common(6):
                print(f"    {n:>3}  {brand}")


if __name__ == "__main__":
    main()
