# -*- coding: utf-8 -*-
"""
Analyse complete du taux de retention (TRE) -- panel mondial d'exportateurs
de petrole (source brute FMI, 6 annees cibles) + positionnement de la
CEMAC (Cameroun : source FMI brute, referent international ET membre de la
CEMAC ; Congo/Gabon/Guinee_Eq/Tchad/RCA : source BEAC officielle, seule
disponible pour ces pays faute de couverture FMI suffisante sur les annees
cibles -- limite documentee, non un choix arbitraire).

Historique des corrections methodologiques (voir conversation) :
  1) Un k-means unique sur tout le panel donnait des seuils ecrases par les
     pays structurellement importateurs nets de biens (TM>100%, dont le
     Cameroun) -- un ecart de -34,8% au lieu d'un veritable signal de fuite
     de rente.
  2) Separer le panel en 2 profils (excedentaire/deficitaire en biens) a
     corrige l'echelle relative, mais le probleme restait que le k-means
     etiquette toujours un "meilleur tiers" comme BON, meme quand ce tiers
     n'est pas bon en absolu (ex. Guinee Eq. a 6,4% etiquete BON).
  3) Correction definitive : abandon du calibrage relatif (k-means) au
     profit de SEUILS ABSOLUS, fixes independamment de l'echantillon :
       CRITIQUE : TRE < 0%   (le pays perd plus que la totalite de la
                  valeur exportee de biens -- fuite nette)
       FAIBLE   : 0% <= TRE < 20%
       NORMAL   : 20% <= TRE < 50%
       BON      : TRE >= 50% (au moins la moitie de la valeur exportee
                  reste dans le pays)
     Sur les 240 observations pays-annee du panel mondial, seules 3
     (Koweit/Qatar/Brunei, 2014 uniquement) atteignent BON -- resultat
     substantiel (la retention forte et durable est rarissime meme chez
     les meilleurs exportateurs), pas un artefact.
  4) Classification ANNEE PAR ANNEE, pas sur une mediane multi-annees : les
     6 annees cibles (2014, 2015, 2016, 2019, 2020, 2021) sont des
     snapshots deliberement choisis autour de deux chocs (petrolier
     2015-2016, COVID 2019-2021) ; les reduire a une mediane efface
     exactement la dynamique que l'etude cherche a observer. La notion de
     "profil excedentaire/deficitaire" (utile seulement pour un calibrage
     relatif) disparait avec les seuils absolus : plus besoin de separer
     les pays en 2 groupes, tous sont classes directement sur leur propre
     valeur, annee par annee.

Ajoute par rapport a extraire_tre_brut_fmi.py :
  - les soldes principaux de la balance des paiements (biens, services,
    revenu primaire, et un solde courant partiel = somme des trois,
    explicitement hors revenu secondaire/transferts courants, indicateur
    FMI brut non valide ici -- cf. verification D2 = 0 pour le Cameroun,
    valeur implausible) ;
  - le recalcul, avec la formule complete (TM inclus), des 5 pays CEMAC
    disponibles uniquement via les fichiers BEAC bruts, a partir des
    composantes deja extraites et validees dans data/TRE_CEMAC_RECALCULE.csv
    -- sans toucher au script d'extraction original ;
  - la production de graphiques (figures/ du projet) pour interpretation.

Ce script ne modifie aucun script existant ; il importe uniquement les
fonctions de calcul d'extraire_tre_brut_fmi.py.
"""
import csv
import os

import matplotlib.pyplot as plt
import numpy as np

from extraire_tre_brut_fmi import ANNEES_CIBLES, PANEL_MONDIAL, calculer_tre, extraire_pays

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data')
FIG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'figures')

SEUILS_ABSOLUS = {'CRITIQUE': (-np.inf, 0), 'FAIBLE': (0, 20), 'NORMAL': (20, 50), 'BON': (50, np.inf)}
ORDRE_BANDES = ['CRITIQUE', 'FAIBLE', 'NORMAL', 'BON']
COULEURS_BANDE = {'CRITIQUE': '#7b241c', 'FAIBLE': '#c0392b', 'NORMAL': '#e67e22', 'BON': '#27ae60'}


def bande(t):
    if t < 0:
        return 'CRITIQUE'
    if t < 20:
        return 'FAIBLE'
    if t < 50:
        return 'NORMAL'
    return 'BON'


def extraire_pays_avec_soldes(code):
    """Comme extraire_pays, mais renvoie aussi les soldes bruts (M USD) et la bande annuelle."""
    data = extraire_pays(code)
    out = {}
    for annee, (cb, db, cs, ds, cr, dr) in data.items():
        r = calculer_tre(cb, db, cs, ds, cr, dr)
        if r is None:
            continue
        solde_biens = cb - db
        solde_services = cs - ds
        solde_revenu_primaire = cr - dr
        solde_courant_partiel = solde_biens + solde_services + solde_revenu_primaire
        out[annee] = {
            **r,
            'bande': bande(r['tre']),
            'solde_biens': solde_biens,
            'solde_services': solde_services,
            'solde_revenu_primaire': solde_revenu_primaire,
            'solde_courant_partiel': solde_courant_partiel,
        }
    return out


def construire_panel_mondial():
    records = []
    for code, label in PANEL_MONDIAL.items():
        data = extraire_pays_avec_soldes(code)
        if len(data) != len(ANNEES_CIBLES):
            continue
        records.append({'code': code, 'label': label, 'par_annee': data})
    return records


def charger_cemac_beac():
    """Recalcule TM/TRE pour Congo/Gabon/Guinee_Eq/Tchad/RCA depuis les
    composantes brutes deja extraites dans TRE_CEMAC_RECALCULE.csv
    (fichiers BDP officiels BEAC), sans toucher au script d'origine."""
    path = os.path.join(DATA_DIR, 'TRE_CEMAC_RECALCULE.csv')
    rows = list(csv.DictReader(open(path, encoding='utf-8-sig')))
    out = {}  # label -> {annee: {...}}
    for r in rows:
        label = r['pays']
        if label == 'Cameroun':
            continue  # Cameroun vient de la source FMI (plus d'annees)
        exp_b = float(r['exp_biens'])
        imp_b = float(r['imp_biens'])
        solde_s = float(r['solde_services'])
        solde_r = float(r['solde_revenu_primaire'])
        tm = imp_b / exp_b * 100 if exp_b else None
        tas = max(0.0, -solde_s) / exp_b * 100 if exp_b else None
        tfr = max(0.0, -solde_r) / exp_b * 100 if exp_b else None
        if None in (tm, tas, tfr):
            continue
        tre = 100 - tm - tas - tfr
        out.setdefault(label, {})[r['annee']] = {
            'tm': tm, 'tas': tas, 'tfr': tfr, 'tre': tre, 'bande': bande(tre),
            'solde_biens': exp_b - imp_b,
            'solde_services': solde_s,
            'solde_revenu_primaire': solde_r,
            'solde_courant_partiel': (exp_b - imp_b) + solde_s + solde_r,
        }
    return out


if __name__ == '__main__':
    os.makedirs(FIG_DIR, exist_ok=True)

    # 1) Panel mondial (40 pays, 6 annees cibles), classe annee par annee ---
    panel = construire_panel_mondial()

    toutes_obs = [(r['label'], a, r['par_annee'][a]['tre'], r['par_annee'][a]['bande'])
                  for r in panel for a in ANNEES_CIBLES]
    n = len(toutes_obs)
    compte_bandes = {b: sum(1 for *_, bb in toutes_obs if bb == b) for b in ORDRE_BANDES}
    print(f"Panel mondial : {len(panel)} pays x {len(ANNEES_CIBLES)} annees = {n} observations pays-annee")
    for b in ORDRE_BANDES:
        print(f"  {b:10s} : {compte_bandes[b]:3d} ({compte_bandes[b]/n*100:4.1f}%)")
    print()
    print("Observations en bande BON (TRE >= 50%) :")
    for label, a, t, b in sorted(toutes_obs, key=lambda x: -x[2]):
        if b == 'BON':
            print(f"  {label} {a} : {t:.1f}%")

    # 2) CEMAC : Cameroun (FMI, deja dans panel) + 5 autres (BEAC), annee par annee ---
    cemac_beac = charger_cemac_beac()
    cemac_tout = {}
    cam = next(r for r in panel if r['code'] == 'CMR')
    cemac_tout['Cameroun'] = {'par_annee': cam['par_annee'], 'source': 'FMI (6 annees cibles)'}
    for label, par_annee in cemac_beac.items():
        cemac_tout[label] = {'par_annee': par_annee,
                              'source': f"BEAC ({','.join(sorted(par_annee.keys()))})"}

    print()
    print("=== Positionnement CEMAC, annee par annee (seuils absolus) ===")
    for label, d in cemac_tout.items():
        print(f"{label} [{d['source']}]:")
        for a in sorted(d['par_annee'].keys()):
            v = d['par_annee'][a]
            print(f"  {a}: TRE={v['tre']:7.1f}%  {v['bande']}")

    # 3) Graphique 1 : heatmap pays x annee (panel mondial + CEMAC) ---
    bande_idx = {b: i for i, b in enumerate(ORDRE_BANDES)}
    tous_labels = [r['label'] for r in panel] + list(cemac_tout.keys())
    tous_par_annee = {r['label']: r['par_annee'] for r in panel}
    tous_par_annee.update({l: d['par_annee'] for l, d in cemac_tout.items()})
    # tri par TRE 2021 (ou derniere annee dispo) decroissant
    def cle_tri(label):
        pa = tous_par_annee[label]
        for a in reversed(ANNEES_CIBLES):
            if a in pa:
                return -pa[a]['tre']
        return 0
    tous_labels.sort(key=cle_tri)

    mat = np.full((len(tous_labels), len(ANNEES_CIBLES)), np.nan)
    for i, label in enumerate(tous_labels):
        pa = tous_par_annee[label]
        for j, a in enumerate(ANNEES_CIBLES):
            if a in pa:
                mat[i, j] = bande_idx[pa[a]['bande']]

    from matplotlib.colors import ListedColormap
    cmap = ListedColormap([COULEURS_BANDE[b] for b in ORDRE_BANDES])
    fig, ax = plt.subplots(figsize=(7, 13))
    ax.imshow(mat, aspect='auto', cmap=cmap, vmin=-0.5, vmax=3.5)
    ax.set_xticks(range(len(ANNEES_CIBLES)))
    ax.set_xticklabels(ANNEES_CIBLES)
    ax.set_yticks(range(len(tous_labels)))
    ax.set_yticklabels([f"* {l}" if l in cemac_tout else l for l in tous_labels], fontsize=7)
    ax.set_title("Bande de retention par pays et par annee\n(seuils absolus : CRITIQUE<0% / FAIBLE 0-20% / NORMAL 20-50% / BON>=50% ; * = CEMAC)")
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(color=COULEURS_BANDE[b], label=b) for b in ORDRE_BANDES],
               loc='upper center', bbox_to_anchor=(0.5, -0.03), ncol=4, fontsize=8)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG_DIR, 'tre_typologie_mondiale.pdf'))
    plt.close(fig)

    # 4) Graphique 2 : trajectoire 2014-2021, CEMAC + reperes mondiaux ---
    reperes = ['Qatar', 'Koweit', 'Norvege', 'Russie', 'Royaume-Uni', 'Nigeria']
    fig, ax = plt.subplots(figsize=(10, 6.5))
    for label in reperes:
        r = next(r for r in panel if r['label'] == label)
        ys = [r['par_annee'][a]['tre'] for a in ANNEES_CIBLES]
        ax.plot(ANNEES_CIBLES, ys, linestyle='--', alpha=0.5, label=f"{label} (repere mondial)")
    for label, d in cemac_tout.items():
        annees_dispo = [a for a in ANNEES_CIBLES if a in d['par_annee']]
        ys = [d['par_annee'][a]['tre'] for a in annees_dispo]
        ax.plot(annees_dispo, ys, marker='o', linewidth=2.2, label=f"{label} (CEMAC)")
    for seuil in (0, 20, 50):
        ax.axhline(seuil, color='gray', linestyle=':', linewidth=0.8)
    ax.set_ylabel("Taux de retention (%)")
    ax.set_title("Trajectoire du taux de retention -- CEMAC vs reperes mondiaux\n(choc petrolier 2014-2016, choc COVID 2019-2021 ; lignes grises = seuils 0/20/50%)")
    ax.legend(fontsize=7.5, loc='best', ncol=2)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG_DIR, 'tre_trajectoire_cemac.pdf'))
    plt.close(fig)

    # 5) Graphique 3 : composition du compte courant (soldes), CEMAC, derniere annee dispo ---
    fig, ax = plt.subplots(figsize=(9, 5.5))
    pays_ordre = list(cemac_tout.keys())
    derniere = {}
    for label, d in cemac_tout.items():
        annees_dispo = sorted(d['par_annee'].keys())
        derniere[label] = d['par_annee'][annees_dispo[-1]]
    x = np.arange(len(pays_ordre))
    sb = [derniere[p]['solde_biens'] for p in pays_ordre]
    ss = [derniere[p]['solde_services'] for p in pays_ordre]
    sr = [derniere[p]['solde_revenu_primaire'] for p in pays_ordre]
    ax.bar(x, sb, label='Solde biens', color='#2980b9')
    ax.bar(x, ss, bottom=sb, label='Solde services', color='#e67e22')
    bottom2 = [a + b for a, b in zip(sb, ss)]
    ax.bar(x, sr, bottom=bottom2, label='Solde revenu primaire', color='#8e44ad')
    ax.axhline(0, color='black', linewidth=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels([f"{p}\n({sorted(cemac_tout[p]['par_annee'].keys())[-1]})" for p in pays_ordre], fontsize=8)
    ax.set_ylabel("Millions USD")
    ax.set_title("Composition du compte courant (hors revenu secondaire) -- CEMAC, derniere annee disponible")
    ax.legend()
    fig.tight_layout()
    fig.savefig(os.path.join(FIG_DIR, 'soldes_cemac_composition.pdf'))
    plt.close(fig)

    print()
    print(f"Graphiques enregistres dans {FIG_DIR} :")
    print(" - tre_typologie_mondiale.pdf (heatmap pays x annee)")
    print(" - tre_trajectoire_cemac.pdf")
    print(" - soldes_cemac_composition.pdf")
