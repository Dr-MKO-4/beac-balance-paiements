# Projet balance_de_paiement  Analyse de la balance des paiements

## Objectif

`balance_de_paiement` est un projet d'analyse macroéconomique des balances des paiements des pays de la CEMAC. Il transforme des relevés BEAC et des données FMI en tableaux comparatifs, indicateurs de diagnostic, graphiques et rapport scientifique.

Le projet cherche à mesurer les soldes extérieurs, la dépendance aux exportations de matières premières, les sorties de revenus vers l'étranger et la soutenabilité de la position extérieure des pays étudiés.

## Axes de travail

### 1. Analyse locale à partir des données BEAC

Les notebooks `bop_cemac_beac.ipynb` et `graphiques_bdp.ipynb` exploitent les relevés BEAC disponibles pour la CEMAC, notamment sur la période 2020–2023. Le traitement comprend :

- lecture et harmonisation des fichiers Excel ;
- regroupement des lignes de la balance par comptes et sous-comptes ;
- contrôle des écarts entre les comptes et les totaux ;
- conversion des montants selon les conventions retenues ;
- calcul d'indicateurs comparables entre pays et années ;
- production de tableaux CSV et de graphiques PDF.

Les pays présents dans le périmètre local comprennent notamment le Congo, le Gabon, la Guinée équatoriale, le Tchad et la République centrafricaine, avec un traitement distinct selon la disponibilité des relevés.

### 2. Analyse comparative basée sur les données FMI

Le notebook `bop_fmi.ipynb` utilise une classification des indicateurs de balance des paiements et les données consolidées pour construire une base plus large. Il produit des résultats à la granularité pays/année et permet de comparer les pays CEMAC à un ensemble international.

Le traitement comprend :

- filtrage des indicateurs selon la classification retenue ;
- agrégation par compte, type d'opération et niveau analytique ;
- calcul de dix métriques d'analyse externe ;
- sélection des pays et périodes comparables ;
- génération de tableaux complets et de tableaux illustratifs ;
- comparaison avec le PIB et les données macroéconomiques disponibles.

## Indicateurs et résultats produits

Les travaux couvrent notamment :

- le solde du compte courant, du compte de capital et du compte financier ;
- les soldes des biens, services, revenus primaires et revenus secondaires ;
- le taux de couverture des biens ;
- le poids du déficit des services ;
- la fuite ou rétention des revenus d'exportation ;
- le ratio du solde courant rapporté au PIB ;
- les indicateurs de termes de l'échange et de vulnérabilité extérieure ;
- la classification des situations économiques et les diagnostics comparatifs.

## Rapport scientifique

Le rapport LaTeX analyse principalement le Congo, le Gabon et le Tchad pour l'exercice 2021, selon le cadre BPM6 du FMI. Il présente :

- la méthodologie et les définitions des soldes ;
- les sources BEAC et les limites de qualité des données ;
- la comparaison des trois pays ;
- les graphiques des soldes et des ratios ;
- l'interprétation des excédents courants et des déficits structurels de services et de revenus ;
- les implications liées à la dépendance pétrolière, aux investissements étrangers et à la diversification économique.

Le projet contient déjà des sorties exploitables : CSV analytiques, tableaux comparatifs, graphiques PDF, rapport PDF et page HTML de benchmark.

## Arborescence utile

- `data/` : fichiers bruts, fichiers consolidés, classifications, métriques et tableaux calculés ;
- `notebooks/bop_cemac_beac.ipynb` : pipeline d'analyse BEAC locale ;
- `notebooks/bop_fmi.ipynb` : pipeline FMI et comparaison élargie ;
- `notebooks/graphiques_bdp.ipynb` : graphiques du rapport Congo–Gabon–Tchad ;
- `figures/` : figures générées ;
- `tableaux/` : tableaux PDF ;
- `rapport/` : source LaTeX, bibliographie et rapport associé ;
- `rapport.tex` : autre version de la source du rapport ;
- `bdp_radar_benchmark_metriques.html` : restitution HTML des métriques et du benchmark.

## Étapes suivantes

### Priorité 1  Fiabiliser les données

- Centraliser clairement les sources BEAC et FMI, les périodes couvertes et les versions de fichiers.
- Vérifier les correspondances entre les comptes, les agrégats et la classification BPM6.
- Contrôler systématiquement les écarts par compte avec `VERIFICATION_ECARTS_PAR_COMPTE.csv`.
- Documenter les conversions FCFA/USD, en particulier l'usage du taux fixe lorsqu'aucun taux annuel n'est disponible.
- Traiter explicitement les valeurs manquantes, les doublons et les postes « erreurs et omissions ».

### Priorité 2  Consolider les indicateurs

- Valider les dix métriques avec des formules et des conventions identiques entre les pipelines BEAC et FMI.
- Distinguer les termes de l'échange calculés directement des proxys fondés sur les taux de couverture.
- Vérifier les seuils de diagnostic sur plusieurs années et éviter de les interpréter comme des normes universelles.
- Ajouter des contrôles automatiques de cohérence avant chaque génération de tableau ou de figure.

### Priorité 3  Finaliser le rapport et les restitutions

- Mettre à jour les tableaux et figures après la dernière version des données.
- Harmoniser les deux sources LaTeX (`rapport.tex` et `rapport/rapport_bdp.tex`) pour éviter les divergences.
- Reproduire le PDF depuis une procédure documentée et vérifier la bibliographie avec Biber.
- Relire les interprétations économiques en séparant les résultats observés, les proxys et les hypothèses.
- Ajouter une synthèse CEMAC et, si nécessaire, des fiches par pays.

### Priorité 4  Rendre l'analyse reproductible

- Extraire les fonctions communes de préparation et de calcul dans des scripts Python réutilisables.
- Paramétrer les chemins, les années, les pays et les taux de conversion au lieu de les laisser dispersés dans les notebooks.
- Ajouter des tests sur les agrégations, les soldes, les ratios et les contrôles d'écarts.
- Générer automatiquement les CSV, les tableaux PDF, les figures et le rapport à partir d'une même configuration.
- Conserver la date, la source et la version des données dans les sorties finales.
