# Changelog

## V2 - Cleaner train/test validation

Date: 2026-06-30

Main change:

The model now makes the chronological train/test validation more explicit. It distinguishes between full-sample profitability and out-of-sample test performance.

Key findings from V2:

- A-class names: SMTC, VIAV
- B-class names: RVLV, SAM
- C / watchlist names: REAL, IRTC, LMB, PLAY, VSAT, BLFS, GPRO
- Rejected names: BOOT, ENVX, KOP, LMND, LUMN, VREX

Important point:

Several names had positive full-sample returns but were rejected because the rule selected on the training period lost money on the test period.

Main warning:

Most US macro releases are pre-market, so this should be interpreted as a "macro calendar day + VWAP intraday" framework, not a pure minute-by-minute reaction to macro releases.

## V1 - First US macro + VWAP screening

Date: 2026-06-29

Main change:

First broad US screening using macro surprise signal + VWAP execution.

Key purpose:

Identify which US stocks might show directional or contrarian behaviour around macro release days.
