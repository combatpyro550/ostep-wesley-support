#!/usr/bin/env python3
"""Refresh fundraiser-data.json from the public GiveSendGo campaign page."""

from __future__ import annotations

import html
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen


CAMPAIGN_URL = (
    "https://www.givesendgo.com/"
    "legal-support-for-osteps-immigration-cou"
)
OUTPUT_PATH = Path(__file__).resolve().parents[1] / "fundraiser-data.json"


def fetch_campaign() -> str:
    request = Request(
        CAMPAIGN_URL,
        headers={
            "User-Agent": "Mozilla/5.0 StandWithOstep fundraiser updater/1.0",
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Language": "en-US,en;q=0.9",
        },
    )
    with urlopen(request, timeout=30) as response:
        return response.read().decode(
            response.headers.get_content_charset() or "utf-8",
            errors="replace",
        )


def extract_amount(page: str, label: str) -> int:
    match = re.search(
        rf'aria-label=["\']{label}:\s*[^\d]*([\d,]+)(?:\.\d+)?\s+USD["\']',
        html.unescape(page),
        re.IGNORECASE,
    )
    if not match:
        raise RuntimeError(f"Could not locate the {label} amount")
    return int(match.group(1).replace(",", ""))


def main() -> None:
    page = fetch_campaign()
    goal = extract_amount(page, "Goal")
    raised = extract_amount(page, "Raised")

    if OUTPUT_PATH.exists():
        current = json.loads(OUTPUT_PATH.read_text(encoding="utf-8"))
        if (
            current.get("goal") == goal
            and current.get("raised") == raised
            and current.get("currency") == "USD"
        ):
            print(f"No change: Goal ${goal:,}; Raised ${raised:,}")
            return

    totals = {
        "goal": goal,
        "raised": raised,
        "currency": "USD",
        "updated_at": datetime.now(timezone.utc).isoformat(timespec="seconds")
        .replace("+00:00", "Z"),
        "source": CAMPAIGN_URL,
    }
    OUTPUT_PATH.write_text(json.dumps(totals, indent=2) + "\n", encoding="utf-8")
    print(f"Goal: ${totals['goal']:,}; Raised: ${totals['raised']:,}")


if __name__ == "__main__":
    main()
