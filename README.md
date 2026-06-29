# Macro Surprise + VWAP Execution

Ce repo presente mon etude sur les journees de publications macro US et une execution intraday autour du VWAP.

L'idee de depart est simple : tester si certaines actions reagissent de facon assez reguliere aux surprises macro pour etre analysees avec une regle d'entree plus disciplinee autour du VWAP.

Je ne presente pas ca comme une strategie prete a trader. C'est un travail de recherche. Le but est de separer les noms qui semblent vraiment plus robustes de ceux qui ont juste un bon backtest complet mais qui cassent quand on regarde le train/test, les tests random ou les couts.

## Structure du repo

```text
macro-vwap-event-study/
|-- README.md
|-- requirements.txt
|-- .gitignore
|-- CHANGELOG.md
|-- PROJECT_STATUS.md
|-- scripts/
|   |-- v1_screening/
|   |   `-- macro_event_backtester_single_country_20stocks.py
|   |-- v2_train_test_clean/
|   |   `-- README.md
|   `-- reporting/
|       `-- macro_event_backtester_single_country_20stocks_trader_graphs.py
|-- notebooks/
|   |-- 01_macro_vwap_research_summary.ipynb
|   `-- 02_train_test_validation_update.ipynb
|-- reports/
|   |-- v1_us_screening/
|   |   |-- csv_outputs/
|   |   |-- figures/
|   |   `-- notes/
|   `-- v2_train_test_clean/
|       |-- csv_outputs/
|       |-- figures/
|       `-- notes/
|-- data/
|   `-- README.md
`-- archive/
    `-- old_outputs/
```

V1 correspond au premier screening US macro + VWAP.

V2 correspond a la validation train/test plus propre.

## Comment lancer le backtest

Installer les dependances :

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Le script V1 est ici :

```bash
python scripts/v1_screening/macro_event_backtester_single_country_20stocks.py
```

Le script demande le fichier macro, le pays, puis les fichiers minute des actions. Il genere ensuite un dossier local de resultats avec les CSV de synthese.

Note importante : le script exact utilise pour produire le run V2 n'etait pas present dans les fichiers locaux fournis. Les sorties V2 sont bien archivees dans le repo, mais le code V2 exact devra etre ajoute si je le retrouve.

## Comment lire les notebooks

Le notebook principal est :

```text
notebooks/01_macro_vwap_research_summary.ipynb
```

Il explique l'idee de recherche, le signal macro, DRIFT vs FADE, l'execution VWAP, les tests de robustesse, puis compare V1 et V2.

Le notebook centre sur la validation train/test est :

```text
notebooks/02_train_test_validation_update.ipynb
```

Il montre pourquoi un rendement full-sample positif ne suffit pas, et pourquoi certains noms sont rejetes meme s'ils avaient l'air profitables au depart.

## Ou sont les resultats

Resultats V1 :

```text
reports/v1_us_screening/
```

Resultats V2 :

```text
reports/v2_train_test_clean/
```

Les CSV de synthese sont dans `csv_outputs/`.

Les figures du rapport sont dans `figures/`.

Les notes courtes sont dans `notes/`.

## Donnees

Pour ce premier travail, j'ai teste environ 10 ans de donnees en timeframe 1 minute sur les actions. Les fichiers sont trop lourds pour etre charges ici, et je ne veux pas publier les donnees brutes directement sur GitHub.

Si tu lis ce repo et que tu veux verifier les fichiers exacts utilises, contacte-moi et je peux te les envoyer par mail.

Le format attendu est explique dans :

```text
data/README.md
```

## Statut actuel

V2 est le stade courant.

La validation train/test est maintenant plus stricte. En V2, les candidats les plus propres sont SMTC et VIAV. RVLV et SAM restent interessants, mais sont classes comme plus fragiles. REAL, IRTC, LMB, PLAY, VSAT, BLFS et GPRO restent plutot en watchlist car le signal semble plus VWAP-driven ou moins clairement macro-directionnel.

## Limites principales

- Beaucoup de publications macro US ont lieu avant l'ouverture du marche actions.
- Le framework doit donc etre lu comme "macro calendar day + VWAP intraday", pas comme une reaction pure minute par minute a la publication.
- Les entrees `close_cross` sont plus optimistes que `limit_touch`.
- Certains tickers viennent de noms de fichiers imparfaits. Dans les notebooks, `LONDON-STRATEGIC-EDGE` est affiche comme LMB quand le fichier source correspond a LMB.
- Il y a encore un doublon IRTC a nettoyer dans les fichiers sources.

## Prochaines etapes

V3 devrait se concentrer sur les meilleurs candidats :

- SMTC
- VIAV
- RVLV
- SAM
- REAL
- IRTC

Tests possibles :

- augmenter les simulations random a 500
- comparer `close_cross` et `limit_touch` plus serieusement
- regarder la performance par annee
- regarder les types d'evenements macro les plus importants
- comparer DRIFT vs FADE par action
- verifier si l'edge vient du signal macro, du filtre VWAP, ou des deux
