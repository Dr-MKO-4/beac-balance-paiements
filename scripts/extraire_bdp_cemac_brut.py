# -*- coding: utf-8 -*-
"""
Extraction robuste des soldes Biens / Services / Revenu primaire depuis les
fichiers BDP analytiques bruts de la BEAC (2020-2023, 6 pays CEMAC), et
calcul du taux de retention (TRE) selon la methodologie validee dans
rapport_bdp.tex : TC, TAS, TFR, TRE = 100 - TAS - TFR.

Les fichiers sources sont heterogenes (plusieurs feuilles par classeur,
parfois un pays different de celui du nom de fichier -- ex. une feuille
"NEW_MODEL_1" du classeur Congo contient en realite des donnees du Tchad).
On identifie donc le pays et l'annee a partir du texte reel de l'entete de
chaque feuille, jamais du nom de fichier.
"""
import glob
import os
import re
import unicodedata

import pandas as pd

DIR = os.path.dirname(os.path.abspath(__file__)) + r'\..\data\2020-2023-CEMAC'

PAYS_PATTERNS = {
    'Cameroun': r'cameroun',
    'Congo': r'congo',
    'Gabon': r'gabon',
    'Guinee_Eq': r'guin[ée]e[\s-]*[ée]quatoriale',
    'RCA': r'centrafricaine|r[ée]publique centrafricaine',
    'Tchad': r'tchad',
}


def norm(s):
    if not isinstance(s, str):
        return ''
    s = unicodedata.normalize('NFKD', s)
    s = ''.join(c for c in s if not unicodedata.combining(c))
    return s.lower().strip()


def identifier_pays_annee(df):
    """Cherche dans les 15 premieres lignes/colonnes le pays et l'annee."""
    texte = ' '.join(
        str(v) for v in df.iloc[:15, :3].values.flatten() if isinstance(v, str)
    )
    texte_n = norm(texte)
    pays = None
    for nom, pattern in PAYS_PATTERNS.items():
        if re.search(pattern, texte_n):
            pays = nom
            break
    m = re.search(r'exercice\s+(\d{4})', texte_n)
    annee = m.group(1) if m else None
    return pays, annee


def trouver_colonnes(df):
    """Trouve la ligne d'entete (Libelle/Credit/Debit) et les indices de colonnes."""
    for i in range(20):
        row = df.iloc[i].astype(str).map(norm)
        if any('libelle' in v for v in row):
            libelle_col = next(j for j, v in row.items() if 'libelle' in v)
            credit_col = next((j for j, v in row.items() if v == 'credit'), None)
            debit_col = next((j for j, v in row.items() if v == 'debit'), None)
            if credit_col is not None and debit_col is not None:
                return i, libelle_col, credit_col, debit_col
    return None


def extraire_poste(df, libelle_col, credit_col, debit_col, cible):
    """Recherche un libelle EXACT (apres normalisation) dans la colonne libelle."""
    col = df[libelle_col].astype(str).map(norm)
    cible_n = norm(cible)
    matches = df.index[col == cible_n]
    if len(matches) == 0:
        return None
    idx = matches[0]
    try:
        credit = float(df.at[idx, credit_col])
        debit = float(df.at[idx, debit_col])
    except (ValueError, TypeError):
        return None
    return credit, debit


resultats = []
fichiers = sorted(set(glob.glob(os.path.join(DIR, '*.xlsx'))))
vus = set()  # (pays, annee) deja extraits -> on garde la premiere occurrence propre

for fpath in fichiers:
    fname = os.path.basename(fpath)
    try:
        xl = pd.ExcelFile(fpath, engine='openpyxl')
    except Exception as e:
        print(f"!! Impossible d'ouvrir {fname}: {e}")
        continue
    for sheet in xl.sheet_names:
        try:
            df = xl.parse(sheet, header=None)
        except Exception:
            continue
        pays, annee = identifier_pays_annee(df)
        if not pays or not annee:
            continue
        key = (pays, annee)
        if key in vus:
            continue
        cols = trouver_colonnes(df)
        if not cols:
            continue
        _, lib_col, cred_col, deb_col = cols

        biens = extraire_poste(df, lib_col, cred_col, deb_col, 'Biens')
        services = extraire_poste(df, lib_col, cred_col, deb_col, 'Services')
        revenu_prim = extraire_poste(df, lib_col, cred_col, deb_col, 'Revenu primaire')
        compte_courant = extraire_poste(df, lib_col, cred_col, deb_col,
                                         'COMPTE DES TRANSACTIONS COURANTES')

        if not (biens and services and revenu_prim):
            continue

        exp_biens, imp_biens = biens
        if pd.isna(exp_biens) or pd.isna(imp_biens) or exp_biens <= 0:
            continue
        cred_s, deb_s = services
        solde_services = cred_s - deb_s
        cred_r, deb_r = revenu_prim
        solde_revenu = cred_r - deb_r

        tc = exp_biens / imp_biens if imp_biens else None
        tas = max(0.0, -solde_services) / exp_biens * 100
        tfr = max(0.0, -solde_revenu) / exp_biens * 100
        tre = 100 - tas - tfr

        vus.add(key)
        resultats.append({
            'pays': pays, 'annee': annee, 'fichier': fname, 'feuille': sheet,
            'exp_biens': exp_biens, 'imp_biens': imp_biens,
            'solde_services': solde_services, 'solde_revenu_primaire': solde_revenu,
            'solde_courant': (compte_courant[0] - compte_courant[1]) if compte_courant else None,
            'tc': round(tc, 2) if tc else None,
            'tas': round(tas, 1), 'tfr': round(tfr, 1), 'tre': round(tre, 1),
        })


# Cas particulier : Cameroun (feuille trimestrielle 1T/2T/3T/4T + annuel) ---
import re as _re

def extraire_cameroun(fpath):
    xl = pd.ExcelFile(fpath, engine='openpyxl')
    sheet = xl.sheet_names[0]
    df = xl.parse(sheet, header=None)
    # Ligne des libelles de blocs trimestriels (ex: 'BDP 2021' = colonne annuelle)
    for i in range(12):
        row = df.iloc[i].astype(str)
        annuel_cols = [j for j, v in row.items() if _re.fullmatch(r'BDP\s+\d{4}', v.strip())]
        if annuel_cols:
            credit_col = annuel_cols[0]
            debit_col = annuel_cols[0] + 1
            annee = _re.search(r'\d{4}', row[annuel_cols[0]]).group()
            header_row = i + 1
            break
    else:
        return None
    libelle_col = 1
    col_norm = df[libelle_col].astype(str).map(norm)

    def get(label):
        idx = df.index[col_norm == norm(label)]
        if len(idx) == 0:
            return None
        idx = idx[0]
        try:
            return float(df.at[idx, credit_col]), float(df.at[idx, debit_col])
        except (ValueError, TypeError):
            return None

    biens = get('Biens')
    services = get('Services')
    revenu_prim = get('Revenu primaire') or get('Revenus primaires')
    cc = get('COMPTE DES TRANSACTIONS COURANTES')
    if not (biens and services and revenu_prim):
        return None
    exp_biens, imp_biens = biens
    if pd.isna(exp_biens) or exp_biens <= 0:
        return None
    solde_services = services[0] - services[1]
    solde_revenu = revenu_prim[0] - revenu_prim[1]
    tc = exp_biens / imp_biens if imp_biens else None
    tas = max(0.0, -solde_services) / exp_biens * 100
    tfr = max(0.0, -solde_revenu) / exp_biens * 100
    tre = 100 - tas - tfr
    return {
        'pays': 'Cameroun', 'annee': annee, 'fichier': os.path.basename(fpath), 'feuille': sheet,
        'exp_biens': exp_biens, 'imp_biens': imp_biens,
        'solde_services': solde_services, 'solde_revenu_primaire': solde_revenu,
        'solde_courant': (cc[0] - cc[1]) if cc else None,
        'tc': round(tc, 2) if tc else None,
        'tas': round(tas, 1), 'tfr': round(tfr, 1), 'tre': round(tre, 1),
    }


for fpath in glob.glob(os.path.join(DIR, 'Balance-des-Paiments-Analytique-*-Cameroun.xlsx')):
    r = extraire_cameroun(fpath)
    if r:
        resultats.append(r)

resultats.sort(key=lambda r: (r['pays'], r['annee']))
out = pd.DataFrame(resultats)
out.to_csv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'TRE_CEMAC_RECALCULE.csv'), index=False, encoding='utf-8-sig')
print(out[['pays', 'annee', 'fichier', 'feuille', 'exp_biens', 'tc', 'tas', 'tfr', 'tre', 'solde_courant']].to_string(index=False))
print()
print(f"Total : {len(out)} couples pays-annee extraits sur {len(fichiers)} fichiers.")
