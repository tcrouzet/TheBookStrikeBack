# Le Livre contre-attaque (ou comment combattre la chose)

À l'aide du manuscrit du *Le Livre contre-attaque*, j'aimerais montrer comment créer un livre de qualité quasi professionnelle, uniquement avec des outils libres, sans que ce soit fastidieux.

Vous pouvez vous inspirer de ce modèle pour vos projets.

L'idée est de basculer en mode coopération.
Vous pouvez récupérer les fichiers, les lire, les annoter, faire des retours pour que le texte évolue.
Pour les retours, le format DOCX reste idéal : il permet un suivi des corrections avancé.

J'y parle de la chose faute d'avoir trouver un mot adéquat pour désigner la chose à combattre.

## Formats disponibles

- [Markdown](src/LivreContreAttaque.md)
- [PDF](builds/LivreContreAttaque.pdf)
- [EPUB](builds/LivreContreAttaque.epub)
- [DOCX](builds/LivreContreAttaque.docx)
- [TEX](builds/LivreContreAttaque.tex)

## Police

Pour le PDF, j'ai choisi une police [Open Font License](https://openfontlicense.org/open-font-license-official-text/).

La [Playfair Display](https://fonts.google.com/specimen/Playfair+Display?query=Playfair) est une police x-height élevé : les majuscules et les minuscules hautes dépassent à peine les minuscules basses (contrairement à ce qui était le cas dans les typos classiques comme le Garamond). Les polices avec  x-height élevé permettent de réduire le corps du texte tout en maintenant une forte lisibilité.

La fonte est, en théorie, disponible sur les systèmes Debians dans le package texlive-fonts-extra

## Prérequis pour générer les builds

Installer Latex (sur mac, j'utilise https://www.texmacs.org/tmweb/download/macosx.en.html, version complète 4 Go).

Sur le terminal:

```bash
which tex
tex --version
```

Pour voir si install OK.

Installer Pandoc (https://pandoc.org/installing.html)

Sur le terminal:

```bash
which pandoc
pandoc --version
```

Pour voir si install OK.

Je travaille avec Texmacs 2025 et Pandoc 3.6.4

Sur Mac, mise à jour de pandoc :

```bash
brew upgrade pandoc
```

## Générer les builds

Depuis la racine du projet, lancer le script gen.sh avec en argument le format choisi parmi tex, pdf, epub ou docx.

```bash
./gen.sh tex
./gen.sh pdf
./gen.sh epub
./gen.sh docx
```

## Scribus

J'ai essayé de travailler avec [Scribus](https://www.scribus.net/), me heurtant vite à de nombreuses limitations.

J'ai commencé à développer un script d'importation Markdown, plus complet que la fonction native, mais j'ai un peu jeté l'éponge, tant l'API est limité (faudra que j'y revienne).

[![License: CC BY 4.0](https://img.shields.io/badge/License-CC%20BY%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by/4.0/)
