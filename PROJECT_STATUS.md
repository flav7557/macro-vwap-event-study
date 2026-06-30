# Statut du projet

## Etape actuelle

Test 02 termine - validation train/test plus propre.

## Chemin de recherche

### Test 01 - US macro + VWAP screening

Question :

Tester si les journees de surprise macro + une execution VWAP peuvent faire ressortir des patterns interessants sur une selection d'actions US.

Resultat :

Certains noms semblaient prometteurs, mais la premiere version avait besoin d'une validation plus stricte.

### Test 02 - Validation train/test plus propre

Question :

Verifier si les regles selectionnees sur la periode ancienne fonctionnent encore sur la periode plus recente.

Resultat :

SMTC et VIAV sont les noms les plus propres. RVLV et SAM restent interessants mais plus fragiles. Plusieurs noms sont rejetes parce qu'ils echouent sur la periode de test chronologique.

### Test 03 - Deep dive sur les actifs selectionnes

Prochaine question :

Pour les meilleurs noms, comprendre d'ou vient vraiment l'edge : direction macro, execution VWAP, type d'evenement, comportement pre-market, ou combinaison de plusieurs facteurs.
