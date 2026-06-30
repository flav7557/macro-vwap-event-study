# Macro VWAP Event Study

Ce repo presente mon etude sur les journees de surprises macro US et une execution intraday basee sur le VWAP.

Le but n'est pas de dire que la strategie est prete a trader. Le but est de documenter la recherche etape par etape, pour qu'un trader puisse voir ce qui a ete teste, ce qui a change, et pourquoi certains noms sont retenus ou rejetes.

Commencer ici :

```text
READ_ME_FIRST.md
```

## Organisation du repo

Le repo est organise par test de recherche, pas seulement par type de fichier.

```text
research_tests/
|-- test_01_us_macro_vwap_screening/
|-- test_02_train_test_validation/
`-- test_03_deep_dive_selected_assets/
```

Chaque dossier de test contient ses propres :

- scripts
- notebooks
- resultats
- figures
- notes

## Ce que signifie chaque test

### Test 01 - US macro + VWAP screening

C'etait le premier screening large.

L'objectif etait de tester si les journees de surprise macro US, combinees a une execution VWAP, pouvaient faire ressortir des patterns court terme interessants sur une selection d'actions US.

Dossier :

```text
research_tests/test_01_us_macro_vwap_screening/
```

### Test 02 - Validation train/test plus propre

C'est l'etape actuelle terminee.

On verifie si la regle selectionnee sur la premiere partie de l'historique fonctionne encore sur la periode de test plus recente. C'est important parce qu'un backtest full-sample peut etre positif alors que la regle selectionnee sur le train echoue hors echantillon.

Dossier :

```text
research_tests/test_02_train_test_validation/
```

### Test 03 - Deep dive sur les actifs selectionnes

C'est la prochaine etape prevue.

Elle se concentrera seulement sur les noms les plus forts ou les plus interessants du Test 02.

Dossier :

```text
research_tests/test_03_deep_dive_selected_assets/
```

## Resultats actuels

Noms les plus propres du Test 02 :

- SMTC
- VIAV

Interessants mais plus fragiles :

- RVLV
- SAM

Watchlist / plus VWAP-driven :

- REAL
- IRTC
- LMB
- PLAY
- VSAT

Rejetes malgre un rendement full-sample positif :

- BOOT
- ENVX
- KOP
- LMND
- LUMN
- VREX

## Donnees

Les donnees brutes minute ne sont pas incluses dans le repo.

Pour cette etude, j'ai utilise environ 10 ans de donnees actions en timeframe 1 minute. Les fichiers sont lourds et ne sont pas uploades ici. Si quelqu'un veut les fichiers bruts exacts, je peux les envoyer par mail.

Le format attendu des donnees est explique ici :

```text
shared/data_format/README.md
```

## Avertissement principal

La plupart des publications macro US sont pre-market.

Donc ce travail doit etre interprete comme :

```text
jour de calendrier macro + VWAP intraday
```

et pas comme une reaction pure minute par minute au timestamp de publication.
