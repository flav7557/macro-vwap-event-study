# Test 01 - Screening US macro + VWAP

## Ce que l'on fait ici

Ce premier test screen une selection d'actions US avec un signal de surprise macro et un filtre d'execution VWAP.

Le but n'est pas encore de prouver une strategie tradable. Le but est de voir si certaines actions reagissent mieux en DRIFT, d'autres en FADE, et si le VWAP aide a mieux cadrer l'entree.

## Ce que ce test a produit

Ce test a produit :

- une classification des actions entre propres / suspectes / rejetees
- les premiers candidats interessants
- les premiers tests de robustesse
- les premiers graphiques pour une lecture trader

## Lecture principale

La premiere version a trouve plusieurs noms interessants, mais elle a aussi montre que certains resultats pouvaient etre surtout VWAP-driven ou trop dependants du full-sample.

## Limite principale

La plupart des publications macro US sont pre-market. Ce test doit donc etre lu comme "jour de calendrier macro + VWAP intraday", pas comme une reaction pure minute par minute aux publications macro.

## Contenu du dossier

- `scripts/` contient le script du premier screening
- `notebooks/` contient le premier notebook de synthese
- `results/csv_outputs/` contient les CSV de synthese V1
- `results/figures/` contient les figures trader V1
- `notes/` contient les notes courtes du premier rapport
