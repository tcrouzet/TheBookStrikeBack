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

## Prérequis pour générer les builds

Installer Latex (sur mac, j'utilise https://www.texmacs.org/tmweb/download/macosx.en.html, version complète 4 Go).

Sur le terminal:

'''which tex
tex --version'''

Pour voir si install OK.

Installer Pandoc (https://pandoc.org/installing.html)

Sur le terminal:

'''which pandoc
pandoc --version'''

Pour voir si install OK.

Je travaille avec Texmacs 2025 et Pandoc 3.6.4

Sur Mac, mise à jour de pandoc: brew upgrade pandoc

## Génération des builds

Depuis la racine du projet.

### TEX

pandoc src/LivreContreAttaque.md -o builds/LivreContreAttaque.tex  --metadata-file=templates/latex/latex.yml --template=templates/latex/A5book.tex --pdf-engine=xelatex --no-highlight --top-level-division=chapter --shift-heading-level-by=0 --lua-filter=templates/latex/latex.lua --resource-path=.:src::_i

### PDF

pandoc src/LivreContreAttaque.md -o builds/LivreContreAttaque.pdf --metadata-file=templates/latex/latex.yml --template=templates/latex/A5book.tex --pdf-engine=xelatex --no-highlight --top-level-division=chapter --shift-heading-level-by=0 --lua-filter=templates/latex/latex.lua --resource-path=.:src::_i

### ePub

pandoc src/LivreContreAttaque.md -f markdown+footnotes -t epub -o builds/LivreContreAttaque.epub -d templates/epub/epub.yml --resource-path=.:src::_i

### DOCX

pandoc src/LivreContreAttaque.md -f markdown+footnotes -t docx -o  builds/LivreContreAttaque.docx -d templates/docx/docx.yml  --lua-filter=templates/docx/docx.lua --resource-path=.:src::_i

[![License: CC BY 4.0](https://img.shields.io/badge/License-CC%20BY%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by/4.0/)
