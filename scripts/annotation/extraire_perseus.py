#!/usr/bin/env python3
"""Extrait le texte latin des éditions TEI (CTS/EpiDoc) de Perseus canonical-latinLit.

Pour chaque fichier *-lat*.xml, écrit un JSON contenant la suite des segments citables
(vers, sections…), chacun avec sa citation CTS (« 1.2.3 ») et le séparateur qui le précède :
  "\\n\\n" : frontière forte (livre, poème, chapitre, réplique) = frontière de phrase imposée ;
  "\\n"    : changement de vers ;
  " "      : frontière faible (section, paragraphe, jalon) qui peut couper une phrase.

Usage : extraire_perseus.py <dossier data de canonical-latinLit> <dossier sortie> [--une-edition]
"""
import argparse
import glob
import html.entities
import json
import os
import re
import sys
import xml.etree.ElementTree as ET

TEI = "{http://www.tei-c.org/ns/1.0}"
XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"
CTS = "{http://chs.harvard.edu/xmlns/cts}"

# Éléments dont le contenu n'appartient pas au texte latin lu.
IGNORES = {"note", "head", "speaker", "stage", "bibl", "label", "figure", "rdg", "trailer",
           "fw", "ref", "desc", "listPerson", "castList", "argument", "docAuthor", "byline"}
# Dans <choice>, on garde la forme corrigée / régularisée / développée.
REJETS_CHOICE = {"sic", "orig", "abbr"}
# Sous-types de textpart qui ne marquent pas nécessairement une fin de phrase.
DIVS_FAIBLES = {"section", "subsection", "line", "paragraph", "para", "secton", "verse"}
# Jalons (milestone) qui participent à la citation canonique.
JALONS_CITATION = {"section", "paragraph", "para", "chapter", "line", "book", "fragment",
                   "tale", "vulgate-letter", "act", "sectin"}
JALONS_FAIBLES = {"section", "paragraph", "para", "line", "sectin"}

_ENTITES_XML = {"amp", "lt", "gt", "quot", "apos"}


def remplacer_entites(texte):
    """Remplace les entités nommées HTML (&dagger; …) inconnues du parseur XML."""
    def rempl(m):
        nom = m.group(1)
        if nom in _ENTITES_XML:
            return m.group(0)
        car = html.entities.html5.get(nom + ";")
        return car if car is not None else ""
    return re.sub(r"&([A-Za-z][A-Za-z0-9]*);", rempl, texte)


def local(tag):
    return tag.rsplit("}", 1)[-1] if isinstance(tag, str) else ""


def sous_type_div(el):
    """Sous-type d'une division citable (TEI P5 <div type="textpart"> ou P4 <div1>…), sinon None."""
    nom = local(el.tag)
    if nom == "div" and el.get("type") == "textpart":
        return (el.get("subtype") or "").lower()
    if re.fullmatch(r"div[1-7]", nom):
        return (el.get("type") or "").lower()
    return None


class Extracteur:
    def __init__(self):
        self.segments = []          # [{"cit", "sep", "texte"}]
        self.divs = []              # pile des n de textpart
        self.jalons = []            # [(unité, n)] dans la div courante
        self.vers = None            # n du vers courant
        self.sep_pendant = "\n\n"   # séparateur à poser avant le prochain texte
        self.chars_vers = 0
        self.chars_total = 0
        self.vers_lb = False

    # -- citation -----------------------------------------------------------
    def citation(self):
        parts = [n for n in self.divs if n]
        parts += [n for _, n in self.jalons]
        if self.vers:
            parts.append(self.vers)
        return ".".join(parts)

    def frontiere(self, sep):
        # La frontière la plus forte l'emporte.
        ordre = {" ": 0, "\n": 1, "\n\n": 2}
        if ordre[sep] > ordre[self.sep_pendant]:
            self.sep_pendant = sep

    def texte(self, t, en_vers):
        if not t:
            return
        t = re.sub(r"\s+", " ", t)
        if not t.strip():
            if self.segments and not self.segments[-1]["texte"].endswith(" "):
                self.segments[-1]["texte"] += " "
            return
        cit = self.citation()
        der = self.segments[-1] if self.segments else None
        if der is not None and der["cit"] == cit and self.sep_pendant == " " and not self._nouveau:
            der["texte"] += t
        else:
            self.segments.append({"cit": cit, "sep": self.sep_pendant, "texte": t.lstrip()})
            self.sep_pendant = " "
            self._nouveau = False
        self.chars_total += len(t)
        if en_vers:
            self.chars_vers += len(t)

    _nouveau = False

    # -- parcours -------------------------------------------------------------
    def parcourir(self, el, en_vers=False, dans_choice=False):
        nom = local(el.tag)
        if nom in IGNORES or (dans_choice and nom in REJETS_CHOICE):
            self.texte(el.tail, en_vers)
            return
        if nom == "gap":
            self.texte(" ", en_vers)
            self.texte(el.tail, en_vers)
            return
        if nom == "app":  # apparat inline : on ne garde que le lemme
            for f in el:
                if local(f.tag) == "lem":
                    self.parcourir(f, en_vers)
            self.texte(el.tail, en_vers)
            return
        if nom == "milestone":
            unite, n = el.get("unit"), el.get("n")
            if unite in JALONS_CITATION and n:
                unites = [u for u, _ in self.jalons]
                if unite in unites:
                    del self.jalons[unites.index(unite):]
                self.jalons.append((unite, n))
                self.frontiere(" " if unite in JALONS_FAIBLES else "\n\n")
                self._nouveau = True
            self.texte(el.tail, en_vers)
            return
        if nom == "lb":
            if el.get("n") or self.vers_lb:
                # Vers balisés par <lb n="…"/> (Appendix Vergiliana, TEI P4)
                self.vers_lb = True
                n = el.get("n")
                self.vers = n if n else (str(int(self.vers) + 1) if self.vers and self.vers.isdigit() else self.vers)
                self.frontiere("\n")
                self._nouveau = True
            elif el.get("break") != "no":
                self.texte(" ", en_vers)
            self.texte(el.tail, en_vers or self.vers_lb)
            return
        if nom == "pb":
            self.texte(el.tail, en_vers)
            return

        sauvegarde = None
        sous_type = sous_type_div(el)
        if sous_type is not None:
            sauvegarde = (list(self.divs), list(self.jalons), self.vers)
            self.divs.append(el.get("n") or "")
            self.jalons, self.vers = [], None
            faible = sous_type in DIVS_FAIBLES
            self.frontiere(" " if faible else "\n\n")
            self._nouveau = True
        elif nom == "l":
            n = el.get("n")
            if n:
                self.vers = n
            elif self.vers and self.vers.isdigit():
                self.vers = str(int(self.vers) + 1)
            self.frontiere("\n")
            self._nouveau = True
            en_vers = True
        elif nom == "sp":
            self.frontiere("\n\n")
            self._nouveau = True
        elif nom in ("p", "lg", "ab", "q", "quote", "said", "cit", "seg"):
            pass

        en_vers = en_vers or self.vers_lb
        self.texte(el.text, en_vers)
        for enfant in el:
            self.parcourir(enfant, en_vers, dans_choice=(nom == "choice"))

        if sauvegarde is not None:
            self.divs, self.jalons, self.vers = sauvegarde
            self.frontiere(" " if sous_type in DIVS_FAIBLES else "\n\n")
            self._nouveau = True
        elif nom == "l":
            self.frontiere("\n")
            self._nouveau = True
        elif nom == "sp":
            self.frontiere("\n\n")
            self._nouveau = True
        self.texte(el.tail, en_vers)


def metadonnees(fichier):
    """Auteur et titre depuis les __cts__.xml du textgroup et de l'œuvre."""
    dossier_oeuvre = os.path.dirname(fichier)
    auteur = titre = None
    try:
        r = ET.parse(os.path.join(os.path.dirname(dossier_oeuvre), "__cts__.xml")).getroot()
        g = r.find(CTS + "groupname")
        auteur = g.text.strip() if g is not None and g.text else None
    except (OSError, ET.ParseError):
        pass
    try:
        r = ET.parse(os.path.join(dossier_oeuvre, "__cts__.xml")).getroot()
        titres = {t.get(XML_LANG): (t.text or "").strip() for t in r.findall(CTS + "title")}
        titre = titres.get("lat") or titres.get("eng") or next(iter(titres.values()), None)
    except (OSError, ET.ParseError):
        pass
    return auteur, titre


def extraire(fichier):
    with open(fichier, encoding="utf-8") as f:
        brut = remplacer_entites(f.read())
    racine = ET.fromstring(brut.encode("utf-8"))
    # TEI P5 (espace de noms TEI) ou P4 (<TEI.2>, sans espace de noms)
    corps = next((e for e in racine.iter() if local(e.tag) == "body"), None)
    if corps is None:
        raise ValueError("pas de <body>")
    editions = [d for d in corps.iter() if local(d.tag) == "div" and d.get("type") == "edition"]
    ex = Extracteur()
    for ed in editions or [corps]:
        ex.frontiere("\n\n")
        ex._nouveau = True
        ex.texte(ed.text, False)
        for enfant in ed:
            ex.parcourir(enfant)
    segments = []
    for s in ex.segments:
        s["texte"] = re.sub(r"\s+", " ", s["texte"]).strip()
        if s["texte"]:
            segments.append(s)
    stem = os.path.basename(fichier)[:-4]
    auteur, titre = metadonnees(fichier)
    return {
        "urn": f"urn:cts:latinLit:{stem}",
        "fichier": os.path.relpath(fichier),
        "auteur": auteur,
        "titre": titre,
        "genre": "vers" if ex.chars_total and ex.chars_vers / ex.chars_total > 0.5 else "prose",
        "n_mots": sum(len(s["texte"].split()) for s in segments),
        "segments": segments,
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("data", help="dossier data/ de PerseusDL/canonical-latinLit")
    ap.add_argument("sortie", help="dossier où écrire un JSON par édition")
    ap.add_argument("--une-edition", action="store_true",
                    help="ne garder qu'une édition latine par œuvre (le numéro le plus élevé)")
    args = ap.parse_args()

    fichiers = sorted(glob.glob(os.path.join(args.data, "*", "*", "*-lat*.xml")))
    if args.une_edition:
        par_oeuvre = {}
        for f in fichiers:
            par_oeuvre.setdefault(os.path.dirname(f), []).append(f)
        cle = lambda f: int(re.search(r"lat(\d+)\.xml$", f).group(1) or 0)
        fichiers = [max(fs, key=cle) for fs in par_oeuvre.values()]

    os.makedirs(args.sortie, exist_ok=True)
    total, erreurs, index = 0, [], []
    for f in fichiers:
        try:
            doc = extraire(f)
        except Exception as e:  # un fichier défectueux ne bloque pas le corpus
            erreurs.append((f, str(e)))
            continue
        nom = doc["urn"].rsplit(":", 1)[-1]
        with open(os.path.join(args.sortie, nom + ".json"), "w", encoding="utf-8") as out:
            json.dump(doc, out, ensure_ascii=False)
        total += doc["n_mots"]
        index.append({k: doc[k] for k in ("urn", "auteur", "titre", "genre", "n_mots")}
                     | {"n_segments": len(doc["segments"])})
    with open(os.path.join(args.sortie, "_index.json"), "w", encoding="utf-8") as out:
        json.dump(index, out, ensure_ascii=False, indent=1)
    print(f"{len(index)} éditions, {total} mots ; {len(erreurs)} erreurs", file=sys.stderr)
    for f, e in erreurs:
        print(f"  ERREUR {f}: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
