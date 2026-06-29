# Sorties Du Rapport Trader

Ce dossier sert à stocker les sorties dérivées utilisées par le notebook.

Les fichiers actuellement présents correspondent à la V1 du backtest :

```text
macro_vwap_single_country_results_20260629_225714
```

Ce sont des résultats dérivés, pas les fichiers de prix bruts.

Structure attendue :

```text
reports/trader_report/
|-- figures/
|   `-- graphiques PNG retenus
|-- csv_outputs/
|   |-- single_country_master_summary.csv
|   |-- single_country_all_configs_summary.csv
|   |-- single_country_random_tests.csv
|   |-- single_country_train_test.csv
|   `-- single_country_walk_forward.csv
`-- notes/
    `-- notes courtes sur les fichiers manquants ou les choix manuels
```

Seuls les CSV de synthèse et les PNG finaux doivent aller ici. Les fichiers de prix bruts et le fichier macro doivent rester hors du repo.
