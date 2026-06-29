# Macro Surprise + VWAP Execution

Ce repo présente mon premier screening d'actions US autour des surprises macroéconomiques et d'une exécution intraday basée sur le VWAP.

La question de départ est simple : quand une statistique macro importante sort au-dessus ou en-dessous des attentes, est-ce que certaines actions individuelles montrent des comportements court terme exploitables avec une règle d'entrée plus disciplinée autour du VWAP ?

Je ne veux pas présenter ça comme une stratégie de trading déjà prête. C'est un backtest de recherche, avec plusieurs tests de robustesse. L'intérêt n'est pas seulement de voir quelles actions semblent bien marcher, mais aussi de comprendre lesquelles deviennent fragiles dès qu'on impose des tests aléatoires, des coûts, ou un vrai découpage chronologique train/test.

## Structure Du Repo

```text
macro-vwap-event-study/
|-- README.md
|-- requirements.txt
|-- .gitignore
|-- scripts/
|   |-- macro_event_backtester_single_country_20stocks.py
|   `-- macro_event_backtester_single_country_20stocks_trader_graphs.py
|-- notebooks/
|   `-- 01_macro_vwap_research_summary.ipynb
|-- reports/
|   `-- trader_report/
|       |-- figures/
|       |-- csv_outputs/
|       `-- notes/
`-- data/
    `-- README.md
```

Les scripts Python restent le moteur du backtest. Le notebook sert de résumé lisible pour une revue .

## Ce Que Fait Le Backtest

Pour chaque publication macro, le script compare la valeur publiée avec le consensus :

```text
surprise_raw = actual - estimate
surprise_z = (surprise_raw - historical_average_surprise) / historical_surprise_std
signal = surprise_z * direction
```

`direction` vaut `+1` quand une valeur macro plus élevée est considérée comme positive, et `-1` quand une valeur plus faible est considérée comme positive. Les événements marqués comme `MIXED` sont exclus.

Le moteur teste ensuite deux idées :

- `DRIFT` : trader dans le sens du signal macro.
- `FADE` : trader contre le signal macro.

Le VWAP est utilisé comme filtre d'exécution. Pour un long, le modèle préfère entrer quand le prix est sous ou proche du VWAP. Pour un short, il préfère entrer quand le prix est au-dessus ou proche du VWAP. Si le prix n'est pas favorable, le modèle attend un retour vers le VWAP dans une fenêtre définie.

Une limite importante : beaucoup de publications macro US sortent avant l'ouverture des actions US. Donc il faut plutôt lire cette version comme un test "jour de macro + VWAP intraday" que comme une réaction pure minute par minute au timestamp de la publication.

## Tests De Robustesse

Le moteur évite de garder une action seulement parce que le backtest complet est positif. Il teste :

- test avec sens de trade aléatoire
- test avec timestamp aléatoire
- placebo avec décalage temporel
- sweep de coûts de transaction
- split chronologique train/test
- walk-forward par année

Le split train/test est le point le plus important. La règle est sélectionnée sur les premiers 70% de la période, puis testée sur les derniers 30%. Si une règle paraît bonne sur l'échantillon complet mais perd de l'argent sur la période de test, je la considère comme rejetée ou au minimum fragile.

## Comment Lancer

Installer les dépendances Python :

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Lancer le moteur de backtest :

```bash
python scripts/macro_event_backtester_single_country_20stocks.py
```

Le script demande le fichier macro, le pays, puis les CSV minute des actions. Il écrit ensuite un dossier de résultats timestampé avec des fichiers comme :

- `single_country_master_summary.csv`
- `single_country_all_configs_summary.csv`
- `single_country_random_tests.csv`
- `single_country_train_test.csv`
- `single_country_walk_forward.csv`

Après le run, copier les CSV de synthèse que l'on veut partager dans :

```text
reports/trader_report/csv_outputs/
```

Si des graphiques sont disponibles, placer les PNG retenus dans :

```text
reports/trader_report/figures/
```

Puis ouvrir :

```text
notebooks/01_macro_vwap_research_summary.ipynb
```

Le notebook lit les CSV et les figures déjà générés. Il n'est pas censé relancer tout le backtest.

## Données

Les données brutes ne sont pas incluses dans le repo.

Pour ce premier test, j'ai travaillé avec environ 10 ans de données minute (`1 minute timeframe`) sur les actions testées. Les fichiers sont assez lourds et je n'arrive pas à les charger proprement ici, donc je ne les mets pas directement sur GitHub.

Si tu lis ce repo et que tu veux vérifier exactement les données utilisées, contacte-moi et je peux t'envoyer les fichiers par mail.

Les entrées attendues sont :

- un fichier macro avec actual, estimate, previous et les métriques historiques de surprise
- un CSV OHLCV minute par action

Voir `data/README.md` pour le format attendu.

## Limites Actuelles

- La version US actuelle contient beaucoup d'entrées `PRE_OPEN_SAME_DAY`, donc il faut rester honnête sur l'interprétation temporelle.
- Les entrées VWAP en `close_cross` sont plus faciles à remplir et peuvent être optimistes.
- `limit_touch` est plus conservateur et doit être testé plus en profondeur.
- Un résultat positif sur l'échantillon complet ne suffit pas. Les tests train/test et random servent justement à rejeter les noms probablement sur-optimisés.
- Les noms de fichiers peuvent créer des problèmes de présentation des tickers. Le notebook les signale au lieu de les cacher.

Ce projet est un travail de recherche, pas un conseil d'investissement.
