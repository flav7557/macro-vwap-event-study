# Changelog

## V2 - Validation train/test plus propre

Date : 2026-06-30

Changement principal :

Le modele rend maintenant la validation chronologique train/test plus explicite. Il distingue mieux la profitabilite full-sample et la performance sur la periode de test hors echantillon.

Points importants de V2 :

- noms A-class : SMTC, VIAV
- noms B-class : RVLV, SAM
- watchlist / C : REAL, IRTC, LMB, PLAY, VSAT, BLFS, GPRO
- noms rejetes : BOOT, ENVX, KOP, LMND, LUMN, VREX

Point important :

Plusieurs noms avaient des rendements full-sample positifs mais ont ete rejetes parce que la regle selectionnee sur la periode train perdait de l'argent sur la periode test.

Avertissement principal :

La plupart des publications macro US sont pre-market. Le framework doit donc etre interprete comme "jour de calendrier macro + VWAP intraday", pas comme une reaction pure minute par minute aux publications macro.

## V1 - Premier screening US macro + VWAP

Date : 2026-06-29

Changement principal :

Premier screening large US avec signal de surprise macro + execution VWAP.

Objectif :

Identifier quelles actions US pourraient montrer un comportement directionnel ou contrariant autour des jours de publications macro.
