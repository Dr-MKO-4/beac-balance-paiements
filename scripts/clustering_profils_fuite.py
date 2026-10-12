# -*- coding: utf-8 -*-
"""Profils de fuite : par quel canal la valeur exportée quitte-t-elle le pays ?

Variables : TM, TAS, TFR (les trois canaux dont la somme vaut 100 - TRE).
TC n'est pas retenu car il porte la même information que TM (TM = 10 000 / TC).
Les valeurs extrêmes sont écrêtées aux centiles 2,5 et 97,5 avant
centrage-réduction, puis le nombre de classes est choisi par le score de
silhouette. La typologie est construite sur le panel mondial ; les
observations CEMAC hors panel y sont ensuite rattachées.
"""
import csv
import os
from collections import Counter

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Patch
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

from extraire_tre_brut_fmi import (ANNEES_CIBLES, BANDES, CEMAC, PANEL_MONDIAL,
                                   charger_cemac, charger_panel_mondial)
from style_graphiques import (COULEURS_BANDES, COULEURS_COMPOSANTES, ENCRE,
                              ENCRE_DISCRETE, ENCRE_SECONDAIRE, LIBELLES_COMPOSANTES,
                              NEUTRE_CLAIR, appliquer_style, enregistrer)

VARIABLES = ['tm', 'tas', 'tfr']
DOSSIER_RESULTATS = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'resultats')
ABREV = {'CMR': 'CMR', 'COG': 'COG', 'GAB': 'GAB', 'GNQ': 'GNQ', 'TCD': 'TCD', 'CAF': 'RCA'}


def nommer_classes(centres):
    """Nomme chaque classe d'après son canal de fuite dominant."""
    noms = {}
    restantes = set(range(len(centres)))
    regles = [
        ('Déficit commercial structurel', lambda c: c[0]),
        ('Fuite par les services', lambda c: c[1]),
        ('Fuite par les revenus rapatriés', lambda c: c[2]),
        ('Excédent commercial solide', lambda c: -c[0]),
    ]
    for nom, critere in regles:
        k = max(restantes, key=lambda i: critere(centres[i]))
        noms[k] = nom
        restantes.discard(k)
    for k in restantes:
        noms[k] = 'Commerce équilibré sans marge'
    return noms


def construire():
    panel = charger_panel_mondial()
    cemac = charger_cemac()
    obs = [{'code': c, 'pays': PANEL_MONDIAL[c], 'annee': a, **panel[c][a]}
           for c in panel for a in ANNEES_CIBLES]
    hors_panel = [{'code': c, 'pays': CEMAC[c], 'annee': a, **cemac[c][a]}
                  for c in CEMAC if c not in panel for a in sorted(cemac[c])]

    X = np.array([[o[v] for v in VARIABLES] for o in obs])
    bas, haut = np.percentile(X, 2.5, axis=0), np.percentile(X, 97.5, axis=0)
    normaliseur = StandardScaler().fit(np.clip(X, bas, haut))
    Z = normaliseur.transform(np.clip(X, bas, haut))

    scores = {}
    for k in range(3, 8):
        scores[k] = silhouette_score(Z, KMeans(k, n_init=20, random_state=42).fit_predict(Z))
    k_retenu = max(scores, key=scores.get)
    km = KMeans(k_retenu, n_init=20, random_state=42).fit(Z)

    centres_bruts = [X[km.labels_ == j].mean(axis=0) for j in range(k_retenu)]
    noms = nommer_classes(centres_bruts)
    for o, lab in zip(obs, km.labels_):
        o['classe'] = noms[lab]
    Zh = normaliseur.transform(np.clip(np.array([[o[v] for v in VARIABLES] for o in hors_panel]), bas, haut))
    for o, lab in zip(hors_panel, km.predict(Zh)):
        o['classe'] = noms[lab]

    acp = PCA(n_components=2).fit(Z)
    for o, z in zip(obs, acp.transform(Z)):
        o['axe1'], o['axe2'] = z
    for o, z in zip(hors_panel, acp.transform(Zh)):
        o['axe1'], o['axe2'] = z
    return obs, hors_panel, scores, k_retenu, acp


def ordre_classes(obs):
    """Classes triées du TRE moyen le plus élevé au plus bas."""
    moyennes = {}
    for o in obs:
        moyennes.setdefault(o['classe'], []).append(o['tre'])
    return sorted(moyennes, key=lambda c: -np.mean(moyennes[c]))


def figure_usage_valeur(obs, classes):
    fig, ax = plt.subplots(figsize=(6.3, 0.62 * len(classes) + 1.1))
    for y, cl in enumerate(classes):
        membres = [o for o in obs if o['classe'] == cl]
        moy = {v: np.mean([o[v] for o in membres]) for v in VARIABLES}
        gauche = 0
        for v in VARIABLES:
            cle = v.upper()
            ax.barh(y, moy[v], left=gauche, color=COULEURS_COMPOSANTES[cle], height=0.62,
                    edgecolor='white', linewidth=1)
            if moy[v] >= 9:
                ax.text(gauche + moy[v] / 2, y, f"{moy[v]:.0f}", ha='center', va='center',
                        fontsize=7.5, color='white')
            gauche += moy[v]
        tre = 100 - gauche
        if tre > 0:
            ax.barh(y, tre, left=gauche, color=COULEURS_COMPOSANTES['TRE'], height=0.62,
                    edgecolor='white', linewidth=1)
            ax.text(gauche + tre / 2, y, f"{tre:.0f}", ha='center', va='center', fontsize=7.5,
                    color='white')
            fin = 100
        else:
            fin = gauche
        ax.text(fin + 3, y, f"TRE moyen {tre:+.0f} %  (n={len(membres)})", va='center',
                fontsize=7.5, color=ENCRE)
    ax.axvline(100, color=ENCRE, linewidth=1, linestyle='--')
    ax.text(100, -0.55, ' valeur exportée = 100', fontsize=7, color=ENCRE_SECONDAIRE,
            va='bottom')
    ax.set_yticks(range(len(classes)))
    ax.set_yticklabels(classes, fontsize=8)
    ax.invert_yaxis()
    ax.set_xlim(0, 330)
    ax.set_xlabel('Utilisation de 100 unités de recettes d\'exportation de biens (moyenne de la classe)')
    ax.grid(axis='y', visible=False)
    ax.legend(handles=[Patch(color=COULEURS_COMPOSANTES[c], label=LIBELLES_COMPOSANTES[c])
                       for c in ('TM', 'TAS', 'TFR', 'TRE')],
              loc='upper center', bbox_to_anchor=(0.5, -0.2), ncol=4, fontsize=7)
    enregistrer(fig, 'clusters_usage_valeur.pdf')


def figure_bandes_par_classe(obs, classes):
    fig, ax = plt.subplots(figsize=(6.3, 0.5 * len(classes) + 1.0))
    for y, cl in enumerate(classes):
        compte = Counter(o['bande'] for o in obs if o['classe'] == cl)
        total = sum(compte.values())
        gauche = 0
        for b in BANDES:
            if compte[b] == 0:
                continue
            part = compte[b] / total * 100
            ax.barh(y, part, left=gauche, color=COULEURS_BANDES[b], height=0.62,
                    edgecolor='white', linewidth=1)
            if part >= 7:
                ax.text(gauche + part / 2, y, f"{part:.0f} %", ha='center', va='center',
                        fontsize=7, color='white' if b != 'FAIBLE' else ENCRE)
            gauche += part
    ax.set_yticks(range(len(classes)))
    ax.set_yticklabels(classes, fontsize=8)
    ax.invert_yaxis()
    ax.set_xlim(0, 100)
    ax.set_xlabel('Répartition des observations pays-année de la classe entre les bandes (%)')
    ax.grid(axis='y', visible=False)
    ax.legend(handles=[Patch(color=COULEURS_BANDES[b], label=b) for b in BANDES],
              loc='upper center', bbox_to_anchor=(0.5, -0.25), ncol=5, fontsize=7)
    enregistrer(fig, 'clusters_bandes.pdf')


def figure_acp(obs, hors_panel, classes, acp):
    fig, axes = plt.subplots(2, 3, figsize=(6.6, 4.9), sharex=True, sharey=True)
    axes = axes.ravel()
    tous = obs + hors_panel
    x = np.array([o['axe1'] for o in tous])
    y = np.array([o['axe2'] for o in tous])

    ax = axes[0]
    ax.scatter(x, y, s=6, color=NEUTRE_CLAIR, edgecolor='none')
    noms = {'tm': 'TM', 'tas': 'TAS', 'tfr': 'TFR'}
    for v, (cx, cy) in zip(VARIABLES, acp.components_.T):
        ax.annotate('', xy=(cx * 2.4, cy * 2.4), xytext=(0, 0),
                    arrowprops=dict(arrowstyle='->', color=COULEURS_COMPOSANTES[noms[v]], lw=1.6))
        ax.text(cx * 2.75, cy * 2.75, noms[v], fontsize=8, fontweight='bold',
                color=COULEURS_COMPOSANTES[noms[v]], ha='center', va='center')
    var = acp.explained_variance_ratio_ * 100
    ax.set_title('Lecture des axes', fontsize=8.5, loc='left')

    for ax, cl in zip(axes[1:], classes):
        dedans = np.array([o['classe'] == cl for o in tous])
        ax.scatter(x[~dedans], y[~dedans], s=5, color=NEUTRE_CLAIR, edgecolor='none')
        ax.scatter(x[dedans], y[dedans], s=9, color='#2a78d6', edgecolor='white', linewidth=0.3)
        for o in tous:
            if o['classe'] == cl and o['code'] in CEMAC:
                ax.scatter(o['axe1'], o['axe2'], s=24, facecolor='none', edgecolor=ENCRE, linewidth=0.9)
        ax.set_title(cl, fontsize=8, loc='left')
    for ax in axes:
        ax.grid(color='#f0efec', linewidth=0.5)
        ax.tick_params(labelsize=6.5)
    for ax in axes[3:]:
        ax.set_xlabel(f'Axe 1 ({var[0]:.0f} %)', fontsize=7)
    for ax in axes[::3]:
        ax.set_ylabel(f'Axe 2 ({var[1]:.0f} %)', fontsize=7)
    xmin, xmax = np.percentile(x, [0.5, 99.5])
    ymin, ymax = np.percentile(y, [0.5, 99.5])
    axes[0].set_xlim(xmin - 0.6, xmax + 0.6)
    axes[0].set_ylim(ymin - 0.6, ymax + 0.6)
    fig.tight_layout(h_pad=1.0, w_pad=0.6)
    enregistrer(fig, 'clusters_acp.pdf')


TEINTES_ANNEES = {'2014': '#9ec5f4', '2015': '#6da7ec', '2016': '#3987e5',
                  '2019': '#256abf', '2020': '#184f95', '2021': '#0d366b'}

COURTS = {'Excédent commercial solide': 'Excédent', 'Commerce équilibré sans marge': 'Équilibre',
          'Fuite par les revenus rapatriés': 'Revenus', 'Fuite par les services': 'Services',
          'Déficit commercial structurel': 'Déficit'}


def figure_parcours_cemac(obs, hors_panel, classes):
    """Un panneau par pays CEMAC : son parcours entre les profils, année par année."""
    tous = obs + hors_panel
    x = np.array([o['axe1'] for o in tous])
    y = np.array([o['axe2'] for o in tous])
    centres = {cl: (np.mean([o['axe1'] for o in obs if o['classe'] == cl]),
                    np.mean([o['axe2'] for o in obs if o['classe'] == cl])) for cl in classes}
    fig, axes = plt.subplots(2, 3, figsize=(6.6, 4.8), sharex=True, sharey=True)
    for ax, code in zip(axes.ravel(), CEMAC):
        ax.scatter(x, y, s=5, color=NEUTRE_CLAIR, edgecolor='none')
        for cl, (cx, cy) in centres.items():
            ax.scatter(cx, cy, s=26, marker='s', color=ENCRE_DISCRETE)
            ax.text(cx, cy - 0.32, COURTS[cl], fontsize=6, color=ENCRE_SECONDAIRE, ha='center', va='top')
        parcours = sorted([o for o in tous if o['code'] == code], key=lambda o: o['annee'])
        px = [o['axe1'] for o in parcours]
        py = [o['axe2'] for o in parcours]
        for k in range(len(parcours) - 1):
            ax.annotate('', xy=(px[k + 1], py[k + 1]), xytext=(px[k], py[k]),
                        arrowprops=dict(arrowstyle='->', color='#86b6ef', lw=1.2,
                                        shrinkA=3, shrinkB=3))
        ax.scatter(px, py, s=22, c=[TEINTES_ANNEES[o['annee']] for o in parcours],
                   edgecolor='white', linewidth=0.5, zorder=3)
        for o in (parcours[0], parcours[-1]):
            ax.annotate(o['annee'], (o['axe1'], o['axe2']), xytext=(4, 3), textcoords='offset points',
                        fontsize=6.5, color=ENCRE, fontweight='bold')
        ax.set_title(CEMAC[code], fontsize=8.5, loc='left')
        ax.grid(color='#f0efec', linewidth=0.5)
        ax.tick_params(labelsize=6.5)
    xmin, xmax = np.percentile(x, [0.5, 99.5])
    ymin, ymax = np.percentile(y, [0.5, 99.5])
    axes[0, 0].set_xlim(xmin - 0.6, xmax + 0.6)
    axes[0, 0].set_ylim(ymin - 0.8, ymax + 0.6)
    for ax in axes[1]:
        ax.set_xlabel('Axe 1', fontsize=7)
    for ax in axes[:, 0]:
        ax.set_ylabel('Axe 2', fontsize=7)
    fig.tight_layout(h_pad=1.0, w_pad=0.6, rect=(0, 0.05, 1, 1))
    fig.legend(handles=[plt.Line2D([], [], marker='o', linestyle='', color=c, markersize=5, label=a)
                        for a, c in TEINTES_ANNEES.items()]
               + [plt.Line2D([], [], marker='s', linestyle='', color=ENCRE_DISCRETE, markersize=5,
                             label='Centre de profil')],
               loc='lower center', ncol=7, fontsize=7)
    enregistrer(fig, 'cemac_parcours_profils.pdf')


def ecrire_resultats(obs, hors_panel, classes, scores, k, acp):
    os.makedirs(DOSSIER_RESULTATS, exist_ok=True)
    with open(os.path.join(DOSSIER_RESULTATS, 'classes_profils.csv'), 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['classe', 'n', 'TM', 'TAS', 'TFR', 'TRE'] + BANDES)
        for cl in classes:
            m = [o for o in obs if o['classe'] == cl]
            c = Counter(o['bande'] for o in m)
            w.writerow([cl, len(m)] + [round(np.mean([o[v] for o in m]), 1) for v in VARIABLES + ['tre']]
                       + [c[b] for b in BANDES])
    with open(os.path.join(DOSSIER_RESULTATS, 'classes_cemac.csv'), 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['pays', 'annee', 'classe', 'tre', 'bande', 'source'])
        for o in obs + hors_panel:
            if o['code'] in CEMAC:
                w.writerow([o['pays'], o['annee'], o['classe'], round(o['tre'], 1), o['bande'], o['source']])
    print('Silhouette par k :', {kk: round(s, 3) for kk, s in scores.items()}, '-> k =', k)
    print('Variance expliquée ACP :', (acp.explained_variance_ratio_ * 100).round(1))
    print('Coordonnées des variables :', dict(zip(VARIABLES, acp.components_.T.round(2).tolist())))
    for cl in classes:
        m = [o for o in obs if o['classe'] == cl]
        print(f"{cl:32s} n={len(m):3d}", {v: round(np.mean([o[v] for o in m]), 1) for v in VARIABLES + ['tre']},
              dict(Counter(o['bande'] for o in m)))
    print('CEMAC :')
    for o in sorted(obs + hors_panel, key=lambda o: (o['pays'], o['annee'])):
        if o['code'] in CEMAC:
            print(f"  {o['pays']:20s} {o['annee']} {o['classe']}")


if __name__ == '__main__':
    appliquer_style()
    obs, hors_panel, scores, k, acp = construire()
    classes = ordre_classes(obs)
    figure_usage_valeur(obs, classes)
    figure_bandes_par_classe(obs, classes)
    figure_acp(obs, hors_panel, classes, acp)
    figure_parcours_cemac(obs, hors_panel, classes)
    ecrire_resultats(obs, hors_panel, classes, scores, k, acp)
