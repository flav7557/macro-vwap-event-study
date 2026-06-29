# Read me first

This project is organized by research tests.

## How to read the project

1. Start with `research_tests/test_01_us_macro_vwap_screening/`
   This is the first broad US screening.

2. Then read `research_tests/test_02_train_test_validation/`
   This is the stricter validation step. It explains why some names are rejected even if their full-sample return is positive.

3. `research_tests/test_03_deep_dive_selected_assets/`
   This is the next step and is not completed yet.

## Current status

The project is currently at Test 02.

The cleanest current names are:

- SMTC
- VIAV

RVLV and SAM are still interesting but more fragile.

REAL and IRTC remain watchlist names, but the signal looks more VWAP-driven or less clearly macro-directional.

## Main warning

Most US macro releases are pre-market. So the current setup should be interpreted as:

```text
macro calendar day + VWAP intraday
```

not:

```text
pure minute-by-minute reaction to the exact macro release timestamp
```

## Where things are

- each test has its own scripts, notebooks, results, figures and notes
- shared data format information is in `shared/data_format/`
- old or unclear files are kept in `archive/`
