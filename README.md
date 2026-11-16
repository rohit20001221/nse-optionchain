# NIFTY Live GEX — Real-Time Dealer Positioning & Gamma Analytics

**See where market makers are forced to buy and sell—tick by tick.**

NIFTY Live GEX transforms raw NSE option chain activity into an institutional-grade, real-time view of market maker Gamma Exposure (GEX). Instead of manually scanning static option tables, traders get an instant visual map of key support/resistance walls, volatility regimes, and intraday inflection points as the market moves.

---

## Why Gamma Exposure Matters

Every option contract traded creates a hedging obligation for market makers. Depending on where Open Interest and Implied Volatility cluster, dealer hedging either absorbs market volatility or accelerates breakouts:

- **Positive Gamma Regimes (`+GEX`):** Dealers hedge against price movement—buying dips and selling rallies. Markets tend to consolidate, pin near major strikes, and experience lower intraday volatility.
- **Negative Gamma Regimes (`-GEX`):** Dealers hedge in the direction of momentum—selling into weakness and buying into strength. Breakouts accelerate and intraday swings expand.
- **Zero Gamma Flip:** The exact strike threshold where market behavior transitions from mean-reverting stability to momentum-driven expansion.

---

## Key Capabilities

### 1. Live Tick-by-Tick Option Chain Intelligence

Connects directly to live NSE option chain updates, recalculating dealer exposure automatically on every incoming market tick with zero manual refreshing.

### 2. Visual Strike-by-Strike GEX Profile

A clean, high-contrast vertical distribution centered around the At-The-Money (ATM) strike ($\pm 15$ strikes) immediately highlights:

- **Call & Put Gamma Walls:** Heavy strike concentrations that act as natural intraday magnets or barriers.
- **Net Positioning Balance:** Solid black bars for net positive gamma support versus light grey bars for net negative gamma acceleration zones.

### 3. Essential Market Metrics at a Glance

- **NIFTY Spot & Expiry Countdown:** Live underlying index price paired with precision time-to-expiry modeling down to the 3:30 PM IST closing bell.
- **Total Net GEX:** Instant read on whether aggregate dealer positioning favors range-bound stability or directional volatility.
- **Zero Gamma Flip Level:** Identifies the critical pivot strike separating calm and volatile market regimes.
- **Granular Strike Breakdown:** Side-by-side Call GEX, Put GEX, and Net GEX figures for every strike around spot price.

### 4. Distraction-Free Monochrome Workspace

Designed with a crisp, high-contrast black-and-white interface built for active trading screens—eliminating visual clutter so critical levels stand out immediately during fast-moving sessions.

---

## Who It Is For

- **Intraday Index Traders** looking to anticipate pinning behavior, range boundaries, and breakout acceleration zones on NIFTY 50.
- **Options Sellers & Hedgers** identifying high-gamma strikes where price action is likely to stall or revert.
- **Quantitative & Discretionary Analysts** monitoring real-time shifts in dealer exposure throughout the trading day.

---

## Quick Launch

1. **Install the required packages:**

```bash
 pip install playwright websockets && playwright install firefox
```

2. **Launch the live feed:**

```bash
python server.py
```

3. **Open workspace**

```bash
http://localhost:3001
```
