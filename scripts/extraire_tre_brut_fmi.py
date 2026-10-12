# -*- coding: utf-8 -*-
"""Données, indicateurs et bandes de l'analyse du taux de rétention.

Sources
    FMI : data/brut_fmi/BOP_<ISO3>.csv, export SDMX du jeu IMF.STA:BOP.
          Codes utilisés : G (biens), S (services), IN1 (revenu primaire),
          CD_T (crédit), DB_T (débit). Valeurs en USD.
    BEAC : data/TRE_CEMAC_RECALCULE.csv, produit par extraire_bdp_cemac_brut.py
          à partir des fichiers BDP analytiques officiels (2020 à 2023).

Panel mondial : les pays du top 50 mondial des exportateurs de pétrole dont
les trois postes sont renseignés, en crédit et en débit, sur les six années
cibles (41 pays, dont le Cameroun et le Congo).
"""
import csv
import os

ANNEES_CIBLES = ['2014', '2015', '2016', '2019', '2020', '2021']

PANEL_MONDIAL = {
    'AGO': 'Angola', 'ARG': 'Argentine', 'AUS': 'Australie', 'AZE': 'Azerbaïdjan',
    'BOL': 'Bolivie', 'BRA': 'Brésil', 'BRN': 'Brunei', 'CAN': 'Canada',
    'CHN': 'Chine', 'CMR': 'Cameroun', 'COG': 'Congo', 'COL': 'Colombie',
    'DNK': 'Danemark', 'DZA': 'Algérie', 'ECU': 'Équateur', 'EGY': 'Égypte',
    'GBR': 'Royaume-Uni', 'GHA': 'Ghana', 'GUY': 'Guyana', 'IDN': 'Indonésie',
    'IRQ': 'Irak', 'ITA': 'Italie', 'KAZ': 'Kazakhstan', 'KWT': 'Koweït',
    'LBY': 'Libye', 'MEX': 'Mexique', 'MYS': 'Malaisie', 'NGA': 'Nigeria',
    'NLD': 'Pays-Bas', 'NOR': 'Norvège', 'OMN': 'Oman', 'PER': 'Pérou',
    'QAT': 'Qatar', 'RUS': 'Russie', 'SAU': 'Arabie saoudite', 'SDN': 'Soudan',
    'SSD': 'Soudan du Sud', 'TTO': 'Trinité-et-Tobago', 'TUN': 'Tunisie',
    'USA': 'États-Unis', 'VNM': 'Vietnam',
}

CEMAC = {
    'CMR': 'Cameroun', 'COG': 'Congo', 'GAB': 'Gabon',
    'GNQ': 'Guinée Équatoriale', 'TCD': 'Tchad', 'CAF': 'RCA',
}
NOMS_BEAC = {'Cameroun': 'CMR', 'Congo': 'COG', 'Gabon': 'GAB',
             'Guinee_Eq': 'GNQ', 'Tchad': 'TCD', 'RCA': 'CAF'}

# Bandes de rétention : 0 est fixé par définition (fuites = exportations) ;
# -78, 16 et 35 sont les ruptures naturelles mesurées séparément sur les
# observations négatives et sur les observations positives du panel.
SEUILS = [('TRÈS CRITIQUE', -78.0), ('CRITIQUE', 0.0), ('FAIBLE', 16.0),
          ('NORMAL', 35.0), ('BON', float('inf'))]
BANDES = [nom for nom, _ in SEUILS]

RACINE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
DOSSIER_FMI = os.path.join(RACINE, 'data', 'brut_fmi')
FICHIER_BEAC = os.path.join(RACINE, 'data', 'TRE_CEMAC_RECALCULE.csv')


def bande(tre):
    for nom, borne_sup in SEUILS:
        if tre < borne_sup:
            return nom
    return 'BON'


def indicateurs(credit_biens, debit_biens, solde_services, solde_revenu):
    """Taux de couverture, taux de fuite et taux de rétention (en %)."""
    tm = debit_biens / credit_biens * 100
    tas = max(0.0, -solde_services) / credit_biens * 100
    tfr = max(0.0, -solde_revenu) / credit_biens * 100
    tre = 100 - tm - tas - tfr
    return {'tc': credit_biens / debit_biens * 100, 'tm': tm, 'tas': tas,
            'tfr': tfr, 'tre': tre, 'bande': bande(tre),
            'solde_biens': credit_biens - debit_biens,
            'solde_services': solde_services, 'solde_revenu': solde_revenu}


def extraire_pays(code):
    """{année: indicateurs} pour un pays, depuis l'export FMI brut."""
    chemin = os.path.join(DOSSIER_FMI, f'BOP_{code}.csv')
    if not os.path.exists(chemin):
        return {}
    v = {}
    # errors='replace' : un octet isolé illisible dans les métadonnées ne doit pas bloquer la lecture
    with open(chemin, encoding='utf-8-sig', errors='replace') as f:
        lecteur = csv.reader(f)
        i = {nom: k for k, nom in enumerate(next(lecteur))}
        for r in lecteur:
            if (r[i['INDICATOR']] in ('G', 'S', 'IN1')
                    and r[i['BOP_ACCOUNTING_ENTRY']] in ('CD_T', 'DB_T')
                    and r[i['TIME_PERIOD']] in ANNEES_CIBLES):
                try:
                    v[(r[i['INDICATOR']], r[i['BOP_ACCOUNTING_ENTRY']], r[i['TIME_PERIOD']])] = \
                        float(r[i['OBS_VALUE']]) / 1e6
                except ValueError:
                    pass
    resultat = {}
    for a in ANNEES_CIBLES:
        try:
            cb, db = v[('G', 'CD_T', a)], v[('G', 'DB_T', a)]
            ss = v[('S', 'CD_T', a)] - v[('S', 'DB_T', a)]
            sr = v[('IN1', 'CD_T', a)] - v[('IN1', 'DB_T', a)]
        except KeyError:
            continue
        resultat[a] = {**indicateurs(cb, db, ss, sr), 'source': 'FMI'}
    return resultat


def charger_panel_mondial():
    """{code: {année: indicateurs}} pour les pays couverts sur les 6 années."""
    panel = {}
    for code in PANEL_MONDIAL:
        donnees = extraire_pays(code)
        if len(donnees) == len(ANNEES_CIBLES):
            panel[code] = donnees
    return panel


def charger_cemac():
    """{code: {année: indicateurs}} pour les 6 pays CEMAC, années cibles.

    Source FMI en priorité ; à défaut, fichiers BDP officiels de la BEAC.
    """
    beac = {}
    with open(FICHIER_BEAC, encoding='utf-8-sig') as f:
        for r in csv.DictReader(f):
            code = NOMS_BEAC[r['pays']]
            if r['annee'] in ANNEES_CIBLES:
                beac.setdefault(code, {})[r['annee']] = {
                    **indicateurs(float(r['exp_biens']), float(r['imp_biens']),
                                  float(r['solde_services']), float(r['solde_revenu_primaire'])),
                    'source': 'BEAC'}
    cemac = {}
    for code in CEMAC:
        donnees = dict(beac.get(code, {}))
        donnees.update(extraire_pays(code))
        cemac[code] = donnees
    return cemac
