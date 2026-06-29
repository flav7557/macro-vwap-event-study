# Data Inputs

No raw data is committed to this repo. This folder only documents the input format expected by the backtest engine.

The engine needs two types of input:

- a macro workbook with release data and historical surprise metrics
- one minute-level OHLCV CSV per stock

## Macro Workbook

The workbook can be `.xlsx` or `.ods`. It should contain two sheets.

### `data`

One row per macro release.

Useful columns:

| column | meaning |
| --- | --- |
| `event_date` | release timestamp, ideally timezone-aware |
| `country` | country code, for example `US` |
| `event` | macro event name |
| `estimate` | consensus estimate |
| `actual` | released value |
| `previous` | previous value, if available |

### `METRIQ_FINISH`

One row per macro event type with historical surprise metrics.

Useful columns:

| column | meaning |
| --- | --- |
| `Country` | country code |
| `events` | event name |
| `macro_family` | event group |
| `higher_is_good` | `YES`, `NO`, or `MIXED` |
| `event_importance_guess` | rough importance score |
| `valid_obs_count` | number of observations used for the metrics |
| `surprise_avg_10y` | historical average surprise |
| `surprise_std_10y` | historical surprise standard deviation |
| `beat_rate_10y` | share of releases beating consensus |

The z-score is only clean if the historical average and standard deviation are computed before the tested period. If they are calculated using the same period as the backtest, the result can be too optimistic.

## Minute Price CSV

Use one CSV per stock.

Expected columns:

```text
timestamp,open,high,low,close,volume
2016-11-16 14:31:00+00,14.88,14.92,14.88,14.92,200
```

Notes:

- timestamps should be in UTC if possible
- the data can be sparse for illiquid names
- VWAP is computed intraday and reset each day
- the ticker is usually inferred from the filename

Example filenames:

```text
lmb_dataset.csv
irtc_dataset.csv
sam_dataset.csv
```

The current local folder contains raw CSVs under `US-Actions/`, but that folder is ignored so it is not accidentally committed.
