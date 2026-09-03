# Watchers

Two Telegram watchers running for free on GitHub Actions — no server to
maintain:

- **Uniqlo price tracker** — daily; alerts when a product's price changes.
- **[Opéra de Paris ticket tracker](#opéra-de-paris-ticket-tracker)** — every
  15 minutes; alerts when a sold-out performance becomes bookable.

Both share the same Telegram bot credentials (`TELEGRAM_BOT_TOKEN` and
`TELEGRAM_CHAT_ID` repo secrets) and the same helper module, `notify.py`.

# Uniqlo Price Tracker

Checks the price of Uniqlo product pages once a day and sends you a Telegram
message when a price changes.

## How it works

Uniqlo product pages embed the product data (including price) directly in
the page HTML as `window.__PRELOADED_STATE__`. `check_prices.py` fetches each
URL in `watchlist.json`, pulls the price out of that embedded data, compares
it to the last known price stored in `state.json`, and sends a Telegram
message if it changed (or the first time an item is tracked). The workflow
then commits the updated `state.json` back to the repo.

## One-time setup

### 1. Create the Telegram bot

1. In Telegram, message [@BotFather](https://t.me/BotFather) and send
   `/newbot`. Follow the prompts and copy the **bot token** it gives you.
2. Send your new bot any message (e.g. "hi") so it can see your chat.
3. Visit `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates` in a browser
   and find `"chat":{"id": ...}` in the response — that number is your
   **chat ID**.

### 2. Push this repo to GitHub

Create a new (private is fine) GitHub repo and push this folder to it.

### 3. Add repo secrets

In the GitHub repo: **Settings → Secrets and variables → Actions → New
repository secret**. Add:

- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`

### 4. Enable the workflow

Go to the **Actions** tab and enable workflows if prompted. The
`Check Uniqlo prices` workflow runs daily at 08:00 UTC. You can also trigger
it manually from the Actions tab (**Run workflow**) to test it right away.

## Adding products to watch

Edit `watchlist.json` and add the product page URL, e.g.:

```json
[
  "https://www.uniqlo.com/fr/fr/products/E471808-000/00?colorDisplayCode=78&sizeDisplayCode=004"
]
```

Commit and push. The next scheduled (or manually triggered) run will pick it
up and send a "tracking started" message with the current price.

## Changing the schedule

Edit the `cron` line in `.github/workflows/check-prices.yml`
(`0 8 * * *` = 08:00 UTC daily). Cron times on GitHub Actions are always UTC.

## Local testing

```bash
pip install -r requirements.txt
TELEGRAM_BOT_TOKEN=... TELEGRAM_CHAT_ID=... python check_prices.py
```

Without the environment variables set, the script still runs and prints
notifications to the console instead of sending them.

## Known limitation

Price is read from the product's base/promo price, which is shared across
sizes and colors for virtually all Uniqlo products. A small number of
products price certain sizes differently (`isDualPrice`); this tracker does
not account for that and would report the base price in that case.

---

# Opéra de Paris ticket tracker

Watches specific performances at the Opéra national de Paris and sends a
Telegram message the moment a sold-out performance opens for booking.

## How it works

Each show page has a JSON fragment endpoint listing every performance, e.g.
`.../lhistoire-de-manon/performances`. Each performance row carries an
`actions` list whose `type` encodes availability:

| `type` | Meaning on the site |
|---|---|
| `alert` | Sold out — the button reads "Créer une alerte" |
| `CTABook` | **Bookable** — the button reads "Réserver" |
| `CTAOption` | Resale only (bourse aux billets) |

`check_tickets.py` fetches that endpoint for each entry in
`tickets_watchlist.json`, looks up the performances by `perfId`, and sends a
Telegram message when one flips to `CTABook`. The last seen status per
performance is stored in `tickets_state.json` (committed back by the workflow),
so you get exactly one alert per transition rather than one every run.

Resale (`CTAOption`) is deliberately **not** treated as bookable. To alert on
resale too, add `"CTAOption"` handling in `find_booking_url`.

## Adding a performance to watch

1. Open the show's performances endpoint in a browser — it's the show URL with
   `/performances` appended, e.g.
   `https://www.operadeparis.fr/saison-26-27/ballet/lhistoire-de-manon/performances`
2. Find the performance you want in `body.rows` and note its `perfId`.
3. Add it to `tickets_watchlist.json`:

```json
[
  {
    "name": "L'Histoire de Manon — Palais Garnier",
    "url": "https://www.operadeparis.fr/saison-26-27/ballet/lhistoire-de-manon/performances",
    "page": "https://www.operadeparis.fr/saison-26-27/ballet/lhistoire-de-manon",
    "perf_ids": [8836]
  }
]
```

`perf_ids` takes several ids if you'd accept any of a set of dates.

## Schedule

`*/15 * * * *` in [.github/workflows/check-tickets.yml](.github/workflows/check-tickets.yml).
GitHub bills Actions per run rounded up to the minute, so a 15-minute schedule
needs a **public** repo (public repos get unlimited free Actions minutes).
If you make the repo private, drop to `*/30` or slower to stay inside the
2000 min/month free tier.

GitHub also throttles and delays scheduled workflows under load, so treat the
interval as best-effort — runs can drift by several minutes.

## Local testing

```bash
pip install -r requirements.txt
TELEGRAM_BOT_TOKEN=... TELEGRAM_CHAT_ID=... python check_tickets.py

# send a test message to confirm Telegram delivery
TELEGRAM_BOT_TOKEN=... TELEGRAM_CHAT_ID=... python check_tickets.py --test
```

Without the environment variables set, notifications print to the console
instead of being sent.
