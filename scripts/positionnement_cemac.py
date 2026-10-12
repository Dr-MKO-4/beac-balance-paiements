# -*- coding: utf-8 -*-
"""H3 : positionnement des six pays de la CEMAC dans la typologie mondiale.

Le Cameroun et le Congo font partie du panel mondial (source FMI, 6 années).
Le Gabon (2020-2021), la Guinée Équatoriale, le Tchad et la RCA sont
renseignés par les fichiers BDP officiels de la BEAC sur les années cibles
disponibles. Le score relatif compare chaque pays à la moyenne du panel
mondial de la même année, pour neutraliser le choc commun des cours.
"""
import csv
import os

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Patch

from analyse_typologie_trajectoires import etiquettes_sans_chevauchement, fond_bandes
from extraire_tre_brut_fmi import (ANNEES_CIBLES, BANDES, CEMAC, SEUILS, charger_cemac,
                                   charger_panel_mondial)
from style_graphiques import (COULEURS_CEMAC, COULEURS_COMPOSANTES, ENCRE, ENCRE_SECONDAIRE,
                              LIBELLES_COMPOSANTES, appliquer_style, enregistrer)

DOSSIER_RESULTATS = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'resultats')
X_ANNEES = [int(a) for a in ANNEES_CIBLES]
BAS, HAUT = -130, 62


def figure_trajectoires(cemac):
    fig, ax = plt.subplots(figsize=(6.3, 3.9))
    fond_bandes(ax, BAS, HAUT, 2023.9)
    finales, noms = [], []
    for code, nom in CEMAC.items():
        y = [cemac[code][a]['tre'] if a in cemac[code] else np.nan for a in ANNEES_CIBLES]
        y_trace = [v if np.isnan(v) or v > BAS else np.nan for v in y]
        ax.plot(X_ANNEES, y_trace, color=COULEURS_CEMAC[nom], linewidth=2, marker='o',
                markersize=4.5, label=nom)
        if not np.isnan(y_trace[-1]):
            finales.append(y_trace[-1])
            noms.append(nom)
    for nom, yl in zip(noms, etiquettes_sans_chevauchement(finales, 7)):
        ax.text(2021.25, yl, nom, fontsize=7.5, color=ENCRE, va='center')
    hors = ', '.join(f"{cemac['CAF'][a]['tre']:.0f} % ({a})" for a in sorted(cemac['CAF']))
    ax.annotate(f'RCA hors échelle : {hors}', xy=(2020.5, BAS + 2), xytext=(2016.4, BAS + 14),
                fontsize=7, color=ENCRE,
                arrowprops=dict(arrowstyle='->', color=COULEURS_CEMAC['RCA'], lw=1.2))
    ax.set_xticks(X_ANNEES)
    ax.set_xlim(2013.6, 2025.6)
    ax.set_ylim(BAS, HAUT)
    ax.set_ylabel('Taux de rétention (%)')
    ax.grid(axis='x', visible=False)
    ax.legend(loc='upper center', bbox_to_anchor=(0.42, -0.1), ncol=6, fontsize=7)
    enregistrer(fig, 'cemac_trajectoires.pdf')


def profil_moyen(panel, bande):
    obs = [d for v in panel.values() for d in v.values() if d['bande'] == bande]
    return {k: np.mean([o[k] for o in obs]) for k in ('tm', 'tas', 'tfr', 'tre')}, len(obs)


def figure_usage_2021(panel, cemac):
    lignes = []
    for code, nom in CEMAC.items():
        d = cemac[code]['2021']
        lignes.append((f'{nom} 2021', d, False))
    for b in ('NORMAL', 'BON'):
        moy, n = profil_moyen(panel, b)
        lignes.append((f'Profil moyen {b} (monde, n={n})', moy, True))
    borne = 230
    fig, ax = plt.subplots(figsize=(6.3, 0.42 * len(lignes) + 1.2))
    for y, (nom, d, reference) in enumerate(lignes):
        gauche = 0
        for k in ('tm', 'tas', 'tfr'):
            v = d[k]
            fin = min(gauche + v, borne)
            if fin > gauche:
                ax.barh(y, fin - gauche, left=gauche, color=COULEURS_COMPOSANTES[k.upper()],
                        height=0.62, edgecolor='white', linewidth=1, alpha=0.75 if reference else 1)
                if v >= 9 and fin - gauche >= 9:
                    ax.text(gauche + (fin - gauche) / 2, y, f'{v:.0f}', ha='center', va='center',
                            fontsize=7, color='white')
            gauche += v
        if gauche < 100:
            ax.barh(y, 100 - gauche, left=gauche, color=COULEURS_COMPOSANTES['TRE'], height=0.62,
                    edgecolor='white', linewidth=1, alpha=0.75 if reference else 1)
            ax.text(gauche + (100 - gauche) / 2, y, f"{100 - gauche:.0f}", ha='center', va='center',
                    fontsize=7, color='white')
        texte = f"TRE {d['tre']:+.0f} %"
        ax.text(min(max(gauche, 100), borne) + 3, y, texte, va='center', fontsize=7.5, color=ENCRE)
    ax.axhline(len(CEMAC) - 0.5, color=ENCRE_SECONDAIRE, linewidth=0.6)
    ax.axvline(100, color=ENCRE, linewidth=1, linestyle='--')
    ax.set_yticks(range(len(lignes)))
    ax.set_yticklabels([l[0] for l in lignes], fontsize=7.5)
    ax.invert_yaxis()
    ax.set_xlim(0, borne + 35)
    ax.set_xlabel("Utilisation de 100 unités de recettes d'exportation de biens")
    ax.grid(axis='y', visible=False)
    ax.legend(handles=[Patch(color=COULEURS_COMPOSANTES[c], label=LIBELLES_COMPOSANTES[c])
                       for c in ('TM', 'TAS', 'TFR', 'TRE')],
              loc='upper center', bbox_to_anchor=(0.5, -0.16), ncol=4, fontsize=7)
    enregistrer(fig, 'cemac_usage_valeur_2021.pdf')


def statistiques_annuelles(panel):
    """Moyenne et écart-type du panel par année, après écrêtage à 2,5 % de chaque côté."""
    stats = {}
    for a in ANNEES_CIBLES:
        v = np.array([panel[c][a]['tre'] for c in panel])
        v = np.clip(v, *np.percentile(v, [2.5, 97.5]))
        stats[a] = (v.mean(), v.std())
    return stats


def figure_score_relatif(panel, cemac):
    stats = statistiques_annuelles(panel)
    fig, ax = plt.subplots(figsize=(6.3, 3.4))
    ax.axhspan(-1, 1, color='#f0efec', linewidth=0)
    ax.axhline(0, color=ENCRE_SECONDAIRE, linewidth=0.9)
    finales, noms = [], []
    for code, nom in CEMAC.items():
        if code == 'CAF':
            continue
        z = [(cemac[code][a]['tre'] - stats[a][0]) / stats[a][1] if a in cemac[code] else np.nan
             for a in ANNEES_CIBLES]
        ax.plot(X_ANNEES, z, color=COULEURS_CEMAC[nom], linewidth=2, marker='o', markersize=4.5, label=nom)
        finales.append(z[-1])
        noms.append(nom)
    for nom, yl in zip(noms, etiquettes_sans_chevauchement(finales, 0.22)):
        ax.text(2021.25, yl, nom, fontsize=7.5, color=ENCRE, va='center')
    z_rca = {a: (cemac['CAF'][a]['tre'] - stats[a][0]) / stats[a][1] for a in cemac['CAF']}
    ax.text(2013.8, -1.85, 'RCA hors échelle : ' + ', '.join(f'{z:.1f} ({a})' for a, z in z_rca.items()),
            fontsize=7, color=ENCRE)
    ax.text(2022.5, 0.06, '↑ mieux que la moyenne\n   mondiale de l\'année', fontsize=6.5,
            color=ENCRE_SECONDAIRE, va='bottom')
    ax.text(2022.5, -0.06, '↓ moins bien', fontsize=6.5, color=ENCRE_SECONDAIRE, va='top')
    ax.text(2013.8, 1.05, 'zone de ±1 écart-type', fontsize=6.5, color=ENCRE_SECONDAIRE)
    ax.set_xticks(X_ANNEES)
    ax.set_xlim(2013.6, 2024.6)
    ax.set_ylim(-2.05, 2.2)
    ax.set_ylabel('Score relatif (écarts-types)')
    ax.grid(axis='x', visible=False)
    ax.legend(loc='upper center', bbox_to_anchor=(0.45, -0.1), ncol=5, fontsize=7)
    enregistrer(fig, 'cemac_score_relatif.pdf')
    return stats, z_rca


def ecart_aux_seuils(panel, cemac):
    """Pour 2021 : points manquants pour la bande suivante et levier prioritaire."""
    reference, _ = profil_moyen(panel, 'NORMAL')
    lignes = []
    for code, nom in CEMAC.items():
        d = cemac[code]['2021']
        rang = BANDES.index(d['bande'])
        cible = None
        if rang < len(BANDES) - 1:
            borne = SEUILS[rang][1]
            cible = (BANDES[rang + 1], borne - d['tre'])
        excedents = {k: d[k] - reference[k] for k in ('tm', 'tas', 'tfr')}
        levier = max(excedents, key=excedents.get)
        lignes.append({'pays': nom, 'tre': d['tre'], 'bande': d['bande'],
                       'bande_suivante': cible[0] if cible else '', 'points_manquants': cible[1] if cible else 0,
                       'manque_normal': max(0.0, 16 - d['tre']), 'tm': d['tm'], 'tas': d['tas'], 'tfr': d['tfr'],
                       'exc_tm': excedents['tm'], 'exc_tas': excedents['tas'], 'exc_tfr': excedents['tfr'],
                       'levier': levier.upper()})
    return lignes, reference


def ecrire_resultats(cemac, stats, z_rca, lignes, reference):
    os.makedirs(DOSSIER_RESULTATS, exist_ok=True)
    with open(os.path.join(DOSSIER_RESULTATS, 'cemac_leviers_2021.csv'), 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(lignes[0].keys()))
        w.writeheader()
        for l in lignes:
            w.writerow({k: round(v, 1) if isinstance(v, float) else v for k, v in l.items()})
    print('Profil moyen NORMAL :', {k: round(v, 1) for k, v in reference.items()})
    for l in lignes:
        print(f"{l['pays']:20s} TRE {l['tre']:7.1f} {l['bande']:13s} -> {l['bande_suivante']:8s} "
              f"+{l['points_manquants']:5.1f} pts | TM {l['tm']:5.1f} TAS {l['tas']:5.1f} TFR {l['tfr']:5.1f} "
              f"| excès vs NORMAL TM {l['exc_tm']:+.1f} TAS {l['exc_tas']:+.1f} TFR {l['exc_tfr']:+.1f} "
              f"-> levier {l['levier']}")
    print('Moyenne/écart-type par année :', {a: (round(m, 1), round(s, 1)) for a, (m, s) in stats.items()})
    for code, nom in CEMAC.items():
        print(f"  z {nom:20s}", {a: round((cemac[code][a]['tre'] - stats[a][0]) / stats[a][1], 2)
                                  for a in sorted(cemac[code])})


if __name__ == '__main__':
    appliquer_style()
    panel = charger_panel_mondial()
    cemac = charger_cemac()
    figure_trajectoires(cemac)
    figure_usage_2021(panel, cemac)
    stats, z_rca = figure_score_relatif(panel, cemac)
    lignes, reference = ecart_aux_seuils(panel, cemac)
    ecrire_resultats(cemac, stats, z_rca, lignes, reference)
