# Market research datasets — build the numbers instead of buying last year's report

Four questions a market research report answers, and how to answer each one yourself from live
data with the [QuanticData](https://quanticdata.io) APIs:

| Question | Built from |
|---|---|
| **Who competes here?** | [SERP API](https://quanticdata.io/serp-api/) share of voice across a keyword set |
| **What does it cost?** | [`google_shopping`](https://quanticdata.io/collectors/google-shopping-api/) + [`amazon_search`](https://quanticdata.io/collectors/amazon-scraper-api/) price distributions |
| **What do buyers complain about?** | [`place_reviews`](https://quanticdata.io/collectors/google-reviews-scraper-api/) + [`reddit_posts`](https://quanticdata.io/collectors/reddit-scraper-api/) |
| **Is it growing?** | [`keyword_ideas`](https://quanticdata.io/collectors/keyword-research-api/) breadth + [`google_news`](https://quanticdata.io/collectors/google-news-api/) volume + hiring counts |

Every number below is reproducible: same inputs, same day, same result — which is more than most
purchased reports can say.

[Market research data](https://quanticdata.io/market-research-data/)

```bash
pip install requests
export QUANTICDATA_API_KEY=qd_live_your_key_here

python3 share_of_voice.py keywords.txt --country us --out sov.csv
python3 price_landscape.py "espresso machine" --countries us gb de
python3 demand_signals.py "cold brew" --country us --out signals.json
```

## Files

| File | What it does |
|---|---|
| [`research.py`](research.py) | SERP + collector helpers used by everything here |
| [`share_of_voice.py`](share_of_voice.py) | who owns a keyword set, weighted by position |
| [`price_landscape.py`](price_landscape.py) | price distribution and brand mix, per market |
| [`demand_signals.py`](demand_signals.py) | keyword breadth, news volume, review sentiment, in one JSON |

## Share of voice, defined

Ranking first for one keyword is not "owning a market". `share_of_voice.py` weights each
appearance by a click-share curve and sums per domain across the whole keyword set:

```
weight(position) = 1 / position^0.6
share(domain)    = sum(weights) / sum(all weights)
```

The exponent matters and is a choice, not a fact — 0.6 is a flat-ish curve that credits page-one
presence rather than only the top spot. The script prints the raw appearance counts next to the
weighted share so you can see what the weighting did.

## Being honest about what this is

- **Live SERPs are a sample of one moment, in one place.** Run the same keyword set weekly and
  from more than one country before you call anything a trend.
- **Prices from Shopping are offers, not transactions.** Nobody publishes what things actually
  sold for.
- **Reviews over-represent the extremes.** They are excellent for *what* people complain about
  and poor for *how many* people are unhappy.
- **Hiring counts are a public surface**, not a headcount.

None of that makes the data useless — it makes it data rather than a conclusion. State the
method next to the number and the number becomes defensible.

## Related

- [Market research data](https://quanticdata.io/market-research-data/) · [SERP API](https://quanticdata.io/serp-api/) · [All collectors](https://quanticdata.io/collectors/)
- [What is web data?](https://quanticdata.io/blog/what-is-web-data/) · [How to use data for AI](https://quanticdata.io/blog/how-to-use-data-for-ai/)
- [Competitor price monitoring](https://quanticdata.io/competitor-price-monitoring/)

MIT licensed.
