import json
import re
import sys
from pathlib import Path

import requests

from notify import load_json, save_json, send_telegram

ROOT = Path(__file__).parent
WATCHLIST_PATH = ROOT / "watchlist.json"
STATE_PATH = ROOT / "state.json"

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; UniqloPriceTracker/1.0)"}
PRELOADED_STATE_RE = re.compile(r"window\.__PRELOADED_STATE__\s*=\s*(.*?)</script>", re.S)
PRODUCT_PATH_RE = re.compile(r"/products/([A-Z0-9-]+)/(\d+)")

def fetch_product(url):
    match = PRODUCT_PATH_RE.search(url)
    if not match:
        raise ValueError(f"Could not find a product id in URL: {url}")
    product_id, price_group = match.groups()
    product_key = f"{product_id}-{price_group}"

    response = requests.get(url, headers=HEADERS, timeout=30)
    response.raise_for_status()
    response.encoding = "utf-8"

    state_match = PRELOADED_STATE_RE.search(response.text)
    if not state_match:
        raise ValueError(f"Could not find __PRELOADED_STATE__ on page: {url}")

    preloaded_state = json.loads(state_match.group(1))
    entity = preloaded_state.get("entity", {}).get("pdpEntity", {}).get(product_key)
    if not entity:
        raise ValueError(f"No product entity found for {product_key}: {url}")

    product = entity["product"]
    prices = product["prices"]
    promo = prices.get("promo")
    price = promo["value"] if promo else prices["base"]["value"]

    return {
        "name": product.get("name", product_key),
        "price": price,
        "currency": prices["base"]["currency"]["symbol"],
    }


def main():
    watchlist = load_json(WATCHLIST_PATH, [])
    state = load_json(STATE_PATH, {})

    for url in watchlist:
        try:
            product = fetch_product(url)
        except Exception as exc:
            print(f"[error] {url}: {exc}", file=sys.stderr)
            continue

        previous = state.get(url)
        price, currency, name = product["price"], product["currency"], product["name"]
        print(f"[ok] {name}: {price}{currency}")

        if previous is None:
            send_telegram(f"Tracking started: {name}\n{price}{currency}\n{url}")
        elif previous["price"] != price:
            send_telegram(
                f"Price change: {name}\n{previous['price']}{currency} -> {price}{currency}\n{url}"
            )

        state[url] = {"name": name, "price": price, "currency": currency}

    save_json(STATE_PATH, state)


if __name__ == "__main__":
    main()
