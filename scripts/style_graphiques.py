# -*- coding: utf-8 -*-
"""Charte graphique commune à toutes les figures de l'analyse.

Les palettes ont été vérifiées (séparation des couleurs adjacentes, y
compris pour les daltonismes les plus fréquents). Les couleurs ne portent
jamais seules l'information : chaque figure affiche une légende ou des
étiquettes directes.
"""
import os

import matplotlib.pyplot as plt
from matplotlib import rcParams

DOSSIER_FIGURES = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'figures')

# Encre et repères
ENCRE = '#0b0b0b'
ENCRE_SECONDAIRE = '#52514e'
ENCRE_DISCRETE = '#898781'
GRILLE = '#e1e0d9'
AXE = '#c3c2b7'
FOND = '#ffffff'
NEUTRE_CLAIR = '#e9e8e3'

# Bandes de rétention : échelle divergente (deux rouges, un neutre, deux bleus)
COULEURS_BANDES = {
    'TRÈS CRITIQUE': '#9e1f1f',
    'CRITIQUE': '#e0675e',
    'FAIBLE': '#a8a69c',
    'NORMAL': '#5598e7',
    'BON': '#184f95',
}

# Usages de la valeur exportée (ordre d'empilement validé)
COULEURS_COMPOSANTES = {
    'TM': '#eb6834',    # financement des importations de biens
    'TAS': '#1baf7a',   # absorption par les services
    'TFR': '#eda100',   # fuite du revenu primaire
    'TRE': '#2a78d6',   # part retenue
}
LIBELLES_COMPOSANTES = {
    'TM': 'Importations de biens (TM)',
    'TAS': 'Déficit des services (TAS)',
    'TFR': 'Revenus rapatriés (TFR)',
    'TRE': 'Part retenue (TRE)',
}

# Pays de la CEMAC (ordre catégoriel fixe, validé)
COULEURS_CEMAC = {
    'Cameroun': '#2a78d6',
    'Congo': '#eb6834',
    'Gabon': '#1baf7a',
    'Guinée Équatoriale': '#eda100',
    'Tchad': '#e87ba4',
    'RCA': '#008300',
}


def appliquer_style():
    rcParams.update({
        'font.family': 'DejaVu Sans',
        'font.size': 9,
        'axes.titlesize': 10,
        'axes.titleweight': 'bold',
        'axes.labelsize': 9,
        'axes.labelcolor': ENCRE_SECONDAIRE,
        'axes.edgecolor': AXE,
        'axes.linewidth': 0.8,
        'axes.spines.top': False,
        'axes.spines.right': False,
        'axes.grid': True,
        'axes.axisbelow': True,
        'grid.color': GRILLE,
        'grid.linewidth': 0.6,
        'xtick.color': ENCRE_DISCRETE,
        'ytick.color': ENCRE_DISCRETE,
        'xtick.labelcolor': ENCRE_SECONDAIRE,
        'ytick.labelcolor': ENCRE_SECONDAIRE,
        'legend.frameon': False,
        'legend.fontsize': 8,
        'figure.facecolor': FOND,
        'axes.facecolor': FOND,
        'savefig.facecolor': FOND,
        'figure.dpi': 150,
        'pdf.fonttype': 42,
    })


def enregistrer(fig, nom):
    os.makedirs(DOSSIER_FIGURES, exist_ok=True)
    chemin = os.path.join(DOSSIER_FIGURES, nom)
    fig.savefig(chemin, bbox_inches='tight')
    plt.close(fig)
    print('Figure :', os.path.normpath(chemin))
