# Licences des textes

Ce dépôt est une **compilation** : il ne place pas les textes sous une licence unique.
Chaque corpus du dossier [`textes/`](textes/) garde la licence que lui a donnée son
producteur. Quand vous réutilisez un texte, appliquez la licence de son corpus, et
celle de son en-tête TEI si le fichier en déclare une.

Le tableau lisible par machine se trouve dans [`catalogue/sources.csv`](catalogue/sources.csv).
Chaque dossier contient aussi un fichier `.version-amont` qui donne le commit ou la date de la
version téléchargée, ainsi que le README ou la licence d'origine quand le producteur en fournit un.

Relevé effectué le 22 octobre 2026.

## Résumé par licence

| Licence | Usage commercial | Corpus |
|---|---|---|
| [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/) | oui | neolatdracor |
| Domaine public | oui | vulgata-clementina, gutenberg-latin (domaine public aux États-Unis) |
| [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) | oui, avec attribution | croala, openmgh, noscemus, isicily-latin, formulae-litterae-chartae (en majorité), pta-latin (en partie) |
| [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) | oui, avec attribution et partage à l'identique | perseus-canonical-latinlit, ogl-latin, ogl-csel, ogl-patrologia-latina, camena, dll-caesar-bellum-alexandrinum, dll-problemata, edh-inscriptions, latinise, wikisource-la, pta-latin (en partie) |
| [CC BY-NC-SA 3.0 IT](https://creativecommons.org/licenses/by-nc-sa/3.0/it/) / [4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/) | **non** | digiliblt, notre-dame-latin, epistolae |
| [CC BY-NC-ND 4.0](https://creativecommons.org/licenses/by-nc-nd/4.0/) | **non**, et pas de modification | 105 fichiers de formulae-litterae-chartae |

Pour un site public sans usage commercial, tous ces corpus sont réutilisables à condition de
citer la source et, pour les licences SA, de diffuser les versions modifiées sous la même licence.
Pour un usage commercial, excluez les corpus marqués NC.

## Détail par corpus

| Dossier | Corpus | Licence | Où elle est déclarée |
|---|---|---|---|
| `perseus-canonical-latinlit` | [Perseus canonical-latinLit](https://github.com/PerseusDL/canonical-latinLit) | CC BY-SA 4.0 | `license.md` du dépôt |
| `ogl-latin` | [Open Greek and Latin – Latin](https://github.com/OpenGreekAndLatin/Latin) | CC BY-SA 4.0 | `license.md` du dépôt |
| `ogl-csel` | [CSEL (OGL)](https://github.com/OpenGreekAndLatin/csel-dev) | CC BY-SA 4.0 | en-tête TEI de chaque texte |
| `ogl-patrologia-latina` | [Patrologia Latina (OGL)](https://github.com/OpenGreekAndLatin/patrologia_latina-dev) | CC BY-SA 4.0 | en-têtes TEI |
| `pta-latin` | [Patristisches Textarchiv](https://pta.bbaw.de) | CC BY 4.0 ou CC BY-SA 4.0 | en-tête de chaque fichier |
| `digiliblt` | [digilibLT](https://digiliblt.uniupo.it/) | CC BY-NC-SA 3.0 IT | en-têtes TEI |
| `croala` | [CroALa](https://github.com/nevenjovanovic/croatiae-auctores-latini-textus) | CC BY 4.0 | `LICENSE.md` (quelques en-têtes indiquent CC BY 3.0 ou CC0) |
| `camena` | [CAMENA](https://github.com/nevenjovanovic/camena-neolatinlit) | CC BY-SA 4.0 | `LICENSE.md` |
| `neolatdracor` | [NeoLatDraCor](https://github.com/dracor-org/neolatdracor) | CC0 1.0 | `LICENSE` |
| `formulae-litterae-chartae` | [Formulae – Litterae – Chartae](https://github.com/Formulae-Litterae-Chartae/formulae-open) | CC BY 4.0 (5355 fichiers) ; CC BY-NC-ND 4.0 (105 fichiers) | en-tête de chaque fichier |
| `dll-caesar-bellum-alexandrinum` | [DLL, Bellum Alexandrinum](https://github.com/DigitalLatin/caesar-balex) | CC BY-SA 4.0 | README |
| `dll-problemata` | [DLL, Problemata](https://github.com/DigitalLatin/Problemata) | CC BY-SA 4.0 | en-têtes TEI |
| `notre-dame-latin` | [Notre Dame Digitized Latin Collection](https://github.com/Mythologos/Notre-Dame-Digitized-Latin-Collection) | CC BY-NC-SA 4.0 | `LICENSE` |
| `epistolae` | [Epistolae](https://github.com/ccnmtl/epistolae-hugo) | CC BY-NC-SA 4.0 (contenu) | `LICENSE` (le code du site est sous GPL v3) |
| `edh-inscriptions` | [Epigraphic Database Heidelberg](https://github.com/epigraphic-database-heidelberg/data) | CC BY-SA 4.0 | README |
| `isicily-latin` | [I.Sicily](https://github.com/ISicily/ISicily) | CC BY 4.0 (les 6 fichiers CC BY-NC 4.0 du dépôt d'origine ne font pas partie du sous-ensemble latin) | `licence.txt` et en-têtes |
| `openmgh` | [openMGH](https://www.mgh.de/de/mgh-digital/openmgh) | CC BY 4.0 | page openMGH : citer MGH et Bayerische Staatsbibliothek |
| `latinise` | [LatinISE v6](https://hdl.handle.net/11372/LRT-6140) | CC BY-SA 4.0 | notice LINDAT |
| `wikisource-la` | [Vicifons](https://la.wikisource.org) | CC BY-SA 4.0 | conditions Wikimedia |
| `noscemus` | [Noscemus Digital Sourcebook](https://zenodo.org/records/15040256) | CC BY 4.0 | notice Zenodo |
| `vulgata-clementina` | [Vulgate clémentine, eBible.org](https://ebible.org/Bible/details.php?id=latVUC) | Domaine public | notice eBible.org |
| `gutenberg-latin` | [Project Gutenberg](https://www.gutenberg.org) | Domaine public (États-Unis) | [licence Project Gutenberg](https://www.gutenberg.org/policy/license.html) incluse dans chaque fichier |

## Sources examinées mais non téléchargées

### Licence absente, restrictive ou incertaine

| Source | Motif |
|---|---|
| [The Latin Library](https://www.thelatinlibrary.com) | Aucune licence explicite (textes présentés comme du domaine public, sans source) |
| [Corpus Corporum](https://mlat.uzh.ch) | CC BY-NC-SA annoncée, mais droits variables selon l'origine des textes ; pas d'export en bloc. À intégrer texte par texte |
| [Musisque Deoque](https://www.mqdq.it) | Licence inconnue (une partie des textes est incluse dans LatinISE) |
| [IntraText](https://www.intratext.com) | CC BY-NC-SA 3.0, sans export en bloc (une partie est incluse dans LatinISE) |
| [Corpus Thomisticum](https://www.corpusthomisticum.org) | Tous droits réservés |
| [Capitularia](https://capitularia.uni-koeln.de) | Contenu « libre d'accès et non commercial », sans licence Creative Commons |
| [DLL – Calpurnius Siculus](https://github.com/DigitalLatin/Calpurnius_Siculus) | Aucune licence dans le dépôt |
| [JesDraCor](https://github.com/alexander-winkler/JesDraCor) | Aucune licence (le README invoque seulement le domaine public) |
| [Tesserae](https://github.com/latincy/lat_text_tesserae) | UB Public License 1.0 ; textes repris de The Latin Library et de Perseus (doublons) |
| Library of Latin Texts, BTL, PHI 5, dMGH (Brepols) | Bases commerciales |
| Nova Vulgata | Droits du Saint-Siège |

### À ajouter plus tard (licence libre, mais pas d'export simple trouvé)

| Source | Licence |
|---|---|
| [Roman Inscriptions of Britain](https://romaninscriptionsofbritain.org) | CC BY 4.0 (édition EpiDoc) |
| [Inscriptions of Roman Tripolitania 2009](https://inslib.kcl.ac.uk/irt2009/) / [IRT 2021](https://irt2021.inslib.kcl.ac.uk) | CC BY / CC BY-NC-SA |
| [papyri.info (DDbDP)](https://papyri.info), papyrus latins | CC BY 3.0 |
| [Dickinson College Commentaries](https://dcc.dickinson.edu) | CC BY-SA (textes avec commentaires) |
| [Library of Digital Latin Texts](https://ldlt.digitallatin.org), autres éditions | Creative Commons, variante à vérifier par édition |
| [Latin Text Archive (BBAW)](https://lta.bbaw.de) | CC BY 4.0 pour une partie des textes, à vérifier |

### Ressources linguistiques annotées (non téléchargées : ce sont des annotations plutôt que des textes de lecture)

| Ressource | Licence |
|---|---|
| [LASLA](https://github.com/CIRCSE/LASLA) | CC BY-NC-SA 4.0 |
| [PROIEL Treebank](https://github.com/proiel/proiel-treebank) | CC BY-NC-SA 3.0 |
| [Perseus Latin Dependency Treebank](https://github.com/PerseusDL/treebank_data) | CC BY-SA 3.0 US |
| [Index Thomisticus Treebank](https://github.com/CIRCSE/IT-TB) | CC BY-NC-SA 3.0 |
| [Universal Dependencies (Latin)](https://universaldependencies.org/) | Variable selon le treebank |
| [Lasciva Roma – latin-lemmatized-texts](https://github.com/lascivaroma/latin-lemmatized-texts) | Annotations CC BY-SA 4.0, textes sous la licence d'origine |
| [CompHistSem](https://github.com/CIRCSE/CompHistSem) | CC BY 4.0 / CC BY-SA 4.0 |
