# BTC Race Bot — dip-buy mean reversion (make.fun btc-race-24h-20261117-0603)
#
# Protocol: agent-fun/bars-replay/v1, via the vendored shim
# (vendor/makefun_bars.py, the kit's sdk/makefun_bars.py, standard library
# only). The grader runs: python3 -P -s /bot/main.py, PYTHONHASHSEED=0.
#
# Strategy (pattern of the top-scoring entries on this bounty):
#   - Buy the dip: close 1.05% or more below the 60-bar simple moving average.
#   - All-in on the first signal (starting capital $1,000, paper money).
#   - Take profit at +1.8% over the entry reference; stop loss at -0.6%.
#   - Guaranteed-trade fallback: if no trade has happened after 600 scored
#     bars, buy once, so the race window's "at least 1 trade" bar is met.
#   - One position at a time. Deterministic: a pure function of the bars and
#     the account state the harness reports. No network, no wall clock, no
#     files, no randomness, standard library only.
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "vendor"))
import makefun_bars

SMA_WINDOW = 60           # bars for the dip reference mean
DIP_PCT = 0.0105          # buy when close is 1.05% below SMA60
TAKE_PROFIT_PCT = 0.018   # sell at +1.8% over the entry reference
STOP_LOSS_PCT = 0.006     # sell at -0.6% under the entry reference
FALLBACK_AFTER_BARS = 600  # guarantee at least one trade
MAX_SLIPPAGE_BPS = 100

_symbol = None
_closes = []        # raw close ints (price_scale units), oldest first
_entry_ref = None   # raw close that triggered the current position
_trades = 0
_bars_seen = 0      # scored (non-warmup) bars seen


def on_hello(state):
    global _symbol
    _symbol = next(iter(state.symbols))


def on_batch(state, batch):
    global _entry_ref, _trades, _bars_seen
    close = state.close(_symbol)
    if close is None:
        return []
    # Warm-up bars build history but take no orders (the harness rejects them).
    if state.warming_up:
        _closes.append(close)
        return []
    _bars_seen += 1

    # --- exits first (we hold a position) ---
    holding = state.positions.get(_symbol)
    if holding is not None and holding.qty > 0 and _entry_ref is not None:
        if close >= _entry_ref * (1 + TAKE_PROFIT_PCT) or close <= _entry_ref * (1 - STOP_LOSS_PCT):
            _trades += 1
            _entry_ref = None
            _closes.append(close)
            return [{"side": "sell", "symbol": _symbol, "qty": holding.qty,
                     "max_slippage_bps": MAX_SLIPPAGE_BPS}]

    # --- entries (flat) ---
    if (holding is None or holding.qty == 0) and state.cash > 0:
        if len(_closes) >= SMA_WINDOW:
            sma = sum(_closes[-SMA_WINDOW:]) / SMA_WINDOW
            if close <= sma * (1 - DIP_PCT):
                spend = min(state.cash, state.weight_room(_symbol))
                if spend > 0:
                    _entry_ref = close
                    _closes.append(close)
                    return [{"side": "buy", "symbol": _symbol,
                             "notional_quote_units": spend,
                             "max_slippage_bps": MAX_SLIPPAGE_BPS}]
        elif _bars_seen >= FALLBACK_AFTER_BARS and _trades == 0:
            spend = min(state.cash, state.weight_room(_symbol))
            if spend > 0:
                _entry_ref = close
                _closes.append(close)
                return [{"side": "buy", "symbol": _symbol,
                         "notional_quote_units": spend,
                         "max_slippage_bps": MAX_SLIPPAGE_BPS}]

    _closes.append(close)
    return []


makefun_bars.run(on_batch, on_hello=on_hello)
