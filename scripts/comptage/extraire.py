"""Extraction du texte latin de chaque corpus de textes/ et calcul des empreintes
(5-grammes échantillonnés) servant au dédoublonnage entre corpus."""
import bz2
import glob
import hashlib
import lzma
import os
import re
import unicodedata
import zlib

from lxml import etree

TEXTES = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "textes"))

# ---------------------------------------------------------------- normalisation

_TRANS = str.maketrans({"æ": "ae", "œ": "oe", "ß": "ss", "j": "i", "v": "u", "ſ": "s"})
_MOT = re.compile(r"[a-z]+")


def mots(texte):
    t = unicodedata.normalize("NFKD", texte.lower())
    t = "".join(c for c in t if not unicodedata.combining(c)).translate(_TRANS)
    return _MOT.findall(t)


# ------------------------------------------------------- filtre de langue

LATIN = set("""est ut sed cum quod enim autem atque etiam nec neque esse sunt eius hoc ab ex quam uel tamen ita
nam ipse sic omnia sibi erat ac iam quoque ad quae quid id eum eorum quia sicut igitur ergo inter post ante sine
super uero deus et in non qui de se quoque cuius quibus eam ille illa sit fuit esset haec atque nobis uobis
eos suo sua suis per pro inquit dum nunc tunc ubi unde aut autem ne quoniam""".split())
AUTRES = {
    "en": set("the and of to is that was he for it with as his on be at by this which have from are were they".split()),
    "fr": set("le la les des et est un une du dans pour pas sur au par ce il elle nous vous ont sont avec".split()),
    "de": set("der die das und ist nicht ein eine zu den von mit sich des auf fur im dem wird auch werden".split()),
    "it": set("il di che la e un per una sono del della le gli con alla nel questo".split()),
    "es": set("y el los las del que en por con para una como pero".split()),
    "hr": set("i je u na se da su za od kao ali ili".split()),
    "nl": set("de het een en van is dat op te zijn niet met".split()),
}


def score(toks):
    n = len(toks) or 1
    lat = sum(t in LATIN for t in toks) / n
    autre = max(sum(t in s for t in toks) / n for s in AUTRES.values())
    return lat, autre


def filtre_latin(lignes, fenetre=40):
    """Regroupe les lignes en fenêtres d'au moins `fenetre` mots et ne garde que
    celles dont le vocabulaire grammatical est latin."""
    garde, tampon, n = [], [], 0
    def vider():
        toks = [t for l in tampon for t in l]
        if not toks:
            return
        lat, autre = score(toks)
        if lat >= 0.04 and lat > autre:
            garde.extend(toks)
    for l in lignes:
        toks = mots(l)
        if not toks:
            continue
        tampon.append(toks)
        n += len(toks)
        if n >= fenetre:
            vider()
            tampon, n = [], 0
    if tampon:
        if n < 15 and garde:  # reste trop court pour être jugé : suit la décision précédente
            garde.extend(t for l in tampon for t in l)
        else:
            vider()
    return garde


# ------------------------------------------------------------ extraction XML

SAUTER = {"teiHeader", "note", "bibl", "listBibl", "rdg", "back", "fw", "figDesc", "witDetail", "am",
          "speaker", "castList", "interpGrp", "standOff", "facsimile", "table", "wit"}
DANS_CHOICE = {"sic", "orig"}
BLOCS = {"p", "l", "ab", "head", "item", "cell", "sp", "lg", "div", "div1", "div2", "div3", "div4", "div5",
         "row", "quote", "q", "stage", "label", "opener", "closer", "dateline", "salute", "signed", "lb", "trailer"}
PARSER = etree.XMLParser(recover=True, huge_tree=True, load_dtd=False, no_network=True, resolve_entities=False)
XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"


def nom(el):
    return etree.QName(el).localname if isinstance(el.tag, str) else ""


def est_latin(lang):
    return lang is None or lang.lower().startswith("la")


def texte_xml(racine, lang_defaut=None, sauter_en_plus=frozenset()):
    """Renvoie une liste de lignes de texte, en sautant apparat, notes et passages
    explicitement non latins."""
    morceaux = []
    deja = set()  # mots coupés en deux <w corresp> (MGH)

    def visite(el, lang):
        n = nom(el)
        if not n:  # commentaire, instruction
            if el.tail:
                morceaux.append(el.tail)
            return
        lang = el.get(XML_LANG, lang)
        parent = el.getparent()
        sauter = n in SAUTER or n in sauter_en_plus or (n in DANS_CHOICE and parent is not None and nom(parent) == "choice") \
            or (n == "abbr" and parent is not None and nom(parent) == "choice") or not est_latin(lang)
        if n == "lb":
            morceaux.append("\x00" if el.get("break") == "no" else "\n")
        elif n in BLOCS:
            morceaux.append("\n")
        if not sauter:
            if n == "w" and el.get("corresp"):
                ids = el.get("corresp").split()
                cle = el.get("corresp")
                if cle not in deja:
                    deja.add(cle)
                    morceaux.append(" " + (el.get("lemma") or "") + " ")
            else:
                if el.text:
                    morceaux.append(el.text)
                for e in el:
                    visite(e, lang)
        if n in BLOCS:
            morceaux.append("\n")
        if el.tail:
            morceaux.append(el.tail)

    visite(racine, lang_defaut)
    t = "".join(morceaux)
    t = re.sub(r"\s*\x00\s*", "", t)               # <lb break="no"/>
    t = re.sub(r"(\w)-\s*\n\s*(\w)", r"\1\2", t)   # césure en fin de ligne
    return t.split("\n")


def lire_xml(chemin):
    return etree.parse(chemin, PARSER).getroot()


def corps_tei(racine):
    """Éléments <text> d'un TEI (ou de chaque TEI d'un teiCorpus)."""
    return [e for e in racine.iter() if nom(e) == "text" and not any(nom(a) == "text" for a in e.iterancestors())]


# ------------------------------------------------------------ par corpus

def oeuvres_tei(chemin, epidoc=False, sans_front=False):
    """Génère (identifiant, liste_de_mots) pour un fichier TEI."""
    racine = lire_xml(chemin)
    if racine is None:
        return
    if epidoc:
        editions = [e for e in racine.iter() if nom(e) == "div" and e.get("type") == "edition"]
        primaires = [e for e in editions if e.get("subtype") == "primary"]
        latines = [e for e in (primaires or editions) if (e.get(XML_LANG) or "la").startswith("la")]
        toks = []
        for e in latines:
            for h in [h for h in e if nom(h) == "head"]:
                e.remove(h)
            for l in texte_xml(e):
                toks += mots(l)
        yield os.path.basename(chemin), toks
        return
    textes = corps_tei(racine)
    if not textes:  # TEI.2 sans <text> repérable : tout le document hors en-tête
        textes = [racine]
    for i, t in enumerate(textes):
        lang = None
        for a in [t] + list(t.iterancestors()):
            if a.get(XML_LANG):
                lang = a.get(XML_LANG)
                break
        if lang and not est_latin(lang):
            lang = None  # en-tête en anglais, texte sans indication : on laisse décider le filtre
        yield f"{os.path.basename(chemin)}#{i}", filtre_latin(texte_xml(t, lang, {"front"} if sans_front else frozenset()))


def oeuvres_texte(chemin, lignes):
    yield os.path.basename(chemin), filtre_latin(lignes)


def gutenberg(chemin):
    t = open(chemin, encoding="utf-8", errors="replace").read()
    d = re.search(r"\*\*\* ?START OF[^\n]*\n", t)
    f = re.search(r"\*\*\* ?END OF", t)
    t = t[d.end() if d else 0: f.start() if f else len(t)]
    return oeuvres_texte(chemin, t.split("\n"))


def noscemus(chemin):
    t = lzma.open(chemin, "rt", encoding="utf-8", errors="replace").read()
    i = t.find("End of metadata section")
    if i >= 0:
        t = t[t.find("\n", t.find("\n", i) + 1):]
    return oeuvres_texte(chemin, t.split("\n"))


def epistolae(chemin):
    t = open(chemin, encoding="utf-8").read()
    i = t.find("Original letter:")
    if i < 0:
        return iter([])
    t = t[i + len("Original letter:"):]
    j = t.find("<h2")
    t = re.sub(r"<[^>]+>", "\n", t[: j if j >= 0 else len(t)])
    return oeuvres_texte(chemin, t.split("\n"))


def vulgate(chemin):
    return oeuvres_texte(chemin, open(chemin, encoding="utf-8").read().split("\n"))


_GABARIT = re.compile(r"\{\{[^{}]*\}\}")


def nettoyer_wiki(t):
    t = re.sub(r"<!--.*?-->", "", t, flags=re.S)
    t = re.sub(r"<(ref|noinclude|math|score|gallery)[^>]*>.*?</\1>", "", t, flags=re.S | re.I)
    t = re.sub(r"<ref[^>]*/>", "", t)
    for _ in range(6):
        t2 = _GABARIT.sub("", t)
        if t2 == t:
            break
        t = t2
    t = re.sub(r"\[\[(?:Categoria|Category|Fasciculus|File|Imago|Image|[a-z]{2,3}):[^\]]*\]\]", "", t, flags=re.I)
    t = re.sub(r"\[\[[^\]|]*\|([^\]]*)\]\]", r"\1", t)
    t = re.sub(r"\[\[([^\]]*)\]\]", r"\1", t)
    t = re.sub(r"\[https?://\S+ ?([^\]]*)\]", r"\1", t)
    t = re.sub(r"<[^>]+>", " ", t)
    t = re.sub(r"&[a-zA-Z]+;|&#\d+;", " ", t)
    t = re.sub(r"'{2,}|={2,}|__[A-Z]+__", "", t)
    return [l for l in t.split("\n") if not l.lstrip().startswith(("{|", "|", "!", "#REDIRECT", "#redirect"))]


def wikisource():
    parts = sorted(glob.glob(f"{TEXTES}/wikisource-la/*.part-*"))

    class Flux:
        def __init__(self):
            self.fichiers = iter(parts)
            self.courant = open(next(self.fichiers), "rb")
        def read(self, n=-1):
            while True:
                b = self.courant.read(n)
                if b:
                    return b
                try:
                    self.courant = open(next(self.fichiers), "rb")
                except StopIteration:
                    return b""

    flux = bz2.BZ2File(Flux())
    for _, page in etree.iterparse(flux, tag="{*}page", huge_tree=True):
        ns = page.findtext("{*}ns")
        titre = page.findtext("{*}title")
        texte = page.findtext("{*}revision/{*}text") or ""
        redir = page.find("{*}redirect") is not None
        page.clear()
        while page.getprevious() is not None:
            del page.getparent()[0]
        if ns in ("0", "104") and not redir:
            yield titre, filtre_latin(nettoyer_wiki(texte))


def latinise():
    toks, doc = [], None
    with lzma.open(f"{TEXTES}/latinise/latinise-v6.vert.xz", "rt", encoding="utf-8", errors="replace") as f:
        for ligne in f:
            if ligne.startswith("<"):
                if ligne.startswith("<doc "):
                    m = re.search(r'title="([^"]*)"', ligne)
                    doc = m.group(1) if m else "?"
                elif ligne.startswith("</doc"):
                    yield doc, toks
                    toks = []
                continue
            col = ligne.split("\t")
            if len(col) >= 2 and col[1] != "PUN":
                toks += mots(col[0])
    if toks:
        yield doc, toks


def fichiers(motif, exclure=()):
    return sorted(f for f in glob.glob(f"{TEXTES}/{motif}", recursive=True)
                  if "__cts__" not in f and "__capitains__" not in f and not any(x in f for x in exclure))


# Ordre de priorité : la première occurrence d'un texte est attribuée au corpus le mieux édité.
CORPUS = [
    ("perseus-canonical-latinlit", lambda: fichiers("perseus-canonical-latinlit/data/**/*-lat*.xml"), oeuvres_tei),
    ("ogl-latin", lambda: fichiers("ogl-latin/data/**/*lat*.xml"), oeuvres_tei),
    ("dll-caesar-bellum-alexandrinum", lambda: fichiers("dll-caesar-bellum-alexandrinum/*.xml"), lambda c: oeuvres_tei(c, sans_front=True)),
    ("dll-problemata", lambda: fichiers("dll-problemata/edition.xml"), lambda c: oeuvres_tei(c, sans_front=True)),
    ("pta-latin", lambda: fichiers("pta-latin/data/**/*.xml"), oeuvres_tei),
    ("digiliblt", lambda: fichiers("digiliblt/*/*.xml"), oeuvres_tei),
    ("ogl-csel", lambda: fichiers("ogl-csel/data/**/*lat*.xml"), oeuvres_tei),
    ("ogl-patrologia-latina", lambda: fichiers("ogl-patrologia-latina/data/**/*lat*.xml"), oeuvres_tei),
    ("notre-dame-latin", lambda: fichiers("notre-dame-latin/data/**/*lat*.xml"), oeuvres_tei),
    ("vulgata-clementina", lambda: fichiers("vulgata-clementina/chapitres/latVUC_*_read.txt", ("latVUC_000_",)), vulgate),
    ("openmgh", lambda: fichiers("openmgh/xml/*.xml"), oeuvres_tei),
    ("formulae-litterae-chartae", lambda: fichiers("formulae-litterae-chartae/data/**/*.lat0*.xml", ("/elexicon/",)), oeuvres_tei),
    ("epistolae", lambda: fichiers("epistolae/letter/*.md"), epistolae),
    ("croala", lambda: fichiers("croala/txts/*.xml"), oeuvres_tei),
    ("camena", lambda: fichiers("camena/*/*.xml"), oeuvres_tei),
    ("neolatdracor", lambda: fichiers("neolatdracor/tei/*.xml"), oeuvres_tei),
    ("noscemus", lambda: fichiers("noscemus/textes/**/*.txt.xz"), noscemus),
    ("edh-inscriptions", lambda: fichiers("edh-inscriptions/inscriptions/**/*.xml"), lambda c: oeuvres_tei(c, epidoc=True)),
    ("isicily-latin", lambda: fichiers("isicily-latin/inscriptions/*.xml"), lambda c: oeuvres_tei(c, epidoc=True)),
    ("wikisource-la", None, wikisource),
    ("latinise", None, latinise),
    ("gutenberg-latin", lambda: fichiers("gutenberg-latin/txt/*.txt"), gutenberg),
]


# ------------------------------------------------------------ empreintes

TAILLE_BLOC = 1000


def empreintes(toks):
    """Découpe une œuvre en blocs de ~1000 mots ; pour chaque bloc renvoie
    (nombre de mots, empreintes échantillonnées 5-grammes, clé exacte)."""
    blocs = [toks[i:i + TAILLE_BLOC] for i in range(0, len(toks), TAILLE_BLOC)]
    if len(blocs) > 1 and len(blocs[-1]) < 200:
        dernier = blocs.pop()
        blocs[-1] = blocs[-1] + dernier
    sortie = []
    for b in blocs:
        ech = []
        for i in range(len(b) - 4):
            s = " ".join(b[i:i + 5]).encode()
            h2 = zlib.crc32(s, 0x9E3779B9)
            if h2 & 3 == 0:
                ech.append(zlib.crc32(s) | ((h2 >> 2) & 3) << 32)
        cle = hashlib.blake2b(" ".join(b).encode(), digest_size=8).digest()
        sortie.append((len(b), ech, cle))
    return sortie
