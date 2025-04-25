#!/bin/bash
#chmod +x gen.sh
# Requirements:
# - pandoc
# - Playfair Display font (should be available in the package texlive-fonts-extra on Debian )

source=src/LivreContreAttaque.md
output=LivreContreAttaque

generate_tex() {
    echo "Generating tex..."
    pandoc $source -o builds/$output.tex \
        --metadata-file=templates/latex/latex.yml \
        --template=templates/latex/a5book.tex \
        --pdf-engine=xelatex \
        --no-highlight \
        --top-level-division=chapter \
        --shift-heading-level-by=0 \
        --lua-filter=templates/latex/latex.lua \
        --resource-path=.:src::_i
}

generate_pdf() {
    echo "Generating pdf..."
    pandoc $source -o builds/$output.pdf \
        --metadata-file=templates/latex/latex.yml \
        --template=templates/latex/a5book.tex \
        --pdf-engine=xelatex \
        --no-highlight \
        --top-level-division=chapter \
        --shift-heading-level-by=0 \
        --lua-filter=templates/latex/latex.lua \
        --resource-path=.:src::_i
}

generate_epub() {
    echo "Generating epub..."
    pandoc $source \
        -f markdown+footnotes \
        -t epub \
        -o builds/$output.epub \
        -d templates/epub/epub.yml \
        --resource-path=.:src::_i
}

generate_docx() {
    echo "Generating docx..."
    pandoc $source -f markdown+footnotes \
        -t docx \
        -o builds/$output.docx \
        -d templates/docx/docx.yml \
        --lua-filter=templates/docx/docx.lua \
        --resource-path=.:src::_i
}

if [ "$1" = "tex" ]; then
    generate_tex
elif [ "$1" = "pdf" ]; then
    generate_pdf
elif [ "$1" = "epub" ]; then
    generate_epub
elif [ "$1" = "docx" ]; then
    generate_docx
elif [ "$1" = "all" ]; then
    echo "Generating all formats..."
    generate_tex
    generate_pdf
    generate_epub
    generate_docx
    echo "All formats generated successfully."
else
    echo "Please specify one the following: tex, pdf, epub, docx, all"
fi