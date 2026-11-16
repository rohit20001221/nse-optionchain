import math


def _bs_gamma(
    spot: float, strike: float, t: float, r: float, iv_percent: float | None
) -> float:
    """
    Calculates Black-Scholes Gamma using only Python's standard math library.
    iv_percent is expected as a percentage (e.g., 16.5 for 16.5% IV).
    """
    if iv_percent is None or iv_percent <= 0 or t <= 0 or spot <= 0 or strike <= 0:
        return 0.0

    sigma = iv_percent / 100.0
    sqrt_t = math.sqrt(t)

    d1 = (math.log(spot / strike) + (r + 0.5 * sigma**2) * t) / (sigma * sqrt_t)

    # Standard normal probability density function N'(d1)
    n_prime_d1 = math.exp(-0.5 * d1**2) / math.sqrt(2.0 * math.pi)

    return n_prime_d1 / (spot * sigma * sqrt_t)


def calculate_gex(
    option_chain: list[dict],
    spot_price: float,
    days_to_expiry: float,
    lot_size: int = 1,
    risk_free_rate: float = 0.07,
) -> dict:
    """
    Calculates Gamma Exposure (GEX) per strike and total net GEX from the parsed option chain.

    Args:
        option_chain: Output list from option_chain_csv_to_json().
        spot_price: Current underlying index/stock price (e.g., 24500.0).
        days_to_expiry: Calendar days remaining until expiry (e.g., 3.5).
        lot_size: Contract multiplier (e.g., 75 for NIFTY, 30 for BANKNIFTY, 1 for raw units).
        risk_free_rate: Annualized risk-free rate as a decimal (default 0.07 for ~7% RBI/T-bill rate).

    Returns:
        Dictionary containing total_net_gex, zero_gamma_strike (nearest flip level), and per-strike breakdown.
    """
    t = (
        max(days_to_expiry, 1e-6) / 365.0
    )  # Convert days to years; avoid division by zero on expiry day
    strike_breakdown = []
    total_call_gex = 0.0
    total_put_gex = 0.0

    for row in option_chain:
        strike = row.get("strike")
        if strike is None:
            continue

        calls = row.get("calls", {})
        puts = row.get("puts", {})

        call_oi = calls.get("oi") or 0
        put_oi = puts.get("oi") or 0

        call_gamma = _bs_gamma(spot_price, strike, t, risk_free_rate, calls.get("iv"))
        put_gamma = _bs_gamma(spot_price, strike, t, risk_free_rate, puts.get("iv"))

        # Dollar/Rupee GEX per 1% move in the underlying
        call_gex = call_oi * call_gamma * (spot_price**2) * 0.01 * lot_size
        put_gex = -1.0 * put_oi * put_gamma * (spot_price**2) * 0.01 * lot_size
        net_gex = call_gex + put_gex

        total_call_gex += call_gex
        total_put_gex += put_gex

        strike_breakdown.append(
            {
                "strike": strike,
                "call_gamma": round(call_gamma, 6),
                "put_gamma": round(put_gamma, 6),
                "call_gex": round(call_gex, 2),
                "put_gex": round(put_gex, 2),
                "net_gex": round(net_gex, 2),
            }
        )

    # Find the strike closest to the zero-gamma flip point (where net_gex crosses 0)
    zero_gamma_strike = None
    for i in range(len(strike_breakdown) - 1):
        g1 = strike_breakdown[i]["net_gex"]
        g2 = strike_breakdown[i + 1]["net_gex"]
        if (g1 <= 0 <= g2) or (g1 >= 0 >= g2):
            # Pick whichever of the two adjacent strikes is closer to 0
            zero_gamma_strike = (
                strike_breakdown[i]["strike"]
                if abs(g1) < abs(g2)
                else strike_breakdown[i + 1]["strike"]
            )
            break

    return {
        "spot_price": spot_price,
        "total_call_gex": round(total_call_gex, 2),
        "total_put_gex": round(total_put_gex, 2),
        "total_net_gex": round(total_call_gex + total_put_gex, 2),
        "zero_gamma_strike": zero_gamma_strike,
        "strikes": strike_breakdown,
    }
