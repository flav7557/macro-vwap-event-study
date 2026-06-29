# Données D'entrée

Aucune donnée brute n'est commit dans ce repo. Ce dossier documente seulement le format attendu par le moteur de backtest.

Pour ce premier screening, j'ai testé les actions avec environ 10 ans de données en timeframe 1 minute. Les fichiers minute sont lourds, donc je ne les ai pas ajoutés au repo GitHub. En plus, je préfère éviter de publier les fichiers bruts directement.

Si tu lis ce projet et que tu veux les fichiers exacts utilisés pour reproduire le test, envoie-moi un message et je peux te les transmettre par mail.

Le moteur a besoin de deux types d'entrées :

- un fichier macro avec les publications et les métriques historiques de surprise
- un CSV OHLCV minute par action

## Fichier Macro

Le fichier peut être en `.xlsx` ou `.ods`. Il doit contenir deux feuilles.

### `data`

Une ligne par publication macro.

Colonnes utiles :

| colonne | signification |
| --- | --- |
| `event_date` | timestamp de publication, idéalement avec timezone |
| `country` | code pays, par exemple `US` |
| `event` | nom de l'événement macro |
| `estimate` | consensus |
| `actual` | valeur publiée |
| `previous` | valeur précédente, si disponible |

### `METRIQ_FINISH`

Une ligne par type d'événement macro, avec les métriques historiques.

Colonnes utiles :

| colonne | signification |
| --- | --- |
| `Country` | code pays |
| `events` | nom de l'événement |
| `macro_family` | famille de l'événement |
| `higher_is_good` | `YES`, `NO` ou `MIXED` |
| `event_importance_guess` | score approximatif d'importance |
| `valid_obs_count` | nombre d'observations utilisées |
| `surprise_avg_10y` | surprise moyenne historique |
| `surprise_std_10y` | écart-type historique des surprises |
| `beat_rate_10y` | part des publications au-dessus du consensus |

Le z-score est vraiment propre seulement si la moyenne et l'écart-type historiques sont calculés avant la période testée. S'ils sont calculés sur la même période que le backtest, le résultat peut être trop optimiste.

## CSV De Prix Minute

Utiliser un CSV par action.

Colonnes attendues :

```text
timestamp,open,high,low,close,volume
2016-11-16 14:31:00+00,14.88,14.92,14.88,14.92,200
```

Notes :

- les timestamps devraient être en UTC si possible
- les données peuvent être clairsemées pour des actions peu liquides
- le VWAP est calculé en intraday et remis à zéro chaque jour
- le ticker est généralement extrait du nom du fichier

Exemples de noms de fichiers :

```text
lmb_dataset.csv
irtc_dataset.csv
sam_dataset.csv
```

Le dossier local actuel contient des CSV bruts dans `US-Actions/`, mais ce dossier est ignoré pour éviter de le publier par erreur.
