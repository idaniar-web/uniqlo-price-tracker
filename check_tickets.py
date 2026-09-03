import html
import sys
from pathlib import Path

import requests

from notify import load_json, save_json, send_telegram

ROOT = Path(__file__).parent
WATCHLIST_PATH = ROOT / "tickets_watchlist.json"
STATE_PATH = ROOT / "tickets_state.json"

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; OperaTicketTracker/1.0)"}

# Opéra de Paris marks a performance bookable by swapping the row's action from
# "alert" (Créer une alerte) to "CTABook" (Réserver). "CTAOption" is the resale
# marketplace (bourse aux billets) and is deliberately not treated as bookable.
BOOKABLE_ACTION = "CTABook"


def fetch_rows(url):
    response = requests.get(url, headers=HEADERS, timeout=30)
    response.raise_for_status()
    response.encoding = "utf-8"
    return response.json()["body"]["rows"]


def describe_date(row):
    date = row["date"]
    return f"{date['day']} {date['dayNumber']} {date['month']} {date['time']}"


def describe_prices(row):
    parts = []
    for category in row.get("categories", []):
        price = html.unescape(category.get("price") or "").strip()
        parts.append(f"{category.get('title')} {price}".strip())
    return ", ".join(parts)


def find_booking_url(row):
    for action in row.get("actions", []):
        if action.get("type") == BOOKABLE_ACTION:
            return action.get("url")
    return None


def main():
    if "--test" in sys.argv:
        send_telegram("Opéra ticket tracker: test notification, setup works.")
        return

    watchlist = load_json(WATCHLIST_PATH, [])
    state = load_json(STATE_PATH, {})

    for entry in watchlist:
        try:
            rows = fetch_rows(entry["url"])
        except Exception as exc:
            print(f"[error] {entry['url']}: {exc}", file=sys.stderr)
            continue

        rows_by_id = {row["perfId"]: row for row in rows}

        for perf_id in entry["perf_ids"]:
            row = rows_by_id.get(perf_id)
            if row is None:
                print(f"[error] performance {perf_id} not found at {entry['url']}", file=sys.stderr)
                continue

            when = describe_date(row)
            booking_url = find_booking_url(row)
            status = "bookable" if booking_url else "unavailable"
            tags = ", ".join(tag.get("text", "") for tag in row.get("tags", []))
            print(f"[ok] {perf_id} {when}: {status} ({tags})")

            key = str(perf_id)
            if status == "bookable" and state.get(key) != "bookable":
                send_telegram(
                    "Tickets available!\n"
                    f"{entry['name']}\n"
                    f"{when}\n"
                    f"{describe_prices(row)}\n"
                    f"{booking_url}"
                )

            state[key] = status

    save_json(STATE_PATH, state)


if __name__ == "__main__":
    main()
