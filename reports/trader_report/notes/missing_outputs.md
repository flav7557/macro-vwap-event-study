# Sorties Dérivées Manquantes

Au moment du nettoyage, le projet ne contenait pas les CSV de synthèse attendus ni les figures PNG du rapport trader.

Le notebook est construit pour charger les fichiers depuis `reports/trader_report/csv_outputs/` et `reports/trader_report/figures/`. Si ces fichiers manquent, il affiche des avertissements clairs au lieu de planter.

CSV attendus :

- `single_country_master_summary.csv`
- `single_country_all_configs_summary.csv`
- `single_country_random_tests.csv`
- `single_country_train_test.csv`
- `single_country_walk_forward.csv`

Une fois le backtest relancé, copier les CSV dérivés partageables dans `csv_outputs/` et les graphiques finaux sélectionnés dans `figures/`.
