# Macro Surprise + VWAP Execution

Ce repo presente mon premier screening d'actions US autour des surprises macroeconomiques et d'une execution intraday basee sur le VWAP.

La question de depart est simple : quand une statistique macro importante sort au-dessus ou en-dessous des attentes, est-ce que certaines actions individuelles montrent des comportements court terme exploitables avec une regle d'entree plus disciplinee autour du VWAP 

Je ne veux pas presenter ca comme une strategie de trading deja prete. C'est un backtest de recherche, avec plusieurs tests de robustesse. L'interet n'est pas seulement de voir quelles actions semblent bien marcher, mais aussi de comprendre lesquelles deviennent fragiles des qu'on impose des tests aleatoires, des couts, ou un vrai decoupage chronologique train/test.

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

Les scripts Python restent le moteur du backtest. Le notebook sert de resume lisible pour une revue .

## Ce Que Fait Le Backtest

Pour chaque publication macro, le script compare la valeur publiee avec le consensus :

```text
surprise_raw = actual - estimate
surprise_z = (surprise_raw - historical_average_surprise) / historical_surprise_std
signal = surprise_z * direction
```

`direction` vaut `+1` quand une valeur macro plus elevee est consideree comme positive, et `-1` quand une valeur plus faible est consideree comme positive. Les evenements marques comme `MIXED` sont exclus.

Le moteur teste ensuite deux idees :

- `DRIFT` : trader dans le sens du signal macro.
- `FADE` : trader contre le signal macro.

Le VWAP est utilise comme filtre d'execution. Pour un long, le modele prefere entrer quand le prix est sous ou proche du VWAP. Pour un short, il prefere entrer quand le prix est au-dessus ou proche du VWAP. Si le prix n'est pas favorable, le modele attend un retour vers le VWAP dans une fenetre definie.

Une limite importante : beaucoup de publications macro US sortent avant l'ouverture des actions US. Donc il faut plutot lire cette version comme un test "jour de macro + VWAP intraday" que comme une reaction pure minute par minute au timestamp de la publication.

## Tests De Robustesse

Le moteur evite de garder une action seulement parce que le backtest complet est positif. Il teste :

- test avec sens de trade aleatoire
- test avec timestamp aleatoire
- placebo avec decalage temporel
- sweep de couts de transaction
- split chronologique train/test
- walk-forward par annee

Le split train/test est le point le plus important. La regle est selectionnee sur les premiers 70% de la periode, puis testee sur les derniers 30%. Si une regle parait bonne sur l'echantillon complet mais perd de l'argent sur la periode de test, je la considere comme rejetee ou au minimum fragile.

## Comment Lancer

Installer les dependances Python :

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Lancer le moteur de backtest :

```bash
python scripts/macro_event_backtester_single_country_20stocks.py
```

Le script demande le fichier macro, le pays, puis les CSV minute des actions. Il ecrit ensuite un dossier de resultats timestampe avec des fichiers comme :

- `single_country_master_summary.csv`
- `single_country_all_configs_summary.csv`
- `single_country_random_tests.csv`
- `single_country_train_test.csv`
- `single_country_walk_forward.csv`

Apres le run, copier les CSV de synthese que l'on veut partager dans :

```text
reports/trader_report/csv_outputs/
```

Si des graphiques sont disponibles, placer les PNG retenus dans :

```text
reports/trader_report/figures/
```

La V1 actuelle du repo inclut deja les sorties du run :

```text
macro_vwap_single_country_results_20260629_225714
```

Elles sont rangees dans `reports/trader_report/csv_outputs/` et `reports/trader_report/figures/`.

Puis ouvrir :

```text
notebooks/01_macro_vwap_research_summary.ipynb
```

Le notebook lit les CSV et les figures deja generes. Il n'est pas cense relancer tout le backtest.

## Donnees

Les donnees brutes ne sont pas incluses dans le repo.

Pour ce premier test, j'ai travaille avec environ 10 ans de donnees minute (`1 minute timeframe`) sur les actions testees. Les fichiers sont assez lourds et je n'arrive pas a les charger proprement ici, donc je ne les mets pas directement sur GitHub.

Si tu lis ce repo et que tu veux verifier exactement les donnees utilisees, contacte-moi et je peux t'envoyer les fichiers par mail.

Les entrees attendues sont :

- un fichier macro avec actual, estimate, previous et les metriques historiques de surprise
- un CSV OHLCV minute par action

Voir `data/README.md` pour le format attendu.

## Limites Actuelles

- La version US actuelle contient beaucoup d'entrees `PRE_OPEN_SAME_DAY`, donc il faut rester honnete sur l'interpretation temporelle.
- Les entrees VWAP en `close_cross` sont plus faciles a remplir et peuvent etre optimistes.
- `limit_touch` est plus conservateur et doit etre teste plus en profondeur.
- Un resultat positif sur l'echantillon complet ne suffit pas. Les tests train/test et random servent justement a rejeter les noms probablement sur-optimises.
- Les noms de fichiers peuvent creer des problemes de presentation des tickers. Le notebook les signale au lieu de les cacher.

Ce projet est un travail de recherche, pas un conseil d'investissement.
