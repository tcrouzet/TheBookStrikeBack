#!/bin/bash
#chmod +x gen.sh

echo "Generating tex..."
pandoc src/LivreContreAttaque.md -o builds/LivreContreAttaque.tex  --metadata-file=templates/latex/latex.yml --template=templates/latex/A5book.tex --pdf-engine=xelatex --no-highlight --top-level-division=chapter --shift-heading-level-by=0 --lua-filter=templates/latex/latex.lua --resource-path=.:src::_i

echo "Generating pdf..."
pandoc src/LivreContreAttaque.md -o builds/LivreContreAttaque.pdf --metadata-file=templates/latex/latex.yml --template=templates/latex/A5book.tex --pdf-engine=xelatex --no-highlight --top-level-division=chapter --shift-heading-level-by=0 --lua-filter=templates/latex/latex.lua --resource-path=.:src::_i

echo "Generating epub..."
pandoc src/LivreContreAttaque.md -f markdown+footnotes -t epub -o builds/LivreContreAttaque.epub -d templates/epub/epub.yml --resource-path=.:src::_i

echo "Generating docx..."
pandoc src/LivreContreAttaque.md -f markdown+footnotes -t docx -o  builds/LivreContreAttaque.docx -d templates/docx/docx.yml --lua-filter=templates/docx/docx.lua --resource-path=.:src::_i

