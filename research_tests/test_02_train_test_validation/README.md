# Test 02 - Cleaner train/test validation

## What we are doing here

In Test 01, some stocks looked profitable on the full sample. In Test 02, we check whether the rule selected on the earlier part of the data still works on the later test period.

The idea is simple:

- select the best rule on the training period
- apply the same rule on the test period
- reject the asset if it loses money on the test period

## What changed vs Test 01

Test 02 makes the validation stricter.

A stock can now be rejected even if its full-sample return is positive, because what matters is whether the rule works out-of-sample.

## Main current result

The cleanest names from Test 02 are:

- SMTC
- VIAV

Interesting but more fragile:

- RVLV
- SAM

Watchlist / more VWAP-driven:

- REAL
- IRTC
- LMB
- PLAY
- VSAT

Rejected despite positive full-sample returns:

- BOOT
- ENVX
- KOP
- LMND
- LUMN
- VREX

## Why some profitable names are rejected

These names are not rejected because they never made money. They are rejected because the full-sample result looked positive, but the rule selected on the train period lost money on the test period.

This is a warning that the result may be overfit or regime-dependent.

## Folder contents

- `scripts/` contains the note about the V2 script status
- `notebooks/` contains the V2 train/test notebook
- `results/csv_outputs/` contains the latest V2 summary CSVs
- `results/figures/` contains V2 figures
- `notes/` contains notes about the V2 outputs and known naming issues
