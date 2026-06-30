# A lire en premier

Ce projet est organise par tests de recherche.

## Comment lire le projet

1. Commencer par `research_tests/test_01_us_macro_vwap_screening/`
   C'est le premier screening large sur actions US.

2. Lire ensuite `research_tests/test_02_train_test_validation/`
   C'est l'etape de validation plus stricte. Elle explique pourquoi certains noms sont rejetes meme si leur rendement full-sample est positif.

3. `research_tests/test_03_deep_dive_selected_assets/`
   C'est la prochaine etape. Elle n'est pas encore terminee.

## Statut actuel

Le projet est actuellement au Test 02.

Les noms les plus propres actuellement sont :

- SMTC
- VIAV

RVLV et SAM restent interessants mais plus fragiles.

REAL et IRTC restent en watchlist, mais le signal semble plus VWAP-driven ou moins clairement macro-directionnel.

## Avertissement principal

La plupart des publications macro US ont lieu avant l'ouverture du marche actions. Donc le setup actuel doit etre interprete comme :

```text
jour de calendrier macro + VWAP intraday
```

et non comme :

```text
reaction pure minute par minute au timestamp exact de publication macro
```

## Ou sont les fichiers

- chaque test a ses propres scripts, notebooks, resultats, figures et notes
- le format des donnees est explique dans `shared/data_format/`
- les anciens fichiers ou fichiers incertains sont gardes dans `archive/`
