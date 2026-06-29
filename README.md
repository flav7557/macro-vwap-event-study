# Macro VWAP Event Study

This repo is my research project on US macro surprise days and VWAP-based intraday execution.

The goal is not to claim that the strategy is ready to trade. The goal is to document the research step by step, so a trader can see what was tested, what improved, and why some names are selected or rejected.

Start here:

```text
READ_ME_FIRST.md
```

## How the repo is organized

The repo is organized by research test, not only by file type.

```text
research_tests/
|-- test_01_us_macro_vwap_screening/
|-- test_02_train_test_validation/
`-- test_03_deep_dive_selected_assets/
```

Each test folder contains its own:

- scripts
- notebooks
- results
- figures
- notes

## What each test means

### Test 01 - US macro + VWAP screening

This was the first broad screening.

It tested whether US macro surprise days, combined with VWAP execution, could identify interesting short-term patterns across selected US equities.

Folder:

```text
research_tests/test_01_us_macro_vwap_screening/
```

### Test 02 - Cleaner train/test validation

This is the current completed stage.

It checks whether the rule selected on the earlier part of the data still works on the later test period. This is important because a full-sample backtest can look good while the train-selected rule fails out-of-sample.

Folder:

```text
research_tests/test_02_train_test_validation/
```

### Test 03 - Deep dive on selected assets

This is the next planned stage.

It will focus only on the strongest or most interesting names from Test 02.

Folder:

```text
research_tests/test_03_deep_dive_selected_assets/
```

## Current results

Current cleanest names from Test 02:

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

## Data

Raw minute data is not included in the repo.

For this study I used around 10 years of 1-minute stock data. The files are heavy and are not uploaded here. If someone needs the exact raw files, I can send them by mail.

The expected data format is explained here:

```text
shared/data_format/README.md
```

## Main warning

Most US macro releases are pre-market.

So this should be interpreted as:

```text
macro calendar day + VWAP intraday
```

not as a pure minute-by-minute reaction to the release timestamp.
