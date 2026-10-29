"""Contrôle des corrections sur les œuvres présentes à la fois dans le CSEL et dans Perseus.

Pour chaque correction d'une œuvre commune, on regarde la leçon de Perseus (autre édition, saisie à la main) :
  confirmée  : la forme corrigée figure dans l'œuvre de Perseus, la forme d'origine non ;
  démentie   : la forme d'origine figure dans Perseus, la forme corrigée non ;
  muette     : ni l'une ni l'autre (passage absent, autre leçon de l'éditeur).
Usage : valider.py
"""
import collections
import csv
import glob
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import corriger_csel as C  # noqa: E402
import extraire as X  # noqa: E402  (scripts/comptage, ajouté au chemin par corriger_csel)


def formes(chemin):
    s = collections.Counter()
    for _, toks in X.oeuvres_tei(chemin):
        s.update(toks)
    return s


def main():
    rs = list(csv.DictReader(open(C.TSV, encoding="utf-8"), delimiter="\t", quoting=csv.QUOTE_NONE,
                             escapechar="\\"))
    par_oeuvre = collections.defaultdict(list)
    for r in rs:
        par_oeuvre[".".join(os.path.basename(r["fichier"]).split(".")[:2])].append(r)
    bilan = collections.Counter()
    exemples = collections.defaultdict(list)
    for oeuvre, lignes in sorted(par_oeuvre.items()):
        g, w = oeuvre.split(".")
        ps = glob.glob(os.path.join(C.PERSEUS, g, w, "*-lat*.xml"))
        if not ps:
            continue
        P = collections.Counter()
        for p in ps:
            P.update(formes(p))
        for r in lignes:
            if r["type"] == "cesure":
                continue
            orig = X.mots(r["original"].replace("<sic>", " ").replace("</sic>", " "))
            corr = X.mots(r["correction"])
            if r["type"].startswith("colle"):          # le mot collé seul ; les morceaux sont des mots courants
                o_ok, c_ok = all(P[o] for o in orig), False
                c_ok = not o_ok and all(P[c] for c in corr)
            else:
                o_ok, c_ok = all(P[o] for o in orig), all(P[c] for c in corr)
            etat = "confirmée" if c_ok and not o_ok else "démentie" if o_ok and not c_ok else "muette"
            t = r["type"].split("-")[0]
            bilan[(t, etat)] += 1
            exemples[(t, etat)].append(f"{oeuvre} {r['original']} → {r['correction']}")
    for t in ("lettre", "colle", "coupe"):
        c, d, m = (bilan[(t, e)] for e in ("confirmée", "démentie", "muette"))
        prec = f"{100 * c / (c + d):.1f} %" if c + d else "–"
        print(f"{t:7} confirmées {c:4}  démenties {d:3}  muettes {m:4}  précision {prec}")
        for etat in ("démentie", "muette") if "-v" in sys.argv else ("démentie",):
            for e in exemples[(t, etat)]:
                print(f"   {etat} :", e)


if __name__ == "__main__":
    main()
