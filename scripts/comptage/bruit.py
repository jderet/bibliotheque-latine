"""Part des mots de chaque corpus dont la forme n'apparaît dans aucun autre corpus
(indicateur grossier de bruit OCR, à comparer au niveau de base des corpus saisis à la main)."""
import os, sys, json, collections
from multiprocessing import Pool
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import extraire as X

def tache(args):
    corpus, chemin = args
    f = dict((c, fn) for c, _, fn in X.CORPUS)[corpus]
    cpt = collections.Counter()
    try:
        for _, toks in (f() if chemin is None else f(chemin)):
            cpt.update(toks)
    except Exception as e:
        print("ERREUR", corpus, chemin, repr(e), file=sys.stderr)
    return corpus, cpt

if __name__ == "__main__":
    taches = [(c, None) for c, l, _ in X.CORPUS if l is None] + [(c, f) for c, l, _ in X.CORPUS if l for f in l()]
    par = {c: collections.Counter() for c, _, _ in X.CORPUS}
    with Pool(7) as p:
        for c, cpt in p.imap_unordered(tache, taches, chunksize=16):
            par[c].update(cpt)
    nb_corpus = collections.Counter()
    for cpt in par.values():
        nb_corpus.update(cpt.keys())
    res = {}
    for c, cpt in par.items():
        tot = sum(cpt.values()) or 1
        seul = sum(n for w, n in cpt.items() if nb_corpus[w] == 1)
        res[c] = round(100 * seul / tot, 2)
        print(f"{c:32} {tot:12,d} mots  {res[c]:6.2f} % de formes absentes des autres corpus")
    json.dump(res, open(sys.argv[1], "w"), indent=1)
