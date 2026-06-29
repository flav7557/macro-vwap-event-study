# Project status

## Current stage

V2 - Cleaner train/test validation completed.

## What has been tested so far

- US macro releases
- Around 18 US small/mid-cap equities
- DRIFT and FADE directions
- VWAP execution filters
- random side tests
- random timestamp tests
- cost sweep
- chronological train/test
- walk-forward by year

## Current interpretation

The framework does not simply select the stocks with the highest full-period return. It keeps names that survive robustness checks.

In the stricter V2, SMTC and VIAV are the cleanest candidates. RVLV and SAM remain interesting but are now classified as more fragile. REAL and IRTC remain watchlist names, but the signal appears more VWAP-driven or less clearly macro-directional.

## Main limitation

The main limitation is that US macro releases are often pre-market. Therefore, the current framework should be interpreted as macro calendar day + VWAP intraday, not as a pure intraday reaction to the exact release timestamp.

## Next steps

V3 should deep dive on the strongest candidates:

- SMTC
- VIAV
- RVLV
- SAM
- REAL
- IRTC

Potential V3 tests:

- increase random simulations to 500
- compare close_cross vs limit_touch more carefully
- inspect performance by year
- inspect top macro event types
- inspect DRIFT vs FADE by asset
- check whether the edge comes from macro direction, VWAP execution, or both
