# Missing Derived Outputs

At cleanup time, the project did not contain the expected generated summary CSVs or PNG report figures.

The notebook is built to load files from `reports/trader_report/csv_outputs/` and `reports/trader_report/figures/`. If those files are missing, it prints clear warnings instead of crashing.

Expected CSV files:

- `single_country_master_summary.csv`
- `single_country_all_configs_summary.csv`
- `single_country_random_tests.csv`
- `single_country_train_test.csv`
- `single_country_walk_forward.csv`

Once the backtest has been run, copy the safe derived CSVs into `csv_outputs/` and any selected final charts into `figures/`.
