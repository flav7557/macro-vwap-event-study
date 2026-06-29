# Test 01 - US macro + VWAP screening

## What we are doing here

This first test screens a basket of US stocks using a macro surprise signal and a VWAP execution filter.

The goal is not to prove a tradable strategy yet. The goal is to see whether some stocks behave better in DRIFT, some in FADE, and whether VWAP helps the entry.

## What this test produced

This test produced:

- classification of assets into clean / suspicious / rejected
- top candidate assets
- first robustness checks
- first charts for the trader

## Main takeaway

The first version found several interesting names, but it also showed that some results might be VWAP-driven or too dependent on the full sample.

## Main limitation

Most US macro releases are pre-market, so this is better described as macro calendar day + VWAP intraday, not pure minute-by-minute reaction to macro releases.

## Folder contents

- `scripts/` contains the first screening script
- `notebooks/` contains the first readable research summary
- `results/csv_outputs/` contains the V1 summary CSVs
- `results/figures/` contains the V1 trader figures
- `notes/` contains short notes from the first report
