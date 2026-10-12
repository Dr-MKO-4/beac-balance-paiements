# -*- coding: utf-8 -*-
"""
Regenere fig2_retention_exportations.pdf avec la formule complete du TRE
(TRE = 100 - TM - TAS - TFR), pour remplacer la version produite par
notebooks/graphiques_bdp.ipynb (cellule 17), qui utilisait l'ancienne
formule incomplete (TRE = 100 - TAS - TFR, sans TM) et affichait donc des
valeurs de retention (58,5/58,3/64,3 %) desormais incoherentes avec le
texte et les tableaux du rapport (21,5/9,6/15,2 %).

Les valeurs TC/TM/TAS/TFR/TRE utilisees ici sont celles deja validees et
publiees dans tab:diagnostic_stage de rapport_stage.tex (source :
data/TABLEAU3_DIAGNOSTIC_CEMAC_BEAC.csv), pas une nouvelle extraction --
ce script ne fait que redessiner la figure avec les bonnes valeurs.
"""
import os

import matplotlib.pyplot as plt
import numpy as np
from matplotlib import rcParams

rcParams['font.family'] = 'DejaVu Sans'
rcParams['axes.spines.top'] = False
rcParams['axes.spines.right'] = False
rcParams['axes.grid'] = True
rcParams['grid.linestyle'] = '--'
rcParams['grid.alpha'] = 0.35
rcParams['axes.axisbelow'] = True
rcParams['figure.dpi'] = 150

GABON_C = '#009E60'
TCHAD_C = '#C89600'
RED1 = '#D94040'
BLUE2 = '#6FA8DC'  # nouvelle composante TM

PAYS = ['Congo', 'Gabon', 'Tchad']
FIGURES = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'figures')

# Valeurs validees, tab:diagnostic_stage (rapport_stage.tex)
indicateurs = {
    'Congo': {'tre': 21.5, 'tm': 37.0, 'tas': 19.5, 'tfr': 22.0},
    'Gabon': {'tre': 9.6, 'tm': 48.0, 'tas': 25.7, 'tfr': 16.0},
    'Tchad': {'tre': 15.2, 'tm': 49.1, 'tas': 20.7, 'tfr': 15.0},
}

tre = [indicateurs[p]['tre'] for p in PAYS]
tm = [indicateurs[p]['tm'] for p in PAYS]
tas = [indicateurs[p]['tas'] for p in PAYS]
tfr = [indicateurs[p]['tfr'] for p in PAYS]
x = np.arange(len(PAYS))

fig, ax = plt.subplots(figsize=(8, 5.5))

ax.bar(x, tre, 0.52, label='Taux de rétention',
       color=GABON_C, edgecolor='white', linewidth=0.5, zorder=3)
bottom1 = tre
ax.bar(x, tm, 0.52, bottom=bottom1,
       label='Couverture des importations (TM)',
       color=BLUE2, edgecolor='white', linewidth=0.5, zorder=3)
bottom2 = [bottom1[i] + tm[i] for i in range(len(PAYS))]
ax.bar(x, tas, 0.52, bottom=bottom2,
       label='Absorption services',
       color=TCHAD_C, edgecolor='white', linewidth=0.5, zorder=3)
bottom3 = [bottom2[i] + tas[i] for i in range(len(PAYS))]
ax.bar(x, tfr, 0.52, bottom=bottom3,
       label='Fuite revenu primaire',
       color=RED1, edgecolor='white', linewidth=0.5, zorder=3)

for i, (t, m, s, f) in enumerate(zip(tre, tm, tas, tfr)):
    ax.text(i, t / 2, f'{t:.1f} %', ha='center', va='center',
            fontsize=9, fontweight='bold', color='white')
    ax.text(i, t + m / 2, f'{m:.1f} %', ha='center', va='center',
            fontsize=9, fontweight='bold', color='white')
    ax.text(i, t + m + s / 2, f'{s:.1f} %', ha='center', va='center',
            fontsize=9, fontweight='bold', color='white')
    ax.text(i, t + m + s + f / 2, f'{f:.1f} %', ha='center', va='center',
            fontsize=9, fontweight='bold', color='white')

ax.set_xticks(x)
ax.set_xticklabels(PAYS, fontsize=11)
ax.set_ylabel('% des exportations de biens', fontsize=10)
ax.set_ylim(0, 108)
ax.set_yticks(range(0, 101, 20))
ax.legend(fontsize=8.5, loc='upper right', framealpha=0.85)
ax.set_title("Décomposition des exportations de biens\n"
             "Rétention nationale vs. fuites vers l'extérieur -- 2021",
             fontsize=12, fontweight='bold', pad=14)
fig.text(0.01, -0.02,
          "Source : nos calculs à partir des fichiers BEAC 2021 (formule complète, TM inclus).",
          fontsize=7.5, color='#555555', style='italic')
plt.tight_layout()
plt.savefig(os.path.join(FIGURES, 'fig2_retention_exportations.pdf'), bbox_inches='tight')
plt.close(fig)
print("Figure regeneree :", os.path.join(FIGURES, 'fig2_retention_exportations.pdf'))
