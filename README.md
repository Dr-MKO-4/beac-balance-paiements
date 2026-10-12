# BEAC -- Analyse du taux de rétention des exportations pétrolières (CEMAC)

Analyse de la balance des paiements des économies exportatrices de pétrole, construite dans le cadre d'un stage à la Banque des États de l'Afrique Centrale (BEAC), Service de la Balance des Paiements. L'étude mesure la part de la valeur exportée réellement retenue par l'économie nationale (taux de rétention des exportations, TRE), positionne les six pays de la CEMAC dans une typologie mondiale, et identifie par quel canal chacun perd sa valeur exportée (clustering multivarié).

## Méthodologie

Formule complète du taux de rétention :

```
TC  = Crédit biens / Débit biens x 100        (taux de couverture des biens)
TM  = Débit biens / Crédit biens x 100        (taux de couverture des importations)
TAS = max(0, -solde services) / Crédit biens x 100
TFR = max(0, -solde revenu primaire) / Crédit biens x 100
TRE = 100 - TM - TAS - TFR
```

La typologie retient des **bandes absolues et fixes** (CRITIQUE < 0 %, FAIBLE 0-20 %, NORMAL 20-50 %, BON ≥ 50 %), appliquées **année par année** sur six années cibles (2014, 2015, 2016, 2019, 2020, 2021 -- encadrant le contre-choc pétrolier de 2015-2016 et la crise COVID de 2019-2021), plutôt qu'un calibrage statistique relatif (k-means), qui s'est révélé trompeur sur ce panel (il désigne toujours le tiers supérieur de l'échantillon comme « bon », même quand ce tiers reste faible en valeur absolue).

Le détail complet de la démarche, des résultats et de leur discussion se trouve dans `rapport/rapport_bdp.tex`.

## Scripts

| Script | Rôle |
|---|---|
| `scripts/extraire_bdp_cemac_brut.py` | Extraction des postes Biens/Services/Revenu primaire depuis les fichiers BDP officiels bruts de la BEAC (CEMAC, 2020-2023) |
| `scripts/extraire_tre_brut_fmi.py` | Extraction des mêmes postes depuis les fichiers sources bruts du FMI (format SDMX `IMF.STA:BOP`), panel mondial de 40 pays exportateurs de pétrole, 6 années cibles |
| `scripts/analyser_tre_global_cemac.py` | Calcul du TRE (formule complète), typologie par bandes absolues, positionnement des 6 pays CEMAC, génération des graphiques |
| `scripts/clustering_multicritere_tcm_tas_tfr.py` | Clustering multivarié (TC, TM, TAS, TFR) des profils de fuite, projection ACP |

## Utilisation

```bash
pip install -r requirements.txt
```

Placer les fichiers sources dans `data/` selon la structure décrite dans `data/README.md`, puis :

```bash
cd scripts
python extraire_bdp_cemac_brut.py          # génère data/TRE_CEMAC_RECALCULE.csv
python analyser_tre_global_cemac.py         # typologie + graphiques (figures/)
python clustering_multicritere_tcm_tas_tfr.py  # clustering multivarié (figures/)
```

## Structure du dépôt

```
balance_de_paiement/
|-- scripts/      Scripts d'extraction et d'analyse (voir ci-dessus)
|-- rapport/       Rapport scientifique complet (LaTeX + bibliographie)
|-- figures/       Graphiques générés par les scripts
|-- notebooks/     Exploration initiale (Jupyter)
|-- data/          Non versionné -- voir data/README.md
```

## Limites connues

- Les six pays de la CEMAC n'ont pas tous une couverture FMI suffisante sur les années cibles : seul le Cameroun dispose de données exploitables dans cette source ; les cinq autres (Congo, Gabon, Guinée Équatoriale, Tchad, RCA) sont positionnés à partir des fichiers BEAC officiels (2020-2023 uniquement).
- Le sous-compte « revenu primaire débité » est très incomplètement renseigné dans le panel FMI pour la plupart des pays hors CEMAC ; les valeurs de TRE qui en dérivent doivent se lire comme un plancher de fuite mesurable avec les données disponibles.
