# BEAC : rétention de la valeur des exportations dans les économies pétrolières

Analyse de la balance des paiements réalisée pendant un stage à la Banque des États de l'Afrique Centrale (BEAC), Service de la Balance des Paiements (août à octobre 2026). L'étude mesure la part de la valeur des exportations de biens que les grands exportateurs de pétrole conservent réellement, identifie les leviers qui permettent de progresser d'un niveau de rétention à l'autre, et positionne les six États de la CEMAC.

## Question et hypothèses

Quelle part de la valeur de leurs exportations les économies exportatrices de pétrole parviennent-elles à conserver, et par quels leviers peuvent-elles passer d'une rétention faible à une rétention élevée ?

- **H1** : la rétention s'organise en niveaux distincts.
- **H2** : un chemin de progression entre ces niveaux existe, avec des leviers identifiables.
- **H3** : les six États de la CEMAC peuvent être situés dans cette typologie (le Cameroun sert de référent).

## Méthode

Indicateurs, tous rapportés aux recettes d'exportation de biens :

```
TM  = Débit des biens / Crédit des biens x 100
TAS = max(0, -Solde des services) / Crédit des biens x 100
TFR = max(0, -Solde du revenu primaire) / Crédit des biens x 100
TRE = 100 - TM - TAS - TFR
```

- **Panel** : 41 pays du top 50 mondial des exportateurs de pétrole, ayant des données FMI complètes sur six années cibles (2014, 2015, 2016, 2019, 2020, 2021).
- **Cinq bandes absolues** : TRÈS CRITIQUE (< -78 %), CRITIQUE (-78 à 0 %), FAIBLE (0 à 16 %), NORMAL (16 à 35 %), BON (>= 35 %). Le seuil 0 découle de la définition ; les autres sont les ruptures naturelles mesurées séparément sur les taux négatifs et positifs.
- **Lecture année par année**, matrice de transition entre années cibles et décomposition de chaque montée de bande par levier.
- **Profils de fuite** : k-moyennes sur TM, TAS et TFR (nombre de classes choisi par le score de silhouette), représentées par ACP.
- **Score relatif** : position de chaque pays CEMAC par rapport à la moyenne du panel la même année.

## Scripts

| Script | Rôle |
|---|---|
| `scripts/extraire_bdp_cemac_brut.py` | Extraction des postes depuis les fichiers BDP officiels de la BEAC (2020 à 2023) |
| `scripts/extraire_tre_brut_fmi.py` | Chargement des données FMI et BEAC, calcul des indicateurs et des bandes |
| `scripts/analyse_typologie_trajectoires.py` | H1 et H2 : distribution, typologie par année, transitions, leviers |
| `scripts/clustering_profils_fuite.py` | Profils de fuite : classification, ACP, parcours des pays CEMAC |
| `scripts/positionnement_cemac.py` | H3 : trajectoires CEMAC, usage de la valeur exportée, leviers, score relatif |
| `scripts/style_graphiques.py` | Charte graphique commune (palettes vérifiées) |

## Utilisation

```bash
pip install -r requirements.txt
cd scripts
python extraire_bdp_cemac_brut.py          # génère data/TRE_CEMAC_RECALCULE.csv
python analyse_typologie_trajectoires.py   # figures H1 et H2
python clustering_profils_fuite.py         # profils de fuite
python positionnement_cemac.py             # positionnement de la CEMAC
```

Les figures sont écrites dans `figures/` et les résultats chiffrés dans `resultats/`. Les données sources ne sont pas versionnées : leur structure attendue est décrite dans `data/README.md`.

## Limites

- Pour le Gabon (2020 et 2021), la Guinée Équatoriale, le Tchad et la RCA, seules les années 2020 et 2021 sont disponibles parmi les années cibles (source BEAC).
- La mesure du revenu primaire dépend de la qualité de déclaration des bénéfices et intérêts versés aux non-résidents.
- Le TRE ne tient pas compte du revenu secondaire (transferts courants).
