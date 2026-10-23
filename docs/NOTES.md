# Notes de travail

Ce journal garde ce qui a été appris en constituant le dépôt (22–23 octobre 2026) :
démarche de recherche, décisions, constats chiffrés, pièges rencontrés et pistes.
Les licences sont détaillées dans [LICENCES.md](../LICENCES.md), le catalogue des sources
dans [catalogue/sources.csv](../catalogue/sources.csv) et les chiffres dans
[catalogue/comptage-mots.csv](../catalogue/comptage-mots.csv).

## 1. Taille de la bibliothèque

| | Mots |
|---|---|
| Mots latins, tous corpus confondus | **307,7 millions** |
| Mots latins uniques (chaque texte compté une fois) | **239,7 millions** |

Répartition des mots uniques :

| Ensemble | Corpus | Mots uniques |
|---|---|---|
| Néo-latin | Noscemus 93,2 M · CAMENA 45,5 M · CroALa 5,2 M · NeoLatDraCor 0,24 M | **144,1 M** |
| Corpus transversaux | Wikisource 46,4 M · Gutenberg 3,8 M · LatinISE 1,3 M | **51,5 M** |
| Antiquité et Pères | Patrologia Latina (OGL) 19,5 M · Perseus 5,8 M · CSEL 5,4 M · digilibLT 2,7 M · Notre Dame 0,4 M · OGL Latin 0,13 M · PTA, DLL, Vulgate < 0,05 M chacun | **34,1 M** |
| Moyen Âge | openMGH 7,2 M · Formulae 1,2 M · Epistolae 0,6 M | **9,0 M** |
| Épigraphie | EDH 0,99 M · I.Sicily 0,01 M | **1,0 M** |

Sans le néo-latin, il reste environ 95 millions de mots. La méthode est décrite dans
[scripts/comptage/README.md](../scripts/comptage/README.md).

### Recoupements observés
- **Vulgate clémentine** : 97 % de doublons. La Patrologia Latina d'OGL contient déjà la
  Vulgate, avec Jérôme et la *Glossa ordinaria*.
- **LatinISE** : 88 % de doublons. Il reprend LacusCurtius, IntraText et Musisque Deoque,
  déjà couverts surtout par Perseus.
- **Wikisource** : 50 % de doublons. C'est pourtant le 2ᵉ apport le plus important, avec
  46 M de mots uniques : elle contient beaucoup plus de Migne que la sélection OGL. Ses plus
  grosses œuvres sont les Homélies d'Haymon d'Halberstadt, les *Enarrationes in Psalmos*, la
  *Summa Theologiae*, la Vulgate, Tite-Live, les *Moralia* de Grégoire, le registre d'Innocent
  III, le *Codex Iustinianus*, Pline, la *Gallia Christiana* (OCR des pages `Pagina:`) et les
  tomes 1–2 de la PL. 45 472 de ses 61 789 pages lues sont des pages `Pagina:`.
- **DLL, Bellum Alexandrinum** : 100 % de doublons. Le texte est dans Perseus (mais
  l'édition DLL a un apparat critique propre).
- **Gutenberg** : 32 % de doublons.
- **Perseus** : 17 % de doublons, car il contient plusieurs éditions latines de mêmes œuvres.
- **Notre Dame** : 27 % de doublons. **Epistolae** : 25 % (lettres déjà dans MGH ou Migne).
- **openMGH ↔ Formulae** : des chartes communes, d'où 8 % de doublons pour Formulae.
- **EDH ↔ I.Sicily** : environ 10 % de doublons. Les inscriptions de Sicile sont dans les deux.

### Qualité (indicateur de bruit OCR)
Part des mots dont la forme n'existe dans aucun autre corpus. Le niveau de base est Perseus,
saisi à la main : 0,08 %.

| Corpus | % | Remarque |
|---|---|---|
| Vulgate, LatinISE, Perseus, DLL BAlex | ≤ 0,2 | textes propres |
| CSEL, PTA, OGL Latin, Notre Dame, digilibLT, Wikisource | 0,2 – 0,6 | |
| NeoLatDraCor, Gutenberg, CroALa, PL, openMGH, Epistolae, DLL Problemata, CAMENA | 0,9 – 1,8 | OCR corrigé, graphies médiévales et modernes |
| I.Sicily, Noscemus | ≈ 2,8 | OCR brut (Noscemus) |
| EDH, Formulae | 4,4 – 5,2 | abréviations et graphies épigraphiques ou mérovingiennes, plus que de l'OCR |

Le bruit reste de l'ordre de quelques pour cent du total. Ces corpus sont toutefois de l'OCR,
même corrigé : Noscemus (39 % des mots), une partie de Wikisource, PL et CSEL. Ils devront
être signalés comme tels dans l'interface de lecture.

## 2. Démarche de recherche des sources

Une recherche large a été menée : Digital Classicist Wiki, liste
[jramminger.github.io/corpora](https://jramminger.github.io/corpora/), recherches GitHub
(« latin texts », « neo-latin », « medieval latin », « treebank », organisations
OpenGreekAndLatin, DigitalLatin, CIRCSE, scta, dracor-org, Capitains…), Zenodo, LINDAT,
dumps Wikimedia, et la liste de sources de [latincy-readers](https://github.com/latincy/latincy-readers),
utile comme point de contrôle.

**Règle suivie** : un corpus n'est retenu que si une licence libre explicite est vérifiable,
dans le dépôt, l'en-tête TEI ou la notice d'archive. Une simple affirmation de « domaine
public » sans licence ne suffit pas. Exception : la Vulgate (eBible.org) et Gutenberg, qui
déclarent explicitement le domaine public. Les sources écartées et leurs motifs sont dans
[LICENCES.md](../LICENCES.md).

Constats de licence notables :
- **CSEL et Patrologia Latina (OGL)** : leurs dépôts n'ont pas de fichier LICENSE. La licence
  CC BY-SA 4.0 est déclarée dans chaque en-tête TEI.
- **digilibLT** : le dépôt du CIRCSE affiche un badge CC BY-NC-SA 3.0 et un texte CC BY-SA 4.0,
  ce qui est contradictoire. Les fichiers TEI repris ici (copie de la DLL) disent CC BY-NC-SA 3.0 IT.
- **Epistolae** : le README dit CC BY-SA 3.0 US, le fichier LICENSE dit CC BY-NC-SA 4.0. On
  applique la plus restrictive.
- **Formulae** : licence par fichier, avec 105 fichiers CC BY-NC-ND 4.0.
- **CroALa** : le dépôt est en CC BY 4.0, mais quelques en-têtes indiquent CC BY 3.0 ou CC0.
- **Capitularia** : contenu « non commercial » sans licence CC, donc exclu.
- **Corpus Corporum** : CC BY-NC-SA annoncée, mais les droits varient selon le texte ; à
  reprendre texte par texte.
- **openMGH** : la licence CC BY 4.0 couvre le balisage ; le texte médiéval est libre. Il faut
  citer la MGH et la BSB. La liste des volumes est sur
  `https://www.mgh.de/de/mgh-digital/openmgh/verfuegbare-baende`, car la page anglaise
  renvoie une erreur 404.
- **LatinISE** : la version 4 est en CC BY-NC-SA, les versions 5 et 6 en CC BY-SA 4.0. La v6
  (LINDAT 11372/LRT-6140) a été prise.

## 3. Pièges rencontrés
- **Noscemus** : `unzip` échoue sur les noms de fichiers accentués de l'archive Zenodo et
  interrompt le script. Il faut utiliser `python3 -m zipfile -e`, ce que fait `telecharger.sh`.
- **zsh** : dans `"$c:refs/heads/main"`, `:r` est un modificateur zsh. Il faut écrire `"${c}:refs/heads/main"`.
- **Limites GitHub** : 100 Mo par fichier, d'où Wikisource découpé en 3 morceaux et LatinISE
  et Noscemus compressés en `.xz`. Le dépôt fait environ 1,7 Go de données git ; un premier
  push unique de 1,7 Go est passé.
- **CAMENA** : TEI P4 (`TEI.2`) en ISO-8859-1 avec une DTD externe. Le parseur est configuré
  sans DTD (`recover=True`).
- **I.Sicily** : chaque inscription a une édition `primary` et une édition `simple-lemmatized`
  qui reprend le même texte.
- **The Greek Library** (le modèle visé) n'était pas joignable (connexion refusée) lors de la
  constitution du dépôt.

## 4. Pistes
- Ajouter les sources libres sans export simple : RIB (CC BY 4.0), IRT 2009 (CC BY), papyrus
  latins de papyri.info (CC BY 3.0), Dickinson College Commentaries (CC BY-SA), autres éditions
  LDLT, Latin Text Archive.
- Construire un catalogue unifié par auteur et œuvre à partir des en-têtes TEI et des URN CTS,
  en signalant les doublons identifiés par le comptage.
- Choisir, pour chaque œuvre en double, l'édition affichée par défaut. L'ordre de priorité du
  comptage est un premier classement.
