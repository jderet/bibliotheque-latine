# Bibliothèque latine

Une collection de textes latins **sous licence libre**, de l'Antiquité au néo-latin, réunis
pour servir de base à une bibliothèque latine en ligne, sur le modèle de
[The Greek Library](https://thegreeklibrary.pages.lisn.upsaclay.fr/).

Le dépôt rassemble 22 corpus produits par des projets universitaires et communautaires
(Perseus, Open Greek and Latin, MGH, CAMENA, CroALa, digilibLT, EDH, Wikisource…).
Chaque corpus garde sa licence d'origine : **lisez [LICENCES.md](LICENCES.md) avant toute
réutilisation.**

## Contenu

| Dossier | Corpus | Période | Licence |
|---|---|---|---|
| [`perseus-canonical-latinlit`](textes/perseus-canonical-latinlit) | Perseus Digital Library | Antiquité | CC BY-SA 4.0 |
| [`ogl-latin`](textes/ogl-latin) | Open Greek and Latin | Antiquité | CC BY-SA 4.0 |
| [`ogl-csel`](textes/ogl-csel) | Corpus Scriptorum Ecclesiasticorum Latinorum | Antiquité tardive | CC BY-SA 4.0 |
| [`ogl-patrologia-latina`](textes/ogl-patrologia-latina) | Patrologia Latina (sélection) | Antiquité tardive – Moyen Âge | CC BY-SA 4.0 |
| [`pta-latin`](textes/pta-latin) | Patristisches Textarchiv | Antiquité tardive | CC BY / CC BY-SA 4.0 |
| [`digiliblt`](textes/digiliblt) | digilibLT | Antiquité tardive | CC BY-NC-SA 3.0 IT |
| [`vulgata-clementina`](textes/vulgata-clementina) | Vulgate clémentine | Bible | Domaine public |
| [`openmgh`](textes/openmgh) | Monumenta Germaniae Historica | Moyen Âge | CC BY 4.0 |
| [`formulae-litterae-chartae`](textes/formulae-litterae-chartae) | Chartes et formules du haut Moyen Âge | Moyen Âge | CC BY 4.0 (105 fichiers en CC BY-NC-ND) |
| [`epistolae`](textes/epistolae) | Lettres latines de femmes médiévales | Moyen Âge | CC BY-NC-SA 4.0 |
| [`dll-problemata`](textes/dll-problemata) | Digital Latin Library | Moyen Âge | CC BY-SA 4.0 |
| [`dll-caesar-bellum-alexandrinum`](textes/dll-caesar-bellum-alexandrinum) | Digital Latin Library | Antiquité | CC BY-SA 4.0 |
| [`notre-dame-latin`](textes/notre-dame-latin) | Notre Dame Digitized Latin Collection | Antiquité – Moyen Âge | CC BY-NC-SA 4.0 |
| [`croala`](textes/croala) | Auteurs latins croates | Moyen Âge – époque moderne | CC BY 4.0 |
| [`camena`](textes/camena) | CAMENA, néo-latin | XVe–XVIIIe s. | CC BY-SA 4.0 |
| [`neolatdracor`](textes/neolatdracor) | Théâtre néo-latin | XVIe–XVIIIe s. | CC0 1.0 |
| [`noscemus`](textes/noscemus) | Littérature scientifique néo-latine | XVe–XVIIIe s. | CC BY 4.0 |
| [`edh-inscriptions`](textes/edh-inscriptions) | Epigraphic Database Heidelberg | Épigraphie | CC BY-SA 4.0 |
| [`isicily-latin`](textes/isicily-latin) | I.Sicily, inscriptions latines | Épigraphie | CC BY 4.0 |
| [`latinise`](textes/latinise) | LatinISE, corpus lemmatisé | Toutes périodes | CC BY-SA 4.0 |
| [`wikisource-la`](textes/wikisource-la) | Vicifons (Wikisource latine) | Toutes périodes | CC BY-SA 4.0 |
| [`gutenberg-latin`](textes/gutenberg-latin) | Project Gutenberg | Toutes périodes | Domaine public (États-Unis) |

Le détail (producteur, nombre de textes, format, remarques) se trouve dans
[`catalogue/sources.csv`](catalogue/sources.csv).

## Taille

Environ **240 millions de mots latins uniques** (308 millions en comptant les textes présents
dans plusieurs corpus). Le détail par corpus est dans
[`catalogue/comptage-mots.csv`](catalogue/comptage-mots.csv). La méthode est décrite dans
[`scripts/comptage/`](scripts/comptage/README.md) ; les constats (recoupements, bruit OCR,
licences, pièges) dans [`docs/NOTES.md`](docs/NOTES.md).

## Formats

- La plupart des corpus sont en **TEI XML**. Perseus, OGL, PTA et Formulae suivent les
  conventions CTS/CapiTainS (`data/<auteur>/<œuvre>/<auteur>.<œuvre>.<édition>.xml`).
- Les inscriptions (EDH, I.Sicily) sont en **EpiDoc**.
- Les fichiers volumineux sont compressés pour rester sous la limite de 100 Mo de GitHub :
  - `latinise/latinise-v6.vert.xz` : `xz -d -k latinise-v6.vert.xz`
  - `wikisource-la/` : `cat lawikisource-pages-articles.xml.bz2.part-* > lawikisource.xml.bz2`
  - `noscemus/textes/**.txt.xz` : `xz -d -k fichier.txt.xz`

## Mettre à jour

Le script [`scripts/telecharger.sh`](scripts/telecharger.sh) retélécharge toutes les sources
dans un cache (`.cache/`, ignoré par git) puis reconstruit `textes/` :

```bash
scripts/telecharger.sh
```

## Citer

Citez toujours le projet d'origine du texte (voir [LICENCES.md](LICENCES.md)), pas seulement
ce dépôt. Les licences CC BY imposent l'attribution ; les licences SA imposent de redistribuer
les versions modifiées sous la même licence ; les licences NC interdisent l'usage commercial.

## Prochaines étapes

- Un catalogue unifié par auteur et œuvre (URN CTS, période, genre), tiré des en-têtes TEI.
- Un site de lecture statique (texte, recherche, et traductions quand elles sont libres).
- L'ajout des sources listées comme « à ajouter » dans [LICENCES.md](LICENCES.md).
