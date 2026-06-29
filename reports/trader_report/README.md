# Trader Report Outputs

This folder is for the selected derived outputs used by the notebook.

Expected layout:

```text
reports/trader_report/
|-- figures/
|   `-- selected PNG charts
|-- csv_outputs/
|   |-- single_country_master_summary.csv
|   |-- single_country_all_configs_summary.csv
|   |-- single_country_random_tests.csv
|   |-- single_country_train_test.csv
|   `-- single_country_walk_forward.csv
`-- notes/
    `-- short notes about missing files or manual choices
```

Only derived summary CSVs and final PNGs should go here. Raw price files and the macro workbook should stay out of the repo.
