"""Corrections OCR évidentes du CSEL (textes/ogl-csel) : mots collés, mots coupés, confusions de lettres.

  corriger_csel.py detecter   → scripts/ocr/csel-corrections.tsv, à relire (colonne garder : o/n)
  corriger_csel.py appliquer  → encode dans les TEI les corrections gardées

Seul le texte principal est lu : en-tête, notes (apparat), <hi> (sigles et variantes en italique),
grec, titres et additions sont laissés tels quels, ainsi que les mots voisins d'un crochet, d'une
parenthèse ou d'un chiffre (restitutions de l'éditeur abîmées par l'OCR : « p&lt;ostea fu&gt;turi »).

Encodage TEI des corrections, qui garde la leçon d'origine :
  mot collé, coupé ou mal lu   <choice><sic>consilioMoyses</sic><corr>consilio Moyses</corr></choice>
  <sic> déjà posé par OGL      <choice><sic>patremriserat</sic><corr>patrem riserat</corr></choice>
  césure en fin de ligne       con<lb break="no"/>stringere   (au lieu de « con- <lb/>stringere »)

Une correction n'est retenue que si elle est sans ambiguïté :
  - la forme d'origine est inconnue : absente de Perseus, de Collatinus, et de moins de 3 œuvres du CSEL ;
  - la ou les formes corrigées sont attestées dans Perseus (ou Collatinus pour les mots collés) ;
  - aucune autre correction n'est presque aussi probable (fréquence Perseus au moins 10 fois moindre).
"""
import argparse
import collections
import collections.abc
import csv
import glob
import json
import math
import os
import re
import sys
import unicodedata
from multiprocessing import Pool

collections.Callable = collections.abc.Callable  # PyCollatinus 0.1.6 date d'avant Python 3.10

ICI = os.path.dirname(os.path.abspath(__file__))
RACINE = os.path.normpath(os.path.join(ICI, "..", ".."))
CSEL = os.path.join(RACINE, "textes", "ogl-csel", "data")
PERSEUS = os.path.join(RACINE, "textes", "perseus-canonical-latinlit", "data")
CACHE = os.path.join(RACINE, ".cache", "ocr")
TSV = os.path.join(ICI, "csel-corrections.tsv")
DATE = "2026-10-29"

sys.path.insert(0, os.path.join(RACINE, "scripts", "comptage"))

# ------------------------------------------------------------------ normalisation et lexique

_TRANS = str.maketrans({"æ": "ae", "œ": "oe", "j": "i", "v": "u", "ſ": "s"})


def norm(t):
    t = unicodedata.normalize("NFKD", t.lower())
    return "".join(c for c in t if not unicodedata.combining(c)).translate(_TRANS)


def _compter_perseus(chemin):
    import extraire as X
    cpt = collections.Counter()
    for _, toks in X.oeuvres_tei(chemin):
        cpt.update(toks)
    return cpt


def perseus():
    """Fréquences des formes (normalisées) dans Perseus, texte saisi à la main."""
    chemin = os.path.join(CACHE, "perseus.json")
    if os.path.exists(chemin):
        return collections.Counter(json.load(open(chemin, encoding="utf-8")))
    fichiers = sorted(glob.glob(os.path.join(PERSEUS, "**", "*-lat*.xml"), recursive=True))
    total = collections.Counter()
    with Pool() as p:
        for c in p.imap_unordered(_compter_perseus, fichiers, chunksize=8):
            total.update(c)
    os.makedirs(CACHE, exist_ok=True)
    json.dump(total, open(chemin, "w", encoding="utf-8"))
    return total


class Lexique:
    ENCLITIQUES = ("que", "ue", "ne")

    def __init__(self, csel_oeuvres):
        from pycollatinus import Lemmatiseur
        self.L = Lemmatiseur()
        self.P = perseus()
        self.oeuvres = csel_oeuvres          # forme → nombre d'œuvres du CSEL où elle figure
        self._c = {}

    def collatinus(self, f):
        if f not in self._c:
            try:
                self._c[f] = next(iter(self.L.lemmatise(f)), None) is not None
            except Exception:
                self._c[f] = False
        return self._c[f]

    def atteste(self, f, avec_collatinus=True):
        """Forme réelle : dans Perseus, dans Collatinus (éventuellement avec enclitique)."""
        if self.P[f] or (avec_collatinus and self.collatinus(f)):
            return True
        return any(f.endswith(e) and len(f) > len(e) + 1 and (self.P[f[:-len(e)]] or
                   (avec_collatinus and self.collatinus(f[:-len(e)]))) for e in self.ENCLITIQUES)

    def connu(self, f):
        return self.atteste(f) or self.oeuvres[f] >= 3

    def freq(self, f):
        n = self.P[f]
        if not n:
            for e in self.ENCLITIQUES:
                if f.endswith(e) and len(f) > len(e) + 1:
                    n = max(n, self.P[f[:-len(e)]])
        return n


# ------------------------------------------------------------------ lecture du texte principal

SAUTER = {"teiHeader", "note", "hi", "foreign", "head", "title", "bibl", "add", "unclear", "ref", "label",
          "fw", "figure", "num", "abbr", "gap", "del", "orig", "reg", "choice", "corr", "quote", "persName",
          "name", "date", "speaker", "stage", "milestone", "cit"}
BALISE = re.compile(r"<(/?)([A-Za-z][\w:.-]*)([^>]*?)(/?)>|<!--.*?-->|<\?.*?\?>", re.S)
MOT = re.compile(r"[A-Za-zÀ-ÖØ-öø-ÿ]+")
SUSPECTS = set("<>[]()*|&;'’†/\\{}+=_\"-\u00ad¬") | set("0123456789")


def morceaux(brut):
    """[(début, fin, dans_sic)] des passages de texte principal lus (hors balises sautées)."""
    pile, res, pos, dans_corps = [], [], 0, False
    for m in BALISE.finditer(brut):
        if dans_corps and m.start() > pos and not any(n in SAUTER for n in pile):
            res.append((pos, m.start(), bool(pile) and pile[-1] == "sic"))
        pos = m.end()
        if not m.group(2):
            continue
        nom = m.group(2).split(":")[-1]
        if nom == "body":
            dans_corps = not m.group(1)
        if m.group(4):          # balise vide
            continue
        if m.group(1):
            while pile and pile.pop() != nom:
                pass
        else:
            pile.append(nom)
    return res


def jetons(brut, debut, fin):
    """Mots d'un passage, avec un drapeau « voisin suspect » (crochet, chiffre, entité…)."""
    for m in MOT.finditer(brut, debut, fin):
        # collé à une balise (origi<lb/>ne, supersti</p>) : fragment possible, donc suspect aussi
        av = brut[m.start() - 1] if m.start() > debut else "<"
        ap = brut[m.end()] if m.end() < fin else "<"
        cesure = brut[m.end():m.end() + 3].lstrip()[:1] in ("-", "\u00ad", "¬")   # amaritu ­dine
        yield m.start(), m.end(), m.group(), av in SUSPECTS or ap in SUSPECTS or cesure


# ------------------------------------------------------------------ détection

PREFIXES = set("a ab abs ad ante circum com con contra de di dis e ex extra in inter intra ob per post prae "
               "praeter pro re se sub subter super supra trans ultra ne non bene male satis".split())
FONCTION = set("quo qua quae qui quod quibus quem quam eo ea eis eius se te me nos uos nobis uobis hoc his "
               "illo illa illis ipso ipsa deo deum christo christi domino nihil omnibus omni".split())
LIAISONS = set("que ue ne met pte ce dem dam piam quam libet cumque uis nam".split())
# Confusions visuelles de l'OCR (pas les variantes graphiques : u/o, e/i, ae/e… restent intactes)
PAIRES = [("o", "c"), ("c", "o"), ("e", "c"), ("c", "e"), ("o", "e"), ("e", "o"), ("n", "u"), ("u", "n"),
          ("l", "i"), ("i", "l"), ("rn", "m"), ("m", "rn"), ("in", "m"), ("ri", "n"), ("ii", "u"),
          ("li", "h"), ("h", "li"), ("b", "h"), ("h", "b"), ("t", "f"), ("f", "t"), ("cl", "d"), ("d", "cl"),
          ("f", "s"), ("s", "f"), ("s", "a"), ("c", "g"), ("tl", "d"), ("q", "g"), ("g", "q")]


COURTS = set("a e o ab ad at de do ea eo es et ex hi id ii in me ne ob se si te tu ut".split())
# Mots outils : un mot collé du CSEL en contient presque toujours un (ueritasnon, iustitiamet, deChristo)
OUTILS = set("""a ab ac ad ante apud at atque aut autem cum de dum e ea eam eas eis eius eo eorum eos erat ergo esse
est et etiam eum ex hic hoc haec his iam id igitur ille illa illi illud in inter ipse ipsa ipsum ipsi is ita
me mihi mea meum meus mei meis nam ne nec neque nihil nisi nobis non nos noster nostra nostri nunc per post pro
post propter qua quae quam quasi qui quia quibus quid quidem quis quo quod quoniam se sed sic sibi si sicut sine sit sub
sum sunt super tamen tam te tibi tu tua tuum tuus tui uel uero ut uos uobis deus dei deo deum domini dominus
domino dominum christus christi christo christum ubi unde sunt fuit uelut tamquam quoque enim inquit item ideo
semper adhuc deinde tunc ibi quando quomodo quare utique immo scilicet licet cur num an""".split())


def segmentations(n, lex):
    """Découpages de n en deux ou trois mots fréquents de Perseus, dont au moins un mot outil (deux pour trois
    morceaux). Les morceaux de moins de trois lettres sont des mots outils (et, in, si…), pas des syllabes
    (um, os, st) ; une lettre seule (a, e) n'ouvre que le premier morceau."""
    res = []

    def rec(reste, acc):
        if not reste:
            outils = sum(p in OUTILS for p in acc)
            pleins = [p for p in acc if p not in OUTILS]
            refus = (
                # un mot outil de deux lettres ne s'accole qu'à un mot long ou très fréquent (mestas ≠ me stas)
                any(len(p) <= 2 for p in acc if p in OUTILS) and any(len(p) < 5 and lex.freq(p) < 1000 for p in pleins)
                # un mot plein court et rare est plutôt un fragment (sibiaue, estros, fariam)
                or any(len(p) < 4 and lex.freq(p) < 1000 for p in pleins)
                # infinitif parfait en -isse, -asse (exilisse, dignosse), pas « … se »
                or acc[-1] == "se" and n.endswith("sse")
                # trois morceaux avec un pronom de deux lettres : syllabes (intelectus ≠ in te lectus)
                or len(acc) == 3 and any(p in ("me", "te", "se") for p in acc))
            if len(acc) >= 2 and outils >= len(acc) - 1 and not refus:
                res.append(acc)
            return
        if len(acc) == 3:
            return
        for i in range(1, len(reste) + 1):
            p = reste[:i]
            if (len(p) < 3 and p not in COURTS) or p in LIAISONS or lex.freq(p) < 20 or (len(p) == 1 and acc):
                continue
            if acc and acc[-1] in PREFIXES and p not in FONCTION:
                continue
            rec(reste[i:], acc + [p])

    rec(n, [])
    return res


def meilleur(candidats, cle):
    """Le candidat le plus fréquent s'il l'est au moins 10 fois plus que le suivant, sinon None."""
    if not candidats:
        return None
    c = sorted(candidats, key=cle, reverse=True)
    if len(c) > 1 and cle(c[0]) < 10 * max(cle(c[1]), 1):
        return None
    return c[0]


def casse(modele, mot):
    """Majuscule initiale du modèle, sauf si c'est la lettre mal lue (Iuminibus → luminibus)."""
    return mot[:1].upper() + mot[1:] if modele[:1].isupper() and modele[:1].lower() == mot[:1] else mot


GRAPHIES = [("mt", "mpt"), ("ms", "mps"), ("mn", "mpn"), ("e", "ae"), ("ae", "e"), ("oe", "e"), ("y", "i"),
            ("i", "y"), ("ci", "ti"), ("ti", "ci"), ("f", "ph"), ("ph", "f"), ("ch", "c"), ("c", "ch"),
            ("th", "t"), ("t", "th"), ("h", ""), ("nn", "n"), ("ll", "l"), ("l", "ll"), ("ss", "s"), ("s", "ss"),
            ("tt", "t"), ("cc", "c"), ("pp", "p"), ("rr", "r"), ("r", "rr"), ("x", "s"), ("b", "u"), ("u", "b"),
            ("d", "t"), ("t", "d"), ("o", "u"), ("u", "o"), ("i", "e"), ("e", "i"), ("adp", "app"), ("conp", "comp"),
            ("inp", "imp"), ("inm", "imm"), ("adt", "att"), ("adc", "acc"), ("adf", "aff"), ("ads", "ass")]


def graphie(n, lex):
    """Vraie si n est une autre graphie (assumtam, clamidis, discendit) d'une forme de Perseus."""
    for a, z in GRAPHIES:
        for m in re.finditer(re.escape(a), n):
            if lex.P[n[:m.start()] + z + n[m.end():]] >= 3:
                return True
    return False


def colle(t, n, lex):
    """Mot collé → forme corrigée avec espaces, ou None."""
    if re.search(r"[a-z][A-Z]", t):                 # consilioMoyses, inSamaria
        morceaux_ = re.sub(r"([a-z])([A-Z])", r"\1 \2", t).split()
        if all(lex.P[norm(m)] >= 3 and (len(m) >= 4 or m[0].islower() and (len(m) >= 3 or m in COURTS))
               for m in morceaux_):
            return " ".join(morceaux_)
        return None
    if t[:1].isupper():                             # nom propre rare (Sedima, Hereda) : pas de découpage
        return None
    segs = segmentations(n, lex)
    if not segs:
        return None
    court = min(len(s) for s in segs)
    segs = [s for s in segs if len(s) == court]
    s = meilleur(segs, lambda s: min(lex.freq(p) for p in s))
    if s is None:
        return None
    # recoupe la forme d'origine (u/v, j, majuscule) aux mêmes positions
    out, i = [], 0
    for p in s:
        out.append(t[i:i + len(p)])
        i += len(p)
    return " ".join(out)


def lettre(t, n, lex):
    """Confusion de lettres → forme corrigée, ou None."""
    if len(n) < 3:
        return None
    b = t.lower()
    cands = set()
    for a, z in PAIRES:
        for m in re.finditer(re.escape(a), b):
            cands.add(b[:m.start()] + z + b[m.end():])
        if b.count(a) > 1:                          # même confusion répétée (peocatoruro → peccatorum)
            cands.add(b.replace(a, z))
    cands = {c for c in cands if lex.P[norm(c)] >= 20}
    c = meilleur(cands, lambda c: lex.P[norm(c)])
    if c is None or (len(n) == 3 and lex.P[norm(c)] < 1000) or (len(n) == 4 and lex.P[norm(c)] < 200):
        return None
    if t[:1].isupper() and lex.P[norm(c)] < 100:    # nom propre rare (Aniani) : on n'y touche pas
        return None
    return casse(t, c)


def analyser(chemin, lex=None, compter=False):
    brut = open(chemin, encoding="utf-8").read()
    morc = morceaux(brut)
    toks = []
    for d, f, sic in morc:
        for a, z, t, susp in jetons(brut, d, f):
            toks.append((a, z, t, susp, sic, d, f))
    if compter:
        return {norm(t) for _, _, t, _, _, _, _ in toks}
    rel = os.path.relpath(chemin, CSEL)
    ligne = lambda pos: brut.count("\n", 0, pos) + 1
    res, pris = [], []                              # zones déjà corrigées : césure et coupure passent d'abord

    def ajouter(type_, a, z, orig, corr, info):
        if any(a < z2 and a2 < z for a2, z2 in pris):
            return
        pris.append((a, z))
        ctx = re.sub(r"\s+", " ", re.sub(r"<[^>]*>", " ", brut[max(0, a - 80):a])).strip()[-50:] + " ⟦" + orig + "⟧ " + \
            re.sub(r"\s+", " ", re.sub(r"<[^>]*>", " ", brut[z:z + 80])).strip()[:50]
        res.append({"garder": "o", "fichier": rel, "ligne": ligne(a), "debut": a, "fin": z, "type": type_,
                    "original": orig, "correction": corr, "info": info, "contexte": ctx})

    # 1. césures en fin de ligne : « con- <lb/>stringere »
    for m in re.finditer(r"([A-Za-z]+)-[ \t]*(<lb\b[^>]*?)/>(\s*)([a-z]+)", brut):
        n = norm(m.group(1) + m.group(4))
        dans = any(d <= m.start(1) < f for d, f, _ in morc)
        if dans and lex.atteste(n):
            lb = m.group(2) if "break=" in m.group(2) else m.group(2) + ' break="no"'
            ajouter("cesure", m.start(), m.end(), m.group(0),
                    m.group(1) + lb + "/>" + m.group(4), f"{n} P={lex.P[n]}")

    # 2. mots coupés par une espace : « ta men »
    fragment = lambda i: 0 <= i < len(toks) and not lex.connu(norm(toks[i][2])) and len(toks[i][2]) <= 3
    for i, ((a1, z1, t1, s1, sic1, d1, _), (a2, z2, t2, s2, sic2, d2, _)) in enumerate(zip(toks, toks[1:])):
        if fragment(i - 1) or fragment(i + 2):
            continue
        if d1 != d2 or s1 or s2 or sic1 or sic2 or not brut[z1:a2].strip() == "" or "\n" in brut[z1:a2]:
            continue
        if not t2[:1].islower() or t1.isupper():
            continue
        n1, n2, n = norm(t1), norm(t2), norm(t1 + t2)
        if (lex.connu(n1) and lex.connu(n2)) or lex.P[n] < 3:
            continue
        ajouter("coupe", a1, z2, brut[a1:z2], t1 + t2, f"{n} P={lex.P[n]}")

    # 3. mots collés et confusions de lettres
    for a, z, t, susp, sic, d, f in toks:
        n = norm(t)
        if susp or len(n) < 3 or t.isupper() or lex.connu(n) or lex.oeuvres[n] >= 2 or graphie(n, lex):
            continue
        if re.search(r"[A-Z]", t[1:]) and not re.search(r"[a-z][A-Z]", t):
            continue
        # suse → suae plutôt que « sus e », mais exquo → « ex quo » (que des mots outils) plutôt que exque
        corr, type_ = colle(t, n, lex), "colle"
        if corr is None or not all(norm(p) in OUTILS for p in corr.split()):
            l = lettre(t, n, lex)
            if l is not None:
                corr, type_ = l, "lettre"
        if corr is None:
            continue
        info = " ".join(f"{norm(p)} P={lex.P[norm(p)]}" for p in corr.split())
        if sic and brut[d:f].strip() == t:          # tout le contenu d'un <sic> d'OGL
            a, z = brut.rfind("<sic", 0, d), brut.find("</sic>", f) + len("</sic>")
            type_ += "-sic"
            ajouter(type_, a, z, brut[a:z], corr, info)
        else:
            ajouter(type_, a, z, t, corr, info)
    return res


# ------------------------------------------------------------------ commandes

def fichiers_csel():
    return sorted(glob.glob(os.path.join(CSEL, "*", "*", "*-lat*.xml")))


def _formes(chemin):
    return analyser(chemin, compter=True)


LEX = None


def _init(oeuvres):
    global LEX
    LEX = Lexique(oeuvres)


def _detecter(chemin):
    return analyser(chemin, LEX)


def detecter(args):
    fs = fichiers_csel()
    oeuvres = collections.Counter()
    with Pool() as p:
        for formes in p.imap_unordered(_formes, fs, chunksize=4):
            oeuvres.update(formes)
    perseus()  # calculé une fois avant d'ouvrir les processus
    with Pool(initializer=_init, initargs=(oeuvres,)) as p:
        lignes = [r for res in p.imap(_detecter, fs, chunksize=2) for r in res]
    champs = ["garder", "fichier", "ligne", "debut", "fin", "type", "original", "correction", "info", "contexte"]
    with open(TSV, "w", encoding="utf-8", newline="") as out:
        w = csv.DictWriter(out, champs, delimiter="\t", quoting=csv.QUOTE_NONE, escapechar="\\")
        w.writeheader()
        w.writerows(lignes)
    cpt = collections.Counter(r["type"].split("-")[0] for r in lignes)
    print(f"{len(lignes)} corrections dans {len({r['fichier'] for r in lignes})} fichiers : "
          + ", ".join(f"{k} {v}" for k, v in cpt.most_common()), file=sys.stderr)


def encoder(r):
    if r["type"] == "cesure":
        return r["correction"]
    if r["type"].endswith("-sic"):
        return f"<choice>{r['original']}<corr>{r['correction']}</corr></choice>"
    return f"<choice><sic>{r['original']}</sic><corr>{r['correction']}</corr></choice>"


def appliquer(args):
    par = collections.defaultdict(list)
    with open(TSV, encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f, delimiter="\t", quoting=csv.QUOTE_NONE, escapechar="\\"):
            if r["garder"].strip().lower() in ("o", "oui", "1"):
                par[r["fichier"]].append(r)
    total, refus = 0, 0
    for rel, rs in sorted(par.items()):
        chemin = os.path.join(CSEL, rel)
        brut = open(chemin, encoding="utf-8").read()
        if "<!-- corrections OCR bibliotheque-latine -->" in brut:
            print(f"déjà corrigé : {rel}", file=sys.stderr)
            continue
        n = collections.Counter()
        limite = len(brut)                          # début de la correction précédente (on part de la fin)
        for r in sorted(rs, key=lambda r: -int(r["debut"])):
            a, z = int(r["debut"]), int(r["fin"])
            if brut[a:z] != r["original"] or z > limite:
                refus += 1
                continue
            limite = a
            brut = brut[:a] + encoder(r) + brut[z:]
            n[r["type"].split("-")[0]] += 1
        noms = {"cesure": ("césure", "césures"), "coupe": ("mot coupé", "mots coupés"),
                "colle": ("mot collé", "mots collés"), "lettre": ("mot mal lu", "mots mal lus")}
        change = (f'<change when="{DATE}"><!-- corrections OCR bibliotheque-latine -->Corrections OCR automatiques '
                  f'(bibliotheque-latine, scripts/ocr/corriger_csel.py) : '
                  + ", ".join(f"{v} {noms[k][v > 1]}" for k, v in n.items()) + ".</change>")
        if "</revisionDesc>" in brut:
            brut = brut.replace("</revisionDesc>", change + "\n</revisionDesc>", 1)
        else:
            brut = brut.replace("</teiHeader>", f"<revisionDesc>{change}</revisionDesc>\n</teiHeader>", 1)
        open(chemin, "w", encoding="utf-8").write(brut)
        total += sum(n.values())
    print(f"{total} corrections appliquées dans {len(par)} fichiers ; {refus} refusées (texte changé)", file=sys.stderr)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    sp.add_parser("detecter").set_defaults(f=detecter)
    sp.add_parser("appliquer").set_defaults(f=appliquer)
    a = ap.parse_args()
    a.f(a)
