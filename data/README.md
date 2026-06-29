# Donnees D'entree

Aucune donnee brute n'est commit dans ce repo. Ce dossier documente seulement le format attendu par le moteur de backtest.

Pour ce premier screening, j'ai teste les actions avec environ 10 ans de donnees en timeframe 1 minute. Les fichiers minute sont lourds, donc je ne les ai pas ajoutes au repo GitHub. En plus, je prefere eviter de publier les fichiers bruts directement.

Si tu lis ce projet et que tu veux les fichiers exacts utilises pour reproduire le test, envoie-moi un message et je peux te les transmettre par mail.

Le moteur a besoin de deux types d'entrees :

- un fichier macro avec les publications et les metriques historiques de surprise
- un CSV OHLCV minute par action

## Fichier Macro

Le fichier peut etre en `.xlsx` ou `.ods`. Il doit contenir deux feuilles.

### `data`

Une ligne par publication macro.

Colonnes utiles :

| colonne | signification |
| --- | --- |
| `event_date` | timestamp de publication, idealement avec timezone |
| `country` | code pays, par exemple `US` |
| `event` | nom de l'evenement macro |
| `estimate` | consensus |
| `actual` | valeur publiee |
| `previous` | valeur precedente, si disponible |

### `METRIQ_FINISH`

Une ligne par type d'evenement macro, avec les metriques historiques.

Colonnes utiles :

| colonne | signification |
| --- | --- |
| `Country` | code pays |
| `events` | nom de l'evenement |
| `macro_family` | famille de l'evenement |
| `higher_is_good` | `YES`, `NO` ou `MIXED` |
| `event_importance_guess` | score approximatif d'importance |
| `valid_obs_count` | nombre d'observations utilisees |
| `surprise_avg_10y` | surprise moyenne historique |
| `surprise_std_10y` | ecart-type historique des surprises |
| `beat_rate_10y` | part des publications au-dessus du consensus |

Le z-score est vraiment propre seulement si la moyenne et l'ecart-type historiques sont calcules avant la periode testee. S'ils sont calcules sur la meme periode que le backtest, le resultat peut etre trop optimiste.

## CSV De Prix Minute

Utiliser un CSV par action.

Colonnes attendues :

```text
timestamp,open,high,low,close,volume
2016-11-16 14:31:00+00,14.88,14.92,14.88,14.92,200
```

Notes :

- les timestamps devraient etre en UTC si possible
- les donnees peuvent etre clairsemees pour des actions peu liquides
- le VWAP est calcule en intraday et remis a zero chaque jour
- le ticker est generalement extrait du nom du fichier

Exemples de noms de fichiers :

```text
lmb_dataset.csv
irtc_dataset.csv
sam_dataset.csv
```

Le dossier local actuel contient des CSV bruts dans `US-Actions/`, mais ce dossier est ignore pour eviter de le publier par erreur.
