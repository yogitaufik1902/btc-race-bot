# BTC Race Bot

Entry for make.fun bounty **"Race a BTC trading bot live for 24 hours"**
(`btc-race-24h-20261117-0603`). Simulation only: the bot trades paper money
against real on-chain cbBTC prices; no real money is traded.

## Strategy

Dip-buy mean reversion, the pattern of the top-scoring entries on this bounty:

- **Buy the dip:** close 1.05% or more below the 60-bar simple moving average.
- **All-in** on the first signal (starting capital $1,000).
- **Take profit** at +1.8% over the entry reference; **stop loss** at −0.6%.
- **Guaranteed-trade fallback:** if no trade has happened after 600 bars, buy
  once, so the race window's "at least 1 trade" bar is met.
- One position at a time. Deterministic: a pure function of the bars — no
  network, no wall clock, no files, no randomness, standard library only.

## Run

The harness feeds one JSON line per minute (1-minute bar of cbBTC in USD) on
stdin; the bot answers with one JSON order line per bar on stdout.

```sh
python3 main.py < bars.jsonl
```

## License

MIT. See `LICENSE`.
