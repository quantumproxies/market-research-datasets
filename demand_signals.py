"""Four signals for one category, in one JSON: breadth, news, discussion, sentiment.

None of these is a market size. Together they answer "is anything happening here",
which is the question a market scan is actually for.

    python3 demand_signals.py "cold brew" --country us --out signals.json
"""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from datetime import datetime, timezone

from research import collect, serp

STOP = set("""the a an and or of for to in on with is are was be this that it its
they you your our we i my me as at by from but not no can how what why""".split())


def words(text: str) -> list[str]:
    return [w for w in re.findall(r"[a-z']{4,}", (text or "").lower()) if w not in STOP]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("seed")
    ap.add_argument("--country", default="us")
    ap.add_argument("--lang", default="en")
    ap.add_argument("--out", default="signals.json")
    args = ap.parse_args()

    signals: dict = {"seed": args.seed, "country": args.country,
                     "collected_at": datetime.now(timezone.utc).isoformat(timespec="seconds")}

    # 1. Breadth of demand — how many distinct things people type around the seed.
    keywords = collect("keyword_ideas", seed=args.seed, modes=["seed", "questions", "alphabet"],
                       country=args.country, lang=args.lang, max_results=300)
    signals["keyword_breadth"] = {
        "total": len(keywords),
        "questions": sum(1 for k in keywords if (k.get("keyword") or "").split()[:1]
                         and (k.get("keyword") or "").split()[0] in
                         ("how", "what", "why", "is", "can", "does", "are")),
        "long_tail": sum(1 for k in keywords if len((k.get("keyword") or "").split()) >= 4),
        "sample": [k.get("keyword") for k in keywords[:15]],
    }
    print(f"keywords     {len(keywords)}")

    # 2. Press attention.
    news = collect("google_news", query=args.seed, country=args.country,
                   lang=args.lang, max_results=50)
    signals["news"] = {
        "articles": len(news),
        "sources": Counter(n.get("source") for n in news).most_common(10),
        "latest": [{"date": n.get("date"), "title": n.get("title"), "source": n.get("source")}
                   for n in news[:8]],
    }
    print(f"news         {len(news)} articles from {len({n.get('source') for n in news})} sources")

    # 3. What people say to each other, unprompted.
    reddit = collect("reddit_posts", query=args.seed, sort="top", time="year",
                     country=args.country, max_results=60)
    vocabulary = Counter(w for p in reddit for w in words(p.get("title")))
    signals["discussion"] = {
        "posts": len(reddit),
        "subreddits": Counter(p.get("subreddit") for p in reddit).most_common(10),
        "total_comments": sum(p.get("comments") or 0 for p in reddit),
        "vocabulary": vocabulary.most_common(20),
        "top_posts": [{"title": p.get("title"), "subreddit": p.get("subreddit"),
                       "score": p.get("score"), "comments": p.get("comments"),
                       "permalink": p.get("permalink")} for p in reddit[:8]],
    }
    print(f"reddit       {len(reddit)} posts, "
          f"{sum(p.get('comments') or 0 for p in reddit)} comments")

    # 4. What the SERP itself thinks the intent is.
    page = serp(args.seed, country=args.country, lang=args.lang, num=10)
    signals["serp"] = {
        "results_count": page.get("results_count"),
        "has_shopping": bool(page.get("shopping")),
        "has_local": bool(page.get("local_pack") or page.get("places")),
        "related_searches": page.get("related_searches") or [],
        "top_domains": [r.get("link") for r in (page.get("organic") or [])[:10]],
    }
    print(f"serp         {page.get('results_count')} results, "
          f"shopping={bool(page.get('shopping'))} local={bool(page.get('local_pack'))}")

    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(signals, fh, indent=2, ensure_ascii=False)
    print(f"\nwrote {args.out}")

    print("\nwhat people actually talk about:")
    for word, n in vocabulary.most_common(15):
        print(f"  {n:>3}  {word}")


if __name__ == "__main__":
    main()
