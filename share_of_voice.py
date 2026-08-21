"""Who owns a keyword set, weighted by position.

    python3 share_of_voice.py keywords.txt --country us --num 10 --out sov.csv
"""
from __future__ import annotations

import argparse
import csv
import pathlib
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor

from research import click_weight, domain, serp


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("file", type=pathlib.Path)
    ap.add_argument("--country", default="us")
    ap.add_argument("--lang", default=None)
    ap.add_argument("--num", type=int, default=10)
    ap.add_argument("--exponent", type=float, default=0.6)
    ap.add_argument("--workers", type=int, default=5)
    ap.add_argument("--out", default="sov.csv")
    args = ap.parse_args()

    keywords = [ln.strip() for ln in args.file.read_text(encoding="utf-8").splitlines() if ln.strip()]

    def run(keyword: str):
        try:
            return keyword, serp(keyword, country=args.country, lang=args.lang, num=args.num), None
        except RuntimeError as exc:
            return keyword, {}, str(exc)

    weights: dict[str, float] = defaultdict(float)
    appearances = Counter()
    best_rank: dict[str, int] = {}
    keywords_per_domain: dict[str, set] = defaultdict(set)
    total_weight = 0.0
    failed = 0

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        for keyword, payload, error in pool.map(run, keywords):
            if error:
                failed += 1
                print(f"!! {keyword}: {error}")
                continue
            for row in payload.get("organic") or []:
                host = domain(row.get("link"))
                if not host:
                    continue
                w = click_weight(int(row.get("position") or 99), args.exponent)
                weights[host] += w
                total_weight += w
                appearances[host] += 1
                keywords_per_domain[host].add(keyword)
                best_rank[host] = min(best_rank.get(host, 99), int(row.get("position") or 99))

    ranked = sorted(weights.items(), key=lambda kv: -kv[1])

    with open(args.out, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["domain", "share", "weighted_score", "appearances", "keywords", "best_rank"])
        for host, score in ranked:
            w.writerow([host, round(score / total_weight, 4), round(score, 3),
                        appearances[host], len(keywords_per_domain[host]), best_rank[host]])

    covered = len(keywords) - failed
    print(f"\n{covered} keywords, {len(ranked)} domains, exponent {args.exponent}\n")
    print(f"{'domain':<34}{'share':>8}{'hits':>7}{'kw':>6}{'best':>6}")
    for host, score in ranked[:20]:
        bar = "#" * round(40 * score / ranked[0][1])
        print(f"{host[:33]:<34}{100 * score / total_weight:>7.1f}%{appearances[host]:>7}"
              f"{len(keywords_per_domain[host]):>6}{best_rank[host]:>6}  {bar}")
    print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()
