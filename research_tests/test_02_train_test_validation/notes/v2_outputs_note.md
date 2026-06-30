# Sorties V2 incluses

Les resultats V2 ont ete ajoutes depuis :

```text
C:\Users\PC\Downloads\data\macro_vwap_single_country_results_20260630_000324
```

Les cinq CSV attendus etaient presents :

- `single_country_master_summary.csv`
- `single_country_all_configs_summary.csv`
- `single_country_random_tests.csv`
- `single_country_train_test.csv`
- `single_country_walk_forward.csv`

Aucun dossier de figures V2 n'etait present dans le dossier source. Les figures V2 ont donc ete regenerees depuis les CSV de synthese.

Notes de qualite :

- `LONDON-STRATEGIC-EDGE` vient du fichier `lmb_dataset_London-Strategic-Edge.csv`, donc les notebooks l'affichent visuellement comme LMB.
- IRTC apparait deux fois dans le master summary. Ce doublon est signale dans les notebooks et doit etre nettoye avant un run final.
