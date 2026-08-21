"""SERP and collector helpers for the market research scripts."""
from __future__ import annotations

import os
import time
from typing import Any
from urllib.parse import urlparse

import requests

BASE = "https://api.quanticdata.io/v1"
_s = requests.Session()


def _h() -> dict[str, str]:
    key = os.environ.get("QUANTICDATA_API_KEY")
    if not key:
        raise SystemExit("set QUANTICDATA_API_KEY — https://app.quanticdata.io/register")
    return {"Authorization": f"Bearer {key}"}


def _payload(r: requests.Response, what: str) -> dict:
    data = r.json()
    if data.get("type") == "error" or not r.ok:
        raise RuntimeError(f"{what} ({r.status_code}): {data.get('message')}")
    return data.get("payload", {})


def serp(query: str, **params: Any) -> dict:
    return _payload(_s.post(f"{BASE}/serp", json={"query": query, **params},
                            headers=_h(), timeout=120), "serp")


def collect(slug: str, **input_: Any) -> list[dict]:
    body = {k: v for k, v in input_.items() if v not in (None, "", [], False)}
    run = _payload(_s.post(f"{BASE}/scraper/collectors/{slug}/run", json=body,
                           headers=_h(), timeout=300), slug)
    while run.get("status") in ("queued", "running"):
        time.sleep(3)
        run = _payload(_s.get(f"{BASE}/scraper/collectors/runs/{run['run_id']}",
                              headers=_h(), timeout=60), "run status")
    return run.get("results") or []


def domain(url: str | None) -> str:
    try:
        return urlparse(url or "").netloc.lower().removeprefix("www.")
    except ValueError:
        return ""


def click_weight(position: int, exponent: float = 0.6) -> float:
    """A flat-ish click-share curve: credits page-one presence, not only rank 1."""
    return 1.0 / max(position, 1) ** exponent
