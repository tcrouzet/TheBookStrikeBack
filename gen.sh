#!/bin/bash
#chmod +x gen.sh
# Requirements:
# - pandoc
# - Playfair Display font (should be available in the package texlive-fonts-extra on Debian )
source=src/LivreContreAttaque.md 
output=LivreContreAttaque

if [ "$1" = "tex" ]
then
	echo "Generating tex..."
	pandoc $source -o builds/$output.tex  \
		--metadata-file=templates/latex/latex.yml \
		--template=templates/latex/a5book.tex \
		--pdf-engine=xelatex \
		--no-highlight \
		--top-level-division=chapter \
		--shift-heading-level-by=0 \
		--lua-filter=templates/latex/latex.lua \
		--resource-path=.:src::_i
elif [ "$1" = "pdf" ]
then
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
elif [ "$1" = "epub" ]
then
	echo "Generating epub..."
	pandoc $source \
		-f markdown+footnotes \
		-t epub \
		-o builds/$output.epub \
		-d templates/epub/epub.yml \
		--resource-path=.:src::_i
elif [ "$1" = "docx" ]
then
	echo "Generating docx..."
	pandoc $source -f markdown+footnotes \
		-t docx \
		-o  builds/$output.docx \
		-d templates/docx/docx.yml \
		--lua-filter=templates/docx/docx.lua \
		--resource-path=.:src::_i
else
	echo "Please specify one the following: tex, pdf, epub, docx"
fi
			
