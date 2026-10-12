# -*- coding: utf-8 -*-
"""
Calcul du taux de retention (TRE) pour le panel mondial d'exportateurs de
petrole, a partir des fichiers sources bruts FMI (data/brut_fmi/BOP_<CODE>.csv,
format SDMX IMF.STA:BOP), sur les 6 annees cibles de l'etude (2014, 2015,
2016, 2019, 2020, 2021 -- choc petrolier 2015-2016 et choc COVID 2019-2021,
cf. archive/methode.tex).

Codes indicateurs confirmes par comparaison directe aux donnees BEAC
validees du Cameroun (ecart ~1,5-1,8%, coherent avec une difference de
millesime FMI/BEAC) :
  G   = Biens (Goods)
  S   = Services
  IN1 = Revenu primaire (Primary income)
  CD_T = Credit, DB_T = Debit ; valeurs en USD (SCALE=6, deja en unites),
  converties en millions de USD (/1e6) pour coherence avec le reste du projet.

Formule complete (validee sur TABLEAU3_DIAGNOSTIC_CEMAC_BEAC.csv, Tchad/
Congo/Gabon 2021) :
  TC  = Credit biens / Debit biens x 100
  TM  = Debit biens / Credit biens x 100
  TAS = max(0, -solde services) / Credit biens x 100
  TFR = max(0, -solde revenu primaire) / Credit biens x 100
  TRE = 100 - TM - TAS - TFR

Panel : 43 pays candidats (42 d'origine moins Albanie/Roumanie/Turquie,
hors top 50 mondial des exportateurs de petrole, plus Emirats arabes
unis/Iran/Venezuela/Soudan, presents dans ce top 50). Verification de
couverture faite au prealable (verifier_couverture_brut_fmi.py) : 40 pays
ont les 3 indicateurs (credit+debit) sur les 6 annees cibles ; Emirats
arabes unis et Iran n'ont aucune donnee sur ces indicateurs dans ce fichier,
le Venezuela n'est couvert que 2014-2016. Ces 3 pays sont donc exclus ici,
pour une raison de couverture documentee et verifiee, non par filtre
arbitraire sur le resultat.

La CEMAC (Cameroun inclus) est positionnee a part, en fin d'etude, par
rapport a la typologie batie sur ce panel mondial -- elle n'est pas un
groupe "exclu", mais le sujet final de la comparaison.

Ce script N'EST PAS EXECUTE AUTOMATIQUEMENT.
"""
import csv
import os
import statistics

import numpy as np
from sklearn.cluster import KMeans

ANNEES_CIBLES = ['2014', '2015', '2016', '2019', '2020', '2021']

PANEL_MONDIAL = {
    'AGO': 'Angola', 'ARG': 'Argentine', 'AUS': 'Australie', 'AZE': 'Azerbaidjan',
    'BOL': 'Bolivie', 'BRA': 'Bresil', 'BRN': 'Brunei', 'CAN': 'Canada',
    'CHN': 'Chine', 'CMR': 'Cameroun', 'COL': 'Colombie', 'DNK': 'Danemark',
    'DZA': 'Algerie', 'ECU': 'Equateur', 'EGY': 'Egypte', 'GBR': 'Royaume-Uni',
    'GHA': 'Ghana', 'GUY': 'Guyana', 'IDN': 'Indonesie', 'IRQ': 'Irak',
    'ITA': 'Italie', 'KAZ': 'Kazakhstan', 'KWT': 'Koweit', 'LBY': 'Libye',
    'MEX': 'Mexique', 'MYS': 'Malaisie', 'NGA': 'Nigeria', 'NLD': 'Pays-Bas',
    'NOR': 'Norvege', 'OMN': 'Oman', 'PER': 'Perou', 'QAT': 'Qatar',
    'RUS': 'Russie', 'SAU': 'Arabie saoudite', 'SDN': 'Soudan',
    'SSD': 'Soudan du Sud', 'TTO': 'Trinite-et-Tobago', 'TUN': 'Tunisie',
    'USA': 'Etats-Unis', 'VNM': 'Vietnam',
}  # 40 pays -- Cameroun est le referent international ET membre de la CEMAC :
   # il figure dans le panel de calibrage mondial ET dans le positionnement
   # CEMAC final ci-dessous.

CEMAC = {
    'CMR': 'Cameroun', 'COG': 'Congo', 'GAB': 'Gabon',
    'GNQ': 'Guinee_Eq', 'TCD': 'Tchad', 'CAF': 'RCA',
}

DIR = os.path.dirname(os.path.abspath(__file__)) + r'\..\data\brut_fmi'


def extraire_pays(code):
    """Retourne {annee: (credit_biens, debit_biens, credit_services,
    debit_services, credit_revenu, debit_revenu)} en millions USD."""
    fpath = os.path.join(DIR, f'BOP_{code}.csv')
    if not os.path.exists(fpath):
        return {}
    valeurs = {}  # (indicateur, annee, entry) -> valeur
    with open(fpath, encoding='utf-8-sig') as f:
        reader = csv.reader(f)
        header = next(reader)
        idx = {h: i for i, h in enumerate(header)}
        for r in reader:
            ind = r[idx['INDICATOR']]
            if ind not in ('G', 'S', 'IN1'):
                continue
            annee = r[idx['TIME_PERIOD']]
            if annee not in ANNEES_CIBLES:
                continue
            entry = r[idx['BOP_ACCOUNTING_ENTRY']]
            if entry not in ('CD_T', 'DB_T'):
                continue
            try:
                val = float(r[idx['OBS_VALUE']]) / 1e6  # USD -> millions USD
            except ValueError:
                continue
            valeurs[(ind, annee, entry)] = val

    resultat = {}
    for annee in ANNEES_CIBLES:
        try:
            cb = valeurs[('G', annee, 'CD_T')]
            db = valeurs[('G', annee, 'DB_T')]
            cs = valeurs[('S', annee, 'CD_T')]
            ds = valeurs[('S', annee, 'DB_T')]
            cr = valeurs[('IN1', annee, 'CD_T')]
            dr = valeurs[('IN1', annee, 'DB_T')]
        except KeyError:
            continue
        resultat[annee] = (cb, db, cs, ds, cr, dr)
    return resultat


def calculer_tre(cb, db, cs, ds, cr, dr):
    tc = cb / db * 100 if db else None
    tm = db / cb * 100 if cb else None
    solde_s = cs - ds
    solde_r = cr - dr
    tas = max(0.0, -solde_s) / cb * 100 if cb else None
    tfr = max(0.0, -solde_r) / cb * 100 if cb else None
    if None in (tm, tas, tfr):
        return None
    tre = 100 - tm - tas - tfr
    return {'tc': tc, 'tm': tm, 'tas': tas, 'tfr': tfr, 'tre': tre}


def construire_panel(codes_labels):
    records = []
    for code, label in codes_labels.items():
        data = extraire_pays(code)
        tres = {}
        for annee, vals in data.items():
            r = calculer_tre(*vals)
            if r is not None:
                tres[annee] = r['tre']
        if len(tres) == len(ANNEES_CIBLES):
            records.append({'code': code, 'label': label, 'tre_par_annee': tres})
    return records


if __name__ == '__main__':
    records = construire_panel(PANEL_MONDIAL)
    print(f"Pays a couverture complete sur les 6 annees cibles : {len(records)}/{len(PANEL_MONDIAL)}")
    print()

    for r in records:
        tre_vals = [r['tre_par_annee'][a] for a in ANNEES_CIBLES]
        r['tre_med'] = statistics.median(tre_vals)
        early = [r['tre_par_annee'][a] for a in ('2014', '2015', '2016')]
        late = [r['tre_par_annee'][a] for a in ('2019', '2020', '2021')]
        r['tre_early'] = statistics.median(early)
        r['tre_late'] = statistics.median(late)

    X = np.array([[r['tre_med']] for r in records])
    km = KMeans(n_clusters=3, n_init=10, random_state=42).fit(X)
    centres = sorted(km.cluster_centers_.flatten())
    order = np.argsort(km.cluster_centers_.flatten())
    remap = {old: new for new, old in enumerate(order)}
    NOMS = {0: 'FAIBLE', 1: 'NORMAL', 2: 'BON'}
    for r, lab in zip(records, km.labels_):
        r['groupe'] = NOMS[remap[lab]]

    records.sort(key=lambda r: r['tre_med'])
    print(f"{'Pays':20s} {'2014':>7s} {'2015':>7s} {'2016':>7s} {'2019':>7s} {'2020':>7s} {'2021':>7s} {'Median':>8s} {'Groupe':>8s}  Trajectoire")
    for r in records:
        vals = [f"{r['tre_par_annee'][a]:7.1f}" for a in ANNEES_CIBLES]
        delta = r['tre_late'] - r['tre_early']
        traj = f"{delta:+.0f} pts"
        print(f"{r['label']:20s} " + ' '.join(vals) + f" {r['tre_med']:8.1f} {r['groupe']:>8s}  {traj}")

    print()
    print(f"Seuils de cluster (centres k-means) : {[round(c, 1) for c in centres]}")

    print()
    print("=== Positionnement CEMAC (hors panel de calibrage) ===")
    cemac_records = construire_panel(CEMAC)
    for r in cemac_records:
        tre_vals = [r['tre_par_annee'][a] for a in ANNEES_CIBLES]
        r['tre_med'] = statistics.median(tre_vals)
        t = r['tre_med']
        if t < (centres[0] + centres[1]) / 2:
            groupe = 'FAIBLE'
        elif t < (centres[1] + centres[2]) / 2:
            groupe = 'NORMAL'
        else:
            groupe = 'BON'
        vals = [f"{r['tre_par_annee'][a]:7.1f}" for a in ANNEES_CIBLES]
        print(f"{r['label']:20s} " + ' '.join(vals) + f" {r['tre_med']:8.1f} {groupe:>8s}")
