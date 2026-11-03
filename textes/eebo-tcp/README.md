# EEBO-TCP : livres latins

Trois livres latins saisis par la [Text Creation Partnership](https://textcreationpartnership.org)
(Early English Books Online, phase I), en TEI P5. Le TCP a versé les textes de la phase I au
domaine public le 1er janvier 2015. Chaque livre vient de son dépôt
`github.com/textcreationpartnership/<identifiant>` ; `.version-amont` donne le commit repris.

| Fichier | Auteur | Titre | Édition |
|---|---|---|---|
| `A41890.xml` | Galileo Galilei | *Systema cosmicum* (le *Dialogo* en latin) | Londres, 1663 |
| `A03054.xml` | Edward Herbert of Cherbury | *De veritate* | Londres, 1633 |
| `A44008.xml` | Thomas Hobbes | *Problemata physica* | Londres, 1662 |

La saisie garde les abréviations de l'imprimé (traits de nasale, `<expan>`, ę), les coupures de
fin de ligne et les lettres illisibles (`<gap>`). Le dépôt adnotationes-latinae les résout dans
`scripts/annotation/extraire_tcp.py`.
