# -*- coding: utf-8 -*-
"""
Clustering multivarie sur les 4 composantes du taux de retention
(TC, TM, TAS, TFR), pour completer la typologie univariee (TRE seul) par
une lecture des PROFILS de fuite : deux pays au meme TRE peuvent perdre
leur valeur exportee pour des raisons tres differentes (deficit commercial
global, deficit de services, ou rapatriement de revenu primaire par les
investisseurs etrangers).

Contrairement a la typologie TRE (univariee, seuils absolus 0/20/50%,
interpretable sans ACP), ces 4 variables ont des echelles tres differentes
(TC/TM peuvent depasser 300%, TAS/TFR restent generalement sous 50%) : une
standardisation (centrage-reduction) est donc necessaire avant clustering,
et une ACP sert ici a VISUALISER les 4 dimensions en 2D -- elle ne remplace
pas le clustering, qui est fait sur les 4 variables standardisees.

Unite d'observation : chaque (pays, annee) du panel mondial (40 pays x 6
annees cibles) + les 6 pays de la CEMAC (annees disponibles), sans
distinction de source -- l'echantillon total depasse 260 observations,
suffisant pour un clustering robuste.

Nombre de clusters : choisi par score de silhouette (k=2 a 6), pas fixe a
priori.
"""
import csv
import os

import matplotlib.pyplot as plt
import numpy as np
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

from extraire_tre_brut_fmi import ANNEES_CIBLES, PANEL_MONDIAL, calculer_tre, extraire_pays

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data')
FIG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'figures')


def observations_panel_mondial():
    obs = []
    for code, label in PANEL_MONDIAL.items():
        data = extraire_pays(code)
        for annee, vals in data.items():
            r = calculer_tre(*vals)
            obs.append({'label': label, 'annee': annee, 'source': 'Panel mondial', **r})
    return obs


def observations_cemac_beac():
    path = os.path.join(DATA_DIR, 'TRE_CEMAC_RECALCULE.csv')
    rows = list(csv.DictReader(open(path, encoding='utf-8-sig')))
    obs = []
    for r in rows:
        label = r['pays']
        exp_b = float(r['exp_biens']); imp_b = float(r['imp_biens'])
        solde_s = float(r['solde_services']); solde_r = float(r['solde_revenu_primaire'])
        tc = exp_b / imp_b * 100 if imp_b else None
        tm = imp_b / exp_b * 100 if exp_b else None
        tas = max(0.0, -solde_s) / exp_b * 100 if exp_b else None
        tfr = max(0.0, -solde_r) / exp_b * 100 if exp_b else None
        if None in (tc, tm, tas, tfr):
            continue
        tre = 100 - tm - tas - tfr
        obs.append({'label': label, 'annee': r['annee'], 'source': 'CEMAC (BEAC)',
                    'tc': tc, 'tm': tm, 'tas': tas, 'tfr': tfr, 'tre': tre})
    return obs


if __name__ == '__main__':
    os.makedirs(FIG_DIR, exist_ok=True)

    obs = observations_panel_mondial() + observations_cemac_beac()
    # Cameroun apparait deja dans le panel mondial (source FMI) -- on ne
    # le duplique pas via CEMAC (BEAC) qui ne le contient pas de toute facon.

    X_raw = np.array([[o['tc'], o['tm'], o['tas'], o['tfr']] for o in obs])
    scaler = StandardScaler()
    X = scaler.fit_transform(X_raw)

    print(f"Nombre d'observations pays-annee : {len(obs)}")

    # Choix de k par score de silhouette ---
    scores = {}
    for k in range(2, 7):
        km = KMeans(n_clusters=k, n_init=10, random_state=42).fit(X)
        scores[k] = silhouette_score(X, km.labels_)
    for k, s in scores.items():
        print(f"  k={k} : silhouette={s:.3f}")
    k_opt = max(scores, key=scores.get)
    print(f"k retenu (meilleur score de silhouette) : {k_opt}")

    km = KMeans(n_clusters=k_opt, n_init=10, random_state=42).fit(X)
    for o, lab in zip(obs, km.labels_):
        o['cluster'] = int(lab)

    # Caracterisation des clusters (moyennes en echelle d'origine) ---
    print()
    print("=== Profils moyens par cluster (echelle d'origine, %) ===")
    for c in range(k_opt):
        membres = [o for o in obs if o['cluster'] == c]
        tc_m = np.mean([o['tc'] for o in membres])
        tm_m = np.mean([o['tm'] for o in membres])
        tas_m = np.mean([o['tas'] for o in membres])
        tfr_m = np.mean([o['tfr'] for o in membres])
        tre_m = np.mean([o['tre'] for o in membres])
        print(f"Cluster {c} (n={len(membres)}) : TC={tc_m:6.1f}  TM={tm_m:6.1f}  TAS={tas_m:5.1f}  TFR={tfr_m:5.1f}  -> TRE_moy={tre_m:6.1f}")
        # pays CEMAC dans ce cluster
        cemac_membres = sorted(set(o['label'] for o in membres if o['source'] == 'CEMAC (BEAC)' or o['label'] == 'Cameroun'))
        if cemac_membres:
            print(f"    Pays CEMAC presents : {', '.join(cemac_membres)}")

    # ACP pour visualisation 2D ---
    pca = PCA(n_components=2)
    coords = pca.fit_transform(X)
    var_exp = pca.explained_variance_ratio_
    print()
    print(f"Variance expliquee par les 2 premiers axes : {var_exp[0]*100:.1f}% + {var_exp[1]*100:.1f}% = {sum(var_exp)*100:.1f}%")
    print("Contribution des variables aux axes (loadings) :")
    for i, var in enumerate(['TC', 'TM', 'TAS', 'TFR']):
        print(f"  {var:5s} : axe1={pca.components_[0][i]:+.2f}  axe2={pca.components_[1][i]:+.2f}")

    fig, ax = plt.subplots(figsize=(10, 8))
    cmap = plt.get_cmap('tab10')
    for c in range(k_opt):
        idx = [i for i, o in enumerate(obs) if o['cluster'] == c]
        ax.scatter(coords[idx, 0], coords[idx, 1], s=25, alpha=0.6, color=cmap(c), label=f"Cluster {c}")
    # surligner la CEMAC
    cemac_idx = [i for i, o in enumerate(obs) if o['source'] == 'CEMAC (BEAC)' or o['label'] == 'Cameroun']
    ax.scatter(coords[cemac_idx, 0], coords[cemac_idx, 1], s=70, facecolors='none',
               edgecolors='black', linewidths=1.3, label='Pays CEMAC')
    for i in cemac_idx:
        ax.annotate(f"{obs[i]['label'][:3]}{obs[i]['annee'][2:]}", (coords[i, 0], coords[i, 1]), fontsize=6)
    ax.set_xlabel(f"Axe 1 ({var_exp[0]*100:.0f}% variance)")
    ax.set_ylabel(f"Axe 2 ({var_exp[1]*100:.0f}% variance)")
    ax.set_title(f"Clustering multivarie des profils de fuite (TC, TM, TAS, TFR)\nk={k_opt} clusters, projection ACP -- CEMAC encerclee")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG_DIR, 'clustering_profils_fuite.pdf'))
    plt.close(fig)

    print()
    print("Graphique enregistre :", os.path.join(FIG_DIR, 'clustering_profils_fuite.pdf'))
