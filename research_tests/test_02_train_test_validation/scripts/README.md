# Note sur le script V2

Le script Python exact utilise pour generer le run V2 n'etait pas present dans les fichiers locaux recus.

Les sorties V2 sont incluses ici :

```text
research_tests/test_02_train_test_validation/results/
```

Le changement principal de V2 est visible dans les colonnes de sortie :

- `selected_on_train_*`
- `train_ret_moy_pct`
- `test_ret_moy_pct`
- `test_status`
- `train_test_explanation`

Si je retrouve le moteur exact V2, il faudra l'ajouter dans ce dossier sous le nom :

```text
macro_event_backtester_single_country_20stocks_train_test_clean.py
```
