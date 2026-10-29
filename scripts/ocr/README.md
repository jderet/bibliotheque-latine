# Corrections OCR du CSEL

Le CSEL d'Open Greek and Latin (`textes/ogl-csel`) est un OCR corrigé par machine. Ces scripts y
corrigent les erreurs **évidentes** : mots collés, mots coupés par une espace, césures en fin de
ligne et lettres mal lues. Les corrections sont encodées en TEI, et la leçon d'origine est conservée.

| Type | Exemple | Encodage |
|---|---|---|
| Mot collé | `ueritasnon` → `ueritas non` | `<choice><sic>ueritasnon</sic><corr>ueritas non</corr></choice>` |
| Mot coupé | `ta men` → `tamen` | idem |
| Lettre mal lue | `peocato` → `peccato`, `prsedicantem` → `praedicantem` | idem |
| `<sic>` déjà posé par OGL | `<sic>miliaEphraem</sic>` | `<choice><sic>miliaEphraem</sic><corr>milia Ephraem</corr></choice>` |
| Césure | `con- <lb/>stringere` | `con<lb break="no"/>stringere` |

Chaque fichier modifié reçoit une entrée `<change>` dans son `<revisionDesc>`, comme l'impose
la licence CC BY-SA, qui demande de signaler les modifications.

## Utilisation

```bash
.venv/bin/pip install lxml pycollatinus
.venv/bin/python scripts/ocr/corriger_csel.py detecter   # ≈ 30 s → csel-corrections.tsv
python3 scripts/ocr/corriger_csel.py appliquer           # encode les lignes où garder = o
.venv/bin/python scripts/ocr/valider.py [-v]             # contrôle sur les œuvres communes avec Perseus
```

`detecter` a besoin de `textes/perseus-canonical-latinlit` (lexique de référence) et de PyCollatinus.
`appliquer` n'a besoin que de la bibliothèque standard ; `scripts/telecharger.sh` l'appelle après la
copie du CSEL. Pour écarter une correction, mettre `n` dans la colonne `garder` du TSV. Une
correction dont le texte a changé en amont est refusée, et le nombre de refus est affiché.

## Règles

Le script ne lit que le texte principal. Il laisse de côté l'en-tête, les notes (apparat), les
`<hi>` (sigles et variantes en italique), le grec, les titres et les additions. Il laisse aussi les
mots collés à une balise ou voisins d'un crochet, d'une parenthèse, d'un chiffre ou d'un tiret, car
ce sont souvent des fragments ou des restitutions abîmées, comme `p&lt;ostea fu&gt;turi`.

Une correction n'est retenue que si elle est sans ambiguïté :
- **La forme d'origine est inconnue** : elle est absente de Perseus et de Collatinus, figure dans
  moins de deux œuvres du CSEL et n'est pas une autre graphie d'une forme de Perseus (`assumtam`,
  `clamidis`, `discendit` restent intacts).
- **Lettre mal lue** : on remplace une seule confusion visuelle (c/o/e, n/u, l/i, rn/m, s/a de « se »
  pour « ae », t/f, h/b, c/g…). La forme obtenue doit être attestée au moins 20 fois dans Perseus,
  et au moins 10 fois plus que toute autre candidate.
- **Mot collé** : on découpe en deux ou trois mots fréquents de Perseus, dont au moins un mot outil
  (non, et, est, in, quod, deus…). Les cas où l'on obtient des syllabes, des fragments ou un
  infinitif en `-isse` sont refusés. Les noms propres sont découpés seulement à la majuscule (`deChristo`).
- **Mot coupé** : on recolle deux mots séparés par une espace quand l'un des deux est inconnu et que
  le mot recollé est attesté dans Perseus.

## Résultat (29/10/2026)

3 280 corrections dans 175 fichiers sur 271 : 2 275 lettres mal lues, 693 mots collés, 183 mots
coupés et 129 césures. Le texte principal compte environ 5,4 millions de mots.

Sur les 20 œuvres présentes aussi dans Perseus, Perseus confirme 245 corrections et n'en dément
aucune. Les 62 autres ne figurent pas dans l'édition de Perseus ; relues à la main, elles sont
justes dans neuf cas sur dix environ. Les fautes viennent de fragments de mots (`terri` → `ferri`
pour « terri-tori… ») et de mots espacés (`rap o`).

La correction est volontairement prudente : elle ne fait baisser la part de formes inconnues que de
0,05 point en moyenne, et de 0,4 point pour le *Liber apologeticus* d'Orose. Restent en place :
- les mots collés sans mot outil (`patremriserat`) et les noms propres rares ;
- les mots espacés lettre à lettre (`fec i s ti`) ;
- les graphies tardives (`ymnis`, `michi`) ;
- l'apparat critique que l'OCR a mêlé au texte principal dans quelques volumes (Lactance, *De mortibus*).
