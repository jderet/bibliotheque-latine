# Comptage des mots latins

Ces scripts comptent les mots latins de `textes/`, en ne retenant **qu'une fois** chaque
texte présent dans plusieurs corpus. Les résultats sont dans
[`catalogue/comptage-mots.csv`](../../catalogue/comptage-mots.csv) et commentés dans
[`docs/NOTES.md`](../../docs/NOTES.md).

## Utilisation

```bash
python3 -m venv .venv && .venv/bin/pip install -r scripts/comptage/requirements.txt
.venv/bin/python scripts/comptage/compter.py resultats.json   # ≈ 5 min, 7 processus, ≈ 4 Go de RAM
.venv/bin/python scripts/comptage/bruit.py bruit.json         # indicateur de bruit OCR
```

`textes/` doit être complet (voir `scripts/telecharger.sh`).

## Fichiers

| Fichier | Rôle |
|---|---|
| `extraire.py` | Lecture de chaque corpus, extraction du texte latin, normalisation, empreintes. La liste `CORPUS` fixe les fichiers lus et l'**ordre de priorité**. |
| `compter.py` | Extraction en parallèle, puis dédoublonnage et totaux par corpus. |
| `bruit.py` | Part des mots de chaque corpus dont la forme n'apparaît dans aucun autre corpus. |

## Méthode

### Ce qui est compté
- **Mot** : suite de lettres après normalisation. La normalisation passe en minuscules,
  supprime les diacritiques, remplace æ→ae, œ→oe, j→i, v→u. Les chiffres arabes ne
  comptent pas ; les chiffres romains comptent comme des mots.
- **TEI** : on lit le contenu de `<text>`, ou de chaque `<TEI>` d'un `teiCorpus`, comme pour
  openMGH. On saute `teiHeader`, `note`, `bibl`, `rdg` (on garde `lem`), `back`, `fw`,
  `speaker`, `table`, `wit`, ainsi que `sic`, `orig` et `abbr` lorsqu'ils sont dans un `choice`.
  Les éléments dont `xml:lang` n'est pas latin sont sautés. `<lb break="no"/>` recolle le mot
  coupé ; pour les paires `<w corresp>` de MGH, on garde le lemme une seule fois. La césure
  `-` en fin de ligne est recollée.
- **EpiDoc** (EDH, I.Sicily) : seul `div[@type="edition"]` est lu, sans son `head`. Pour
  I.Sicily, on lit uniquement l'édition `subtype="primary"`, car l'édition lemmatisée en
  doublerait le texte.
- **DLL** : `<front>` est sauté (préface anglaise et listes de variantes).
- **Formulae** : seuls les fichiers `*.lat0*.xml` sont lus ; `elexicon` et les traductions
  `deu001` sont exclus.
- **Perseus, OGL, CSEL, PL, Notre Dame** : seuls les fichiers `*lat*.xml` sont lus ;
  les traductions `*-eng*.xml` sont exclues.
- **Epistolae** : seule la partie « Original letter » est lue, sans la traduction anglaise.
- **Gutenberg** : on retire l'en-tête et le pied de page Project Gutenberg.
- **Noscemus** : on retire le bloc de métadonnées.
- **Wikisource** : on lit les espaces de noms 0 (textes) et 104 (`Pagina:`), sans les
  redirections. On retire les modèles `{{…}}`, les `<ref>`, `<noinclude>`, les tableaux et les
  entités HTML.
- **LatinISE** : on lit la première colonne du fichier vertical, sans la ponctuation (`PUN`).

### Filtre de langue
Pour tout sauf l'épigraphie, le texte est regroupé en fenêtres d'au moins 40 mots. Une
fenêtre est gardée si au moins 4 % de ses mots sont des mots grammaticaux latins, et si cette
part dépasse celle de chaque autre langue testée (anglais, français, allemand, italien,
espagnol, croate, néerlandais). Un reste de moins de 15 mots suit la décision précédente.

Vérifications : les fichiers anglais de Perseus donnent 0 mot. Pour Gutenberg, l'*Énéide*
donne 63 029 mots (le texte réel en fait environ 63 700). Le *De officiis* bilingue donne
38 000 mots latins sur 115 000 ; *Germania* et *Agricola* en donnent 13 900. Un peu de
français passe dans les notes d'une édition commentée de Tacite.

### Dédoublonnage
1. Chaque œuvre est découpée en blocs de 1 000 mots. Un dernier bloc de moins de 200 mots
   est rattaché au précédent.
2. Pour chaque bloc, on calcule les empreintes de ses 5-grammes de mots. On n'en garde qu'un
   sur quatre, par un échantillonnage fondé sur l'empreinte : le même 5-gramme est donc retenu
   dans tous les corpus. Les empreintes sur 34 bits sont stockées dans une table de bits de
   2 Go, avec environ 1 % de faux positifs.
3. Les corpus sont parcourus dans l'ordre de `CORPUS`, les corpus les mieux édités en premier.
   Un bloc est un **doublon** si au moins 50 % de ses empreintes ont déjà été vues (80 % pour un
   bloc de moins de 100 mots, à cause des formules répétitives des chartes et des
   inscriptions). Sinon, ses mots sont comptés et ses empreintes enregistrées.
4. Un bloc trop court pour avoir une empreinte (moins de 5 mots, ou aucun 5-gramme
   échantillonné) est comparé par son texte exact.
5. Une œuvre est dite « majoritairement unique » si plus de la moitié de ses mots est comptée.

Les variantes d'édition, d'orthographe et d'OCR modifient peu les 5-grammes. Deux éditions
d'une même œuvre sont donc reconnues : environ 98 % de mots communs donnent environ 90 % de
5-grammes communs. À l'inverse, deux textes différents qui partagent des formules ne le
sont pas.

### Indicateur de bruit (`bruit.py`)
Il mesure la part des mots d'un corpus dont la forme n'apparaît dans **aucun autre** corpus.
Ce sont des fautes d'OCR, mais aussi des noms propres et des graphies rares. Perseus, saisi à
la main, sert de niveau de base : 0,08 %.

## Limites connues
- L'unité « œuvre » varie selon le corpus : fichier, chapitre (Vulgate), page (Wikisource
  `Pagina:`), document de volume (openMGH), inscription. Seul le nombre de mots est comparable
  d'un corpus à l'autre.
- Les répétitions **internes** à une œuvre (refrains, psaumes répétés) ne sont comptées qu'une fois.
- Plusieurs inscriptions ou chartes au texte identique (« Dis Manibus sacrum ») ne comptent qu'une fois.
- Le total varie de quelques pour cent selon les seuils (50 % et 80 %) et la taille des blocs.
- 5 fichiers EDH sont vides (`HD070403`, `HD071377`, `HD071378`, `HD072745`, `HD072755`) et
  produisent une erreur sans effet.
