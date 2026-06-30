# Test 02 - Validation train/test plus propre

## Ce que l'on fait ici

Dans le Test 01, certaines actions semblaient profitables sur tout l'echantillon. Dans le Test 02, on verifie si la regle selectionnee sur la premiere partie des donnees fonctionne encore sur la periode de test plus recente.

L'idee est simple :

- selectionner la meilleure regle sur la periode train
- appliquer exactement la meme regle sur la periode test
- rejeter l'action si elle perd de l'argent sur la periode test

## Ce qui change vs Test 01

Le Test 02 rend la validation plus stricte.

Une action peut maintenant etre rejetee meme si son rendement full-sample est positif, parce que ce qui compte est de savoir si la regle fonctionne hors echantillon.

## Resultat actuel principal

Les noms les plus propres du Test 02 sont :

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

Rejetes malgre des rendements full-sample positifs :

- BOOT
- ENVX
- KOP
- LMND
- LUMN
- VREX

## Pourquoi certains noms profitables sont rejetes

Ces noms ne sont pas rejetes parce qu'ils n'ont jamais gagne d'argent. Ils sont rejetes parce que le resultat full-sample semblait positif, mais la regle selectionnee sur la periode train perdait de l'argent sur la periode test.

C'est un signal que le resultat peut etre overfit ou dependant d'un regime precis.

## Contenu du dossier

- `scripts/` contient la note sur le statut du script V2
- `notebooks/` contient le notebook train/test V2
- `results/csv_outputs/` contient les CSV de synthese V2
- `results/figures/` contient les figures V2
- `notes/` contient les notes sur les sorties V2 et les problemes de noms de tickers
