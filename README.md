# Uniqlo Price Tracker

Checks the price of Uniqlo product pages once a day and sends you a Telegram
message when a price changes. Runs for free on GitHub Actions — no server to
maintain.

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
