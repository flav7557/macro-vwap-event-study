# V2 - Cleaner train/test validation

Ce dossier contient les sorties partageables du run V2.

Source locale :

```text
C:\Users\PC\Downloads\data\macro_vwap_single_country_results_20260630_000324
```

Contenu :

- `csv_outputs/` : CSV de synthese du backtest V2
- `figures/` : figures PNG regenerees depuis les CSV V2
- `notes/` : notes courtes sur le run V2

Point principal :

V2 rend la validation chronologique plus explicite. Un nom peut avoir un rendement full-sample positif et etre rejete si la regle selectionnee sur la periode train perd de l'argent sur la periode test.
