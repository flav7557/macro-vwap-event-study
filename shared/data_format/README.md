# Donnees d'entree

Aucune donnee brute n'est commit dans ce repo. Ce dossier sert seulement a expliquer le format attendu par le moteur de backtest.

Pour ce premier travail, j'ai utilise environ 10 ans de donnees en timeframe 1 minute. Les fichiers minute sont lourds et je n'arrive pas a les charger proprement ici. Si tu lis ce repo et que tu veux les fichiers exacts, je peux te les envoyer par mail.

## Fichier macro

Le fichier macro doit contenir au minimum deux feuilles :

- `data` : les publications macro, avec les colonnes comme `event_date`, `country`, `event`, `actual`, `estimate`, `previous`
- `METRIQ_FINISH` : les metriques historiques de surprise, avec les colonnes comme `Country`, `events`, `higher_is_good`, `surprise_avg_10y`, `surprise_std_10y`

L'idee est de calculer :

```text
surprise_raw = actual - estimate
surprise_z = (surprise_raw - historical_average_surprise) / historical_surprise_std
signal = surprise_z * direction
```

## Fichiers prix actions

Le format attendu pour chaque action est :

```text
timestamp,open,high,low,close,volume
2016-11-16 14:31:00+00,14.88,14.92,14.88,14.92,200
```

Notes :

- un CSV par action
- timeframe 1 minute
- timestamp idealement en UTC
- VWAP calcule intraday avec reset chaque jour
- ticker generalement extrait du nom du fichier

Les dossiers de donnees brutes comme `US-Actions/` ou `data/raw/` restent locaux et sont ignores par Git.
