#!/usr/bin/env bash
# Télécharge toutes les sources de la Bibliothèque latine dans un cache local,
# puis les assemble dans textes/. Usage : scripts/telecharger.sh [dossier_cache]
# Dépendances : git, curl, unzip, xz, bzip2, python3.
set -euo pipefail

RACINE="$(cd "$(dirname "$0")/.." && pwd)"
CACHE="${1:-$RACINE/.cache}"
TEXTES="$RACINE/textes"
G="$CACHE/git"
W="$CACHE/web"
mkdir -p "$G" "$W" "$TEXTES"

# --------------------------------------------------------------------------
# 1. Téléchargement
# --------------------------------------------------------------------------

clone() { # clone <owner/repo> [chemin sparse]
  local r="$1" n; n="$(echo "$r" | tr / _)"
  [ -d "$G/$n" ] && return
  if [ $# -ge 2 ]; then
    git clone -q --depth 1 --filter=blob:none --sparse "https://github.com/$r.git" "$G/$n"
    git -C "$G/$n" sparse-checkout set "$2"
  else
    git clone -q --depth 1 "https://github.com/$r.git" "$G/$n"
  fi
}

for r in PerseusDL/canonical-latinLit OpenGreekAndLatin/Latin OpenGreekAndLatin/csel-dev \
         nevenjovanovic/croatiae-auctores-latini-textus nevenjovanovic/camena-neolatinlit \
         dracor-org/neolatdracor Formulae-Litterae-Chartae/formulae-open DigitalLatin/caesar-balex \
         DigitalLatin/Problemata Mythologos/Notre-Dame-Digitized-Latin-Collection ISicily/ISicily \
         PatristicTextArchive/pta_data ccnmtl/epistolae-hugo; do
  clone "$r"
done
clone OpenGreekAndLatin/patrologia_latina-dev data
clone epigraphic-database-heidelberg/data inscriptions
clone DigitalLatin/pgls-data digiliblt-data

fetch() { [ -s "$2" ] || curl -sSL -A "bibliotheque-latine" -o "$2" "$1"; }

mkdir -p "$W/openmgh" "$W/latinise" "$W/wikisource" "$W/noscemus" "$W/vulgata" "$W/gutenberg/txt"

# openMGH : liste des volumes publiée par les MGH
curl -sSL https://www.mgh.de/de/mgh-digital/openmgh/verfuegbare-baende \
  | grep -oE 'https://data.mgh.de/openmgh/[^"]+\.zip' | sort -u > "$W/openmgh/urls.txt"
while read -r u; do fetch "$u" "$W/openmgh/$(basename "$u")"; done < "$W/openmgh/urls.txt"

# LatinISE v6 (LINDAT 11372/LRT-6140)
fetch https://lindat.mff.cuni.cz/repository/server/api/core/bitstreams/9d2404a0-04b1-48f5-a189-a2745b5c1cad/content \
      "$W/latinise/latin14.txt"
# Wikisource latine (dump Wikimedia)
fetch https://dumps.wikimedia.org/lawikisource/latest/lawikisource-latest-pages-articles.xml.bz2 \
      "$W/wikisource/lawikisource-latest-pages-articles.xml.bz2"
# Noscemus Digital Sourcebook (Zenodo 15040256)
fetch "https://zenodo.org/api/records/15040256/files/Noscemus_Digital_Sourcebook.zip/content" \
      "$W/noscemus/Noscemus_Digital_Sourcebook.zip"
# Vulgate clémentine (eBible.org, latVUC)
for f in latVUC_usfx.zip latVUC_readaloud.zip; do fetch "https://ebible.org/Scriptures/$f" "$W/vulgata/$f"; done

# Project Gutenberg : tous les livres marqués « la » (API Gutendex)
if [ ! -s "$W/gutenberg/catalogue.json" ]; then
  url="https://gutendex.com/books/?languages=la"; i=0; : > "$W/gutenberg/pages.list"
  while [ -n "$url" ] && [ "$url" != "None" ]; do
    curl -sSL "$url" > "$W/gutenberg/page$i.json"; echo "$W/gutenberg/page$i.json" >> "$W/gutenberg/pages.list"
    url=$(python3 -I -c "import json,sys;print(json.load(open(sys.argv[1]))['next'])" "$W/gutenberg/page$i.json"); i=$((i+1))
  done
  python3 -I -c "
import json,sys
out=[b for f in open(sys.argv[1]).read().split() for b in json.load(open(f))['results']]
json.dump(out,open(sys.argv[2],'w'),ensure_ascii=False,indent=1)" "$W/gutenberg/pages.list" "$W/gutenberg/catalogue.json"
fi
python3 -I -c "
import json,sys
for b in json.load(open(sys.argv[1])):
  f=b['formats']
  u=next((v for k,v in f.items() if k.startswith('text/plain') and 'utf-8' in k),None) or next((v for k,v in f.items() if k.startswith('text/plain')),None)
  if u: print(b['id'],u)" "$W/gutenberg/catalogue.json" > "$W/gutenberg/urls.txt"
while read -r id u; do fetch "$u" "$W/gutenberg/txt/pg$id.txt"; done < "$W/gutenberg/urls.txt"

# --------------------------------------------------------------------------
# 2. Assemblage dans textes/
# --------------------------------------------------------------------------

copie() { # copie <dépôt-cache> <cible> <chemins...>
  local src="$G/$1" dst="$TEXTES/$2"; shift 2
  mkdir -p "$dst"
  for p in "$@"; do rsync -a --exclude .git "$src/$p" "$dst/"; done
  git -C "$src" log -1 --format='%H %cI' > "$dst/.version-amont"
}

copie PerseusDL_canonical-latinLit             perseus-canonical-latinlit data README.md license.md canonical-latinLit.tracking.json
copie OpenGreekAndLatin_Latin                  ogl-latin                  data README.md license.md
copie OpenGreekAndLatin_csel-dev               ogl-csel                   data README.md
copie OpenGreekAndLatin_patrologia_latina-dev  ogl-patrologia-latina      data README.md edition_metadata.csv
copie DigitalLatin_pgls-data                   digiliblt                  digiliblt-data/
copie nevenjovanovic_croatiae-auctores-latini-textus croala               txts README.md LICENSE.md croala-wordcounts.xml
copie nevenjovanovic_camena-neolatinlit        camena                     cera historicapolitica poemata thesaurus README.md LICENSE.md Wordcount.md
copie dracor-org_neolatdracor                  neolatdracor               tei corpus.xml meta.yaml README.md LICENSE
copie Formulae-Litterae-Chartae_formulae-open  formulae-litterae-chartae  data README.md CITATION.cff
copie DigitalLatin_caesar-balex                dll-caesar-bellum-alexandrinum ldlt-balex.xml ldlt-balex.pdf README.md
copie DigitalLatin_Problemata                  dll-problemata             edition.xml problems1.xml problems2.xml README.md
copie Mythologos_Notre-Dame-Digitized-Latin-Collection notre-dame-latin   data README.md LICENSE
copie ccnmtl_epistolae-hugo                    epistolae                  content/letter content/woman content/people content/about.md README.md LICENSE
copie epigraphic-database-heidelberg_data      edh-inscriptions           inscriptions README.md

# PTA : uniquement les textes latins
mkdir -p "$TEXTES/pta-latin"
(cd "$G/PatristicTextArchive_pta_data" && find data -name '*lat*.xml' -print0 | rsync -a --from0 --files-from=- . "$TEXTES/pta-latin/")
cp "$G/PatristicTextArchive_pta_data/README.md" "$G/PatristicTextArchive_pta_data/CITATION.cff" "$TEXTES/pta-latin/"
git -C "$G/PatristicTextArchive_pta_data" log -1 --format='%H %cI' > "$TEXTES/pta-latin/.version-amont"

# I.Sicily : uniquement les inscriptions comportant du latin
mkdir -p "$TEXTES/isicily-latin/inscriptions"
grep -lE 'xml:lang="la"' "$G/ISicily_ISicily/inscriptions/"*.xml | xargs -I{} cp {} "$TEXTES/isicily-latin/inscriptions/"
cp "$G/ISicily_ISicily/README.md" "$G/ISicily_ISicily/licence.txt" "$G/ISicily_ISicily/CITATION.cff" "$TEXTES/isicily-latin/"
git -C "$G/ISicily_ISicily" log -1 --format='%H %cI' > "$TEXTES/isicily-latin/.version-amont"

# openMGH : XML décompressés
mkdir -p "$TEXTES/openmgh/xml"
for z in "$W/openmgh/"*.zip; do unzip -oqj "$z" '*.xml' -d "$TEXTES/openmgh/xml"; done

# LatinISE : texte vertical compressé (xz)
mkdir -p "$TEXTES/latinise"
[ -s "$TEXTES/latinise/latinise-v6.vert.xz" ] || xz -T0 -9 -c "$W/latinise/latin14.txt" > "$TEXTES/latinise/latinise-v6.vert.xz"

# Wikisource : dump découpé en morceaux de 90 Mo (cat wikisource-la.xml.bz2.part-* > dump.xml.bz2)
mkdir -p "$TEXTES/wikisource-la"
split -b 90m -d "$W/wikisource/lawikisource-latest-pages-articles.xml.bz2" \
  "$TEXTES/wikisource-la/lawikisource-pages-articles.xml.bz2.part-"

# Noscemus : un fichier .txt.xz par ouvrage
mkdir -p "$TEXTES/noscemus/textes"
rm -rf "$CACHE/noscemus-extrait"  # unzip gère mal les noms accentués de cette archive
python3 -I -m zipfile -e "$W/noscemus/Noscemus_Digital_Sourcebook.zip" "$CACHE/noscemus-extrait"
(cd "$CACHE/noscemus-extrait/Noscemus_Digital_Sourcebook" && find . -name '*.txt' -print0 \
  | while IFS= read -r -d '' f; do mkdir -p "$TEXTES/noscemus/textes/$(dirname "$f")"; xz -9 -c "$f" > "$TEXTES/noscemus/textes/$f.xz"; done)

# Vulgate clémentine
mkdir -p "$TEXTES/vulgata-clementina/usfx" "$TEXTES/vulgata-clementina/chapitres"
unzip -oq "$W/vulgata/latVUC_usfx.zip" -d "$TEXTES/vulgata-clementina/usfx"
unzip -oq "$W/vulgata/latVUC_readaloud.zip" -d "$TEXTES/vulgata-clementina/chapitres"

# Project Gutenberg
mkdir -p "$TEXTES/gutenberg-latin/txt"
cp "$W/gutenberg/txt/"*.txt "$TEXTES/gutenberg-latin/txt/"
cp "$W/gutenberg/catalogue.json" "$TEXTES/gutenberg-latin/catalogue.json"

echo "Assemblage terminé : $(du -sh "$TEXTES" | cut -f1)"
