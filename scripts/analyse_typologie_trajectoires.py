# -*- coding: utf-8 -*-
"""H1 (typologie) et H2 (chemin de progression entre bandes).

Unité d'observation : le couple pays-année (41 pays x 6 années cibles).
Produit quatre figures et un fichier de résultats chiffrés.
"""
import csv
import os
from collections import Counter

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import ListedColormap, to_rgb
from matplotlib.patches import Patch

from extraire_tre_brut_fmi import (ANNEES_CIBLES, BANDES, CEMAC, PANEL_MONDIAL,
                                   SEUILS, charger_cemac, charger_panel_mondial)
from style_graphiques import (COULEURS_BANDES, COULEURS_CEMAC, COULEURS_COMPOSANTES,
                              ENCRE, ENCRE_SECONDAIRE, LIBELLES_COMPOSANTES,
                              NEUTRE_CLAIR, appliquer_style, enregistrer)

RANG = {b: i for i, b in enumerate(BANDES)}
DOSSIER_RESULTATS = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'resultats')


def couleur_texte(fond):
    r, g, b = to_rgb(fond)
    return 'white' if 0.299 * r + 0.587 * g + 0.114 * b < 0.6 else ENCRE


def transitions(panel):
    """Liste des passages entre deux années cibles consécutives."""
    liste = []
    for code, d in panel.items():
        for a1, a2 in zip(ANNEES_CIBLES[:-1], ANNEES_CIBLES[1:]):
            i1, i2 = d[a1], d[a2]
            liste.append({
                'pays': PANEL_MONDIAL[code], 'a1': a1, 'a2': a2,
                'b1': i1['bande'], 'b2': i2['bande'],
                'dtre': i2['tre'] - i1['tre'],
                # contribution de chaque levier : une baisse de fuite améliore le TRE
                'TM': -(i2['tm'] - i1['tm']),
                'TAS': -(i2['tas'] - i1['tas']),
                'TFR': -(i2['tfr'] - i1['tfr']),
            })
    return liste


def figure_distribution(panel):
    """Histogramme des 246 taux, coloré par bande, avec les seuils retenus."""
    valeurs = np.array([d['tre'] for v in panel.values() for d in v.values()])
    fig, ax = plt.subplots(figsize=(6.3, 2.9))
    bords = np.arange(-230, 65, 5)
    comptes, _ = np.histogram(valeurs, bords)
    for g, h, n in zip(bords[:-1], bords[1:], comptes):
        if n:
            centre = (g + h) / 2
            nom = next(b for b, s in SEUILS if centre < s)
            ax.bar(g, n, width=5, align='edge', color=COULEURS_BANDES[nom], edgecolor='white', linewidth=0.6)
    for nom, s in SEUILS[:-1]:
        ax.axvline(s, color=ENCRE, linewidth=0.9, linestyle='--')
        ax.text(s + 1.5, comptes.max() * 1.02, f'{s:g} %', fontsize=7, color=ENCRE)
    compte = Counter(d['bande'] for v in panel.values() for d in v.values())
    ax.set_xlim(-230, 62)
    ax.set_ylim(0, comptes.max() * 1.15)
    ax.set_xlabel('Taux de rétention (%) des 246 observations pays-année')
    ax.set_ylabel("Nombre d'observations")
    ax.grid(axis='x', visible=False)
    ax.legend(handles=[Patch(color=COULEURS_BANDES[b], label=f'{b} ({compte[b]})') for b in BANDES],
              loc='upper left', fontsize=7)
    enregistrer(fig, 'tre_distribution_seuils.pdf')


def figure_repartition(panel):
    fig, ax = plt.subplots(figsize=(6.3, 2.9))
    annees = ANNEES_CIBLES[::-1]
    for y, a in enumerate(annees):
        compte = Counter(panel[c][a]['bande'] for c in panel)
        gauche = 0
        for b in BANDES:
            n = compte[b]
            if n == 0:
                continue
            ax.barh(y, n, left=gauche, color=COULEURS_BANDES[b], edgecolor='white',
                    linewidth=1.2, height=0.72)
            ax.text(gauche + n / 2, y, str(n), ha='center', va='center', fontsize=8,
                    color=couleur_texte(COULEURS_BANDES[b]))
            gauche += n
    ax.set_yticks(range(len(annees)))
    ax.set_yticklabels(annees)
    ax.set_xlim(0, len(panel))
    ax.set_xlabel('Nombre de pays (panel de 41 pays)')
    ax.grid(axis='y', visible=False)
    ax.legend(handles=[Patch(color=COULEURS_BANDES[b], label=b) for b in BANDES],
              loc='upper center', bbox_to_anchor=(0.5, -0.22), ncol=5, fontsize=7.5)
    enregistrer(fig, 'tre_repartition_bandes_annee.pdf')


def figure_heatmap(panel, cemac):
    lignes = [(PANEL_MONDIAL[c], panel[c], c in CEMAC) for c in panel]
    lignes.sort(key=lambda l: (-np.mean([RANG[l[1][a]['bande']] for a in ANNEES_CIBLES]),
                               -l[1]['2021']['tre']))
    hors_panel = [(CEMAC[c], cemac[c], True) for c in CEMAC if c not in panel]
    lignes += [None] + hors_panel  # ligne vide de séparation

    hauteur = 0.205 * len(lignes) + 0.9
    fig, ax = plt.subplots(figsize=(6.3, hauteur))
    for y, ligne in enumerate(lignes):
        if ligne is None:
            continue
        nom, donnees, est_cemac = ligne
        for x, a in enumerate(ANNEES_CIBLES):
            if a in donnees:
                fond = COULEURS_BANDES[donnees[a]['bande']]
                texte = f"{round(donnees[a]['tre']) + 0:d}"
                if donnees[a]['source'] == 'BEAC':
                    texte += '*'
            else:
                fond, texte = NEUTRE_CLAIR, 'n.d.'
            ax.add_patch(plt.Rectangle((x, y), 1, 1, facecolor=fond, edgecolor='white', linewidth=1))
            ax.text(x + 0.5, y + 0.5, texte, ha='center', va='center', fontsize=6.5,
                    color=couleur_texte(fond) if texte != 'n.d.' else ENCRE_SECONDAIRE)
        ax.text(-0.15, y + 0.5, nom, ha='right', va='center', fontsize=7,
                fontweight='bold' if est_cemac else 'normal', color=ENCRE)
    ax.set_xlim(0, len(ANNEES_CIBLES))
    ax.set_ylim(len(lignes), 0)
    ax.set_xticks([x + 0.5 for x in range(len(ANNEES_CIBLES))])
    ax.set_xticklabels(ANNEES_CIBLES)
    ax.xaxis.tick_top()
    ax.set_yticks([])
    ax.grid(False)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.tick_params(length=0)
    ax.legend(handles=[Patch(color=COULEURS_BANDES[b], label=b) for b in BANDES],
              loc='upper center', bbox_to_anchor=(0.5, -0.005), ncol=5, fontsize=7.5)
    enregistrer(fig, 'tre_heatmap_pays_annee.pdf')


def figure_matrice(trans):
    n = len(BANDES)
    m = np.zeros((n, n), dtype=int)
    for t in trans:
        m[RANG[t['b1']], RANG[t['b2']]] += 1
    proba = m / np.maximum(m.sum(axis=1, keepdims=True), 1)
    rampe = ListedColormap(['#f4f8fd', '#cde2fb', '#9ec5f4', '#6da7ec', '#3987e5',
                            '#256abf', '#184f95', '#0d366b'])
    fig, ax = plt.subplots(figsize=(5.4, 4.2))
    ax.imshow(proba, cmap=rampe, vmin=0, vmax=1)
    for i in range(n):
        for j in range(n):
            if m[i, j] == 0:
                txt, coul = '0', ENCRE_SECONDAIRE
            else:
                txt = f"{proba[i, j] * 100:.0f} %\n(n={m[i, j]})"
                coul = 'white' if proba[i, j] > 0.45 else ENCRE
            ax.text(j, i, txt, ha='center', va='center', fontsize=7.5, color=coul)
    ax.set_xticks(range(n))
    ax.set_yticks(range(n))
    ax.set_xticklabels([b.replace(' ', '\n') for b in BANDES], fontsize=7.5)
    ax.set_yticklabels(BANDES, fontsize=7.5)
    ax.set_xlabel('Bande à l\'année cible suivante')
    ax.set_ylabel('Bande à l\'année cible de départ')
    ax.grid(False)
    for s in ax.spines.values():
        s.set_visible(False)
    enregistrer(fig, 'tre_matrice_transition.pdf')
    return m


def figure_leviers(trans):
    montees = [t for t in trans if RANG[t['b2']] > RANG[t['b1']]]
    montees.sort(key=lambda t: t['dtre'])
    total = {lev: sum(max(t[lev], 0) for t in montees) for lev in ('TM', 'TAS', 'TFR')}
    somme = sum(total.values())
    parts = {lev: total[lev] / somme * 100 for lev in total}

    borne = 120
    fig, (ax0, ax) = plt.subplots(2, 1, figsize=(6.0, 0.15 * len(montees) + 2.1),
                                  gridspec_kw={'height_ratios': [0.95, 0.15 * len(montees)], 'hspace': 0.16})
    # Synthèse : part de chaque levier dans l'ensemble des gains
    gauche = 0
    for lev in ('TM', 'TAS', 'TFR'):
        ax0.barh(0, parts[lev], left=gauche, color=COULEURS_COMPOSANTES[lev], height=0.55,
                 edgecolor='white', linewidth=1.2)
        if parts[lev] >= 8:
            ax0.text(gauche + parts[lev] / 2, 0, f"{parts[lev]:.0f} %", ha='center', va='center',
                     fontsize=8.5, color='white', fontweight='bold')
        else:
            ax0.annotate(f"{parts[lev]:.0f} %", (gauche + parts[lev] / 2, 0.28), xytext=(0, 6),
                         textcoords='offset points', ha='center', fontsize=8.5, color=ENCRE)
        gauche += parts[lev]
    ax0.set_xlim(0, 100)
    ax0.set_ylim(-0.5, 0.75)
    ax0.set_yticks([])
    ax0.set_xticks([])
    ax0.grid(False)
    for s in ax0.spines.values():
        s.set_visible(False)
    ax0.set_title(f'Part de chaque levier dans les gains cumulés des {len(montees)} montées de bande',
                  fontsize=9, loc='left', color=ENCRE)
    ax0.legend(handles=[Patch(color=COULEURS_COMPOSANTES[l], label=LIBELLES_COMPOSANTES[l])
                        for l in ('TM', 'TAS', 'TFR')]
               + [plt.Line2D([], [], color=ENCRE, marker='|', linestyle='', markersize=8,
                             label='Variation totale du TRE')],
               loc='upper center', bbox_to_anchor=(0.5, -0.05), ncol=2, fontsize=7.5)

    # Détail : décomposition de chaque montée
    for y, t in enumerate(montees):
        pos, neg = 0.0, 0.0
        for lev in ('TM', 'TAS', 'TFR'):
            v = t[lev]
            if v >= 0:
                debut, fin = min(pos, borne), min(pos + v, borne)
                pos += v
            else:
                debut, fin = neg, neg + v
                neg += v
            if fin != debut:
                ax.barh(y, fin - debut, left=debut, color=COULEURS_COMPOSANTES[lev], height=0.78,
                        edgecolor='white', linewidth=0.8)
        if t['dtre'] > borne:
            ax.text(borne + 1, y, f"+{t['dtre']:.0f}", va='center', fontsize=6.5, color=ENCRE)
        else:
            ax.plot(t['dtre'], y, marker='|', color=ENCRE, markersize=8, markeredgewidth=1.4)
    ax.set_yticks(range(len(montees)))
    ax.set_yticklabels([f"{t['pays']} {t['a1']}→{t['a2']}" for t in montees], fontsize=7.5)
    ax.set_ylim(-0.6, len(montees) - 0.4)
    ax.set_xlim(-25, borne + 12)
    ax.axvline(0, color=ENCRE_SECONDAIRE, linewidth=0.8)
    ax.set_xlabel('Contribution de chaque levier à la hausse du TRE (points)')
    ax.grid(axis='y', visible=False)
    enregistrer(fig, 'tre_leviers_montees.pdf')
    return montees, parts


def fond_bandes(ax, bas, haut, x_etiquette):
    """Colore l'arrière-plan selon les bandes et les nomme à droite."""
    bornes = [bas] + [s for _, s in SEUILS[:-1]] + [haut]
    for (nom, _), b, h in zip(SEUILS, bornes[:-1], bornes[1:]):
        ax.axhspan(b, h, color=COULEURS_BANDES[nom], alpha=0.12, linewidth=0)
        ax.text(x_etiquette, (b + h) / 2, nom, fontsize=6.5, va='center', ha='left',
                color=COULEURS_BANDES[nom], fontweight='bold')


def etiquettes_sans_chevauchement(valeurs, ecart):
    """Décale verticalement des étiquettes pour qu'elles ne se recouvrent pas."""
    ordre = sorted(range(len(valeurs)), key=lambda i: valeurs[i])
    positions = list(valeurs)
    for k in range(1, len(ordre)):
        i, j = ordre[k - 1], ordre[k]
        positions[j] = max(positions[j], positions[i] + ecart)
    return positions


def figure_trajectoires(panel):
    choix = ['COG', 'SAU', 'IRQ', 'QAT']
    palette = ['#2a78d6', '#eb6834', '#1baf7a', '#eda100']
    x = [int(a) for a in ANNEES_CIBLES]
    fig, ax = plt.subplots(figsize=(6.3, 3.7))
    fond_bandes(ax, -120, 62, 2023.9)
    finales = [panel[c]['2021']['tre'] for c in choix]
    places = etiquettes_sans_chevauchement(finales, 8)
    for code, coul, yl in zip(choix, palette, places):
        y = [panel[code][a]['tre'] for a in ANNEES_CIBLES]
        ax.plot(x, y, color=coul, linewidth=2, marker='o', markersize=4.5, label=PANEL_MONDIAL[code])
        ax.text(2021.25, yl, PANEL_MONDIAL[code], fontsize=7.5, color=ENCRE, va='center')
    ax.set_xticks(x)
    ax.set_xlim(2013.6, 2025.6)
    ax.set_ylim(-120, 62)
    ax.set_ylabel('Taux de rétention (%)')
    ax.grid(axis='x', visible=False)
    ax.legend(loc='upper center', bbox_to_anchor=(0.42, -0.1), ncol=4)
    enregistrer(fig, 'tre_trajectoires_exemplaires.pdf')


def ecrire_resultats(panel, matrice, montees, parts):
    os.makedirs(DOSSIER_RESULTATS, exist_ok=True)
    with open(os.path.join(DOSSIER_RESULTATS, 'repartition_bandes.csv'), 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['annee'] + BANDES)
        for a in ANNEES_CIBLES:
            c = Counter(panel[p][a]['bande'] for p in panel)
            w.writerow([a] + [c[b] for b in BANDES])
    with open(os.path.join(DOSSIER_RESULTATS, 'montees.csv'), 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['pays', 'de', 'a', 'bande_depart', 'bande_arrivee', 'delta_tre', 'TM', 'TAS', 'TFR'])
        for t in montees:
            w.writerow([t['pays'], t['a1'], t['a2'], t['b1'], t['b2'],
                        round(t['dtre'], 1), round(t['TM'], 1), round(t['TAS'], 1), round(t['TFR'], 1)])
    print('Répartition des bandes :', dict(Counter(d['bande'] for v in panel.values() for d in v.values())))
    print('Matrice de transition (lignes = départ) :')
    for b, ligne in zip(BANDES, matrice):
        print(f'  {b:14s}', list(ligne))
    print(f'Montées de bande : {len(montees)} ; part des gains : '
          + ', '.join(f'{k} {v:.0f} %' for k, v in parts.items()))


if __name__ == '__main__':
    appliquer_style()
    panel = charger_panel_mondial()
    cemac = charger_cemac()
    trans = transitions(panel)
    figure_distribution(panel)
    figure_repartition(panel)
    figure_heatmap(panel, cemac)
    matrice = figure_matrice(trans)
    montees, parts = figure_leviers(trans)
    figure_trajectoires(panel)
    ecrire_resultats(panel, matrice, montees, parts)
