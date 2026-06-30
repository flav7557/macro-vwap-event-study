# Test 03 - Deep dive sur les actifs selectionnes

## Ce que l'on fera ensuite

Ce test se concentrera seulement sur les meilleurs candidats du Test 02.

Actifs possibles :

- SMTC
- VIAV
- RVLV
- SAM
- REAL
- IRTC

Le but sera de comprendre si l'edge vient de :

- la direction macro
- l'execution VWAP
- certains types d'evenements macro
- certaines annees
- le comportement pre-market
- ou une combinaison de ces facteurs

Controles possibles :

- augmenter les simulations random a 500
- comparer `close_cross` et `limit_touch`
- regarder la performance par annee
- regarder les principaux types d'evenements
- inspecter DRIFT vs FADE par action
- verifier plus proprement la sensibilite aux couts
