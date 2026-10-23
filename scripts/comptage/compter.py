"""Compte les mots latins de textes/ en ne retenant qu'une fois chaque texte.

1. Extraction parallèle : pour chaque œuvre, texte latin -> blocs de ~1000 mots -> empreintes.
2. Dédoublonnage séquentiel, corpus par corpus dans l'ordre de priorité : un bloc dont au moins
   50 % des 5-grammes échantillonnés (80 % pour les blocs de moins de 100 mots) ont déjà été vus
   est un doublon et n'est pas compté.
"""
import json
import os
import sys
import time
from multiprocessing import Pool

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import extraire as X  # noqa: E402

BITS = 34


def tache(args):
    corpus, chemin = args
    f = dict((c, fn) for c, _, fn in X.CORPUS)[corpus]
    sortie = []
    try:
        it = f() if chemin is None else f(chemin)
        for ident, toks in it:
            blocs = [(n, np.array(e, dtype=np.uint64), k) for n, e, k in X.empreintes(toks)] if toks else []
            sortie.append((ident, blocs))
    except Exception as e:  # un fichier illisible ne doit pas arrêter le comptage
        print(f"ERREUR {corpus} {chemin}: {e!r}", file=sys.stderr, flush=True)
    return corpus, sortie


def main():
    t0 = time.time()
    taches = [(c, None) for c, liste, _ in X.CORPUS if liste is None]
    for c, liste, _ in X.CORPUS:
        if liste is not None:
            taches += [(c, f) for f in liste()]
    print(f"{len(taches)} tâches", flush=True)

    resultats = {c: [] for c, _, _ in X.CORPUS}
    with Pool(7) as pool:
        for i, (c, sortie) in enumerate(pool.imap(tache, taches, chunksize=8)):
            resultats[c].extend(sortie)
            if i % 10000 == 0:
                print(f"  {i}/{len(taches)}  {time.time() - t0:.0f}s", flush=True)
    print(f"extraction terminée en {time.time() - t0:.0f}s", flush=True)

    vu = np.zeros(2 ** BITS // 8, dtype=np.uint8)
    masque = np.uint64(2 ** BITS - 1)
    cles = set()
    stats = []
    for c, _, _ in X.CORPUS:
        brut = uniques = n_oeuvres = n_oeuvres_uniques = 0
        for ident, blocs in resultats[c]:
            n_tot = n_uni = 0
            for n, ech, cle in blocs:
                n_tot += n
                if len(ech):
                    idx = ech & masque
                    octet, bit = (idx >> np.uint64(3)).astype(np.int64), (idx & np.uint64(7)).astype(np.uint8)
                    frac = float(((vu[octet] >> bit) & 1).mean())
                    doublon = frac >= (0.8 if n < 100 else 0.5)
                else:
                    doublon = cle in cles
                if not doublon:
                    n_uni += n
                    if len(ech):
                        np.bitwise_or.at(vu, octet, (np.uint8(1) << bit))
                    cles.add(cle)
            if n_tot:
                n_oeuvres += 1
                n_oeuvres_uniques += n_uni * 2 > n_tot
            brut += n_tot
            uniques += n_uni
        stats.append(dict(corpus=c, oeuvres=n_oeuvres, oeuvres_uniques=n_oeuvres_uniques,
                          mots_bruts=brut, mots_uniques=uniques))
        print(f"{c:32} œuvres {n_oeuvres:7d} (uniques {n_oeuvres_uniques:7d})  "
              f"mots {brut:12,d}  uniques {uniques:12,d}", flush=True)
        resultats[c] = None
    tot_b = sum(s["mots_bruts"] for s in stats)
    tot_u = sum(s["mots_uniques"] for s in stats)
    print(f"TOTAL mots bruts {tot_b:,d}  mots uniques {tot_u:,d}  ({time.time() - t0:.0f}s)")
    json.dump(stats, open(sys.argv[1], "w"), indent=1, ensure_ascii=False)


if __name__ == "__main__":
    main()
