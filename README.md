# Macro Surprise + VWAP Execution

This repo is my first US equity screening around macro surprise days and VWAP-based intraday execution.

The question is simple: when an important US macro number comes out stronger or weaker than expected, do some individual stocks show short-term patterns that can be captured with a disciplined VWAP entry rule?

I do not want to present this as a finished trading strategy. It is a research backtest with a few robustness checks. The useful part is not only which names look good, but also which names look fragile once I force the rule to survive random tests, costs, and a chronological train/test split.

## Repository Structure

```text
macro-vwap-event-study/
|-- README.md
|-- requirements.txt
|-- .gitignore
|-- scripts/
|   |-- macro_event_backtester_single_country_20stocks.py
|   `-- macro_event_backtester_single_country_20stocks_trader_graphs.py
|-- notebooks/
|   `-- 01_macro_vwap_research_summary.ipynb
|-- reports/
|   `-- trader_report/
|       |-- figures/
|       |-- csv_outputs/
|       `-- notes/
`-- data/
    `-- README.md
```

The Python scripts are the engine. The notebook is the readable research summary for review.

## What The Backtest Does

For each macro release, the script compares the actual number with the market estimate:

```text
surprise_raw = actual - estimate
surprise_z = (surprise_raw - historical_average_surprise) / historical_surprise_std
signal = surprise_z * direction
```

`direction` is `+1` when a higher macro value is treated as good, and `-1` when a lower value is treated as good. Events marked as mixed are excluded.

The model then tests two broad ideas:

- `DRIFT`: trade in the direction of the macro signal.
- `FADE`: trade against the macro signal.

VWAP is used as an execution filter. For longs, the model prefers entries below or close to VWAP. For shorts, it prefers entries above or close to VWAP. If the price is not favorable, the model waits for a return toward VWAP inside a fixed window.

One important limitation: many US macro releases happen before the US equity open. So this should be read more as "macro calendar day + VWAP intraday" than as a pure minute-by-minute reaction to the release timestamp.

## Robustness Checks

The engine tries not to keep a stock only because the full backtest looks profitable. It checks:

- random side test
- random timestamp test
- time-shift placebo
- transaction cost sweep
- chronological train/test split
- walk-forward by year

The train/test split matters a lot. The rule is selected on the first 70% of the period, then tested on the final 30%. If a rule looks good in the full sample but loses money on the later test period, I treat it as rejected or at least fragile.

## How To Run

Install the Python dependencies:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Run the backtest engine:

```bash
python scripts/macro_event_backtester_single_country_20stocks.py
```

The script asks for the macro workbook, the country, and the stock minute CSV files. It writes a timestamped results folder with files such as:

- `single_country_master_summary.csv`
- `single_country_all_configs_summary.csv`
- `single_country_random_tests.csv`
- `single_country_train_test.csv`
- `single_country_walk_forward.csv`

After that, copy the selected final CSVs into:

```text
reports/trader_report/csv_outputs/
```

If graph outputs are available, put the selected PNG files into:

```text
reports/trader_report/figures/
```

Then open:

```text
notebooks/01_macro_vwap_research_summary.ipynb
```

The notebook reads the saved CSVs and figures. It is not meant to re-run the full backtest.

## Data

Raw data is not included in the repo.

Expected inputs are:

- one macro workbook with actual, estimate, previous, and historical surprise metrics
- one minute-level OHLCV CSV per stock

See `data/README.md` for the expected format.

## Current Caveats

- The current US setup has many `PRE_OPEN_SAME_DAY` entries, so the timing interpretation needs to be honest.
- `close_cross` VWAP entries are easier to fill and can be optimistic.
- `limit_touch` is more conservative and should be tested more deeply.
- Full-sample profitability is not enough. The train/test and random tests are used to reject names that look overfit.
- Duplicate or messy source filenames can create ticker presentation issues. The notebook flags these instead of hiding them.

This is research work, not investment advice.
