#!/bin/bash

# Fonction de génération Pandoc réutilisable
generate_output() {
    local source="$1"
    local format="$2"
    local title="$3"
    local subtitle="$4"
    local author="$5"
    local description="$6"
    local author_url="$7"
    local subject="$8"
    local rights="$9"
    local publisher="${10}"
    local toc_level="${11}"
    local cover="${12}"
    local css="${13}"
    local fonts="${14}"
    
    # Valeurs par défaut
    toc_level=${toc_level:-2}
    
    # Calculs automatiques
    local script_dir=$(dirname "$0")
    local source_name="$(basename "${source%.*}")"
    local output_base="$script_dir/builds/$source_name"

    echo "Source: $source_name"
    echo "Output base: $output_base"
    
    # Test d'existence du fichier source
    if [ ! -f "$source" ]; then
        echo "Erreur: Le fichier source '$source' n'existe pas."
        return 1
    fi
    
    if [ "$format" == "latex" ]; then
        local output_file="$output_base.tex"
        local pandoc_format="latex"
    else
        local output_file="$output_base.$format"
        local pandoc_format="$format"
    fi

    local charcount=$(cat "$source" | sed 's/\n\n/\n/g' | wc -c -m)
    local charcount_k=$((charcount / 1000))
    local date_formatted="${charcount_k}k signes - $(date '+%Y-%m-%d')"
    
    echo "Generating $format ${charcount_k}k signes..."

    if [ "$format" == "epub" ]; then
        # Configuration spécifique pour EPUB
        pandoc $source --to epub -o $output_file \
            --metadata title="$title" \
            --metadata subtitle="$subtitle" \
            --metadata author="$author" \
            --metadata author-url="$author_url" \
            --metadata lang="fr" \
            --metadata rights="$rights" \
            --metadata publisher="$publisher" \
            --metadata publisher-url="" \
            --metadata identifier="$date_formatted" \
            --metadata isbn="" \
            --metadata isbn-ebook="" \
            --metadata date="${charcount_k}k signes - $(date '+%Y-%m-%d')" \
            --metadata description="$description" \
            --metadata subject="$subject" \
            --metadata reference-location="document" \
            $([ "$cover" ] && echo "--metadata cover-image=$cover") \
            $([ "$css" ] && echo "--css=$css") \
            $(for font in $fonts; do echo "--epub-embed-font=$font"; done) \
            --toc-depth=$toc_level \
            --split-level=$toc_level \
            --shift-heading-level-by=0 \
            --lua-filter=./templates/epub/epub-thin-space.lua \
            --lua-filter=./templates/epub/epub-tab.lua \
            --resource-path=.:src::_i

    elif [ "$format" = "docx" ]; then
        pandoc "$source" --to docx -o "$output_file" \
            --metadata title="$title" \
            --metadata subtitle="$subtitle" \
            --metadata author="$author" \
            --metadata description="$description" \
            --metadata subject="$subject" \
            --metadata rights="$rights" \
            --metadata date="$date_formatted" \
            --reference-doc="./templates/docx/model.docx" \
            --lua-filter="./templates/docx/word-spacer.lua" \
            --lua-filter="./templates/docx/word-tab.lua" \
            --resource-path=.:src::_i

    else
        pandoc "$source" --to $pandoc_format -o "$output_file" \
            --metadata zone=true \
            --metadata title="$title" \
            --metadata author="$author" \
            --metadata charcount="$charcount_k" \
            --metadata date="$date_formatted" \
            --metadata subtitle="$subtitle" \
            --metadata publisher="" \
            --metadata rights="$rights" \
            --metadata language="fr-FR" \
            --metadata cover-image="" \
            --template=./templates/latex/a5book.tex \
            $([ "$format" == "pdf" ] && echo "--pdf-engine=xelatex") \
            --top-level-division=chapter \
            --shift-heading-level-by=0 \
            --lua-filter=./templates/latex/latex.lua \
            --resource-path=.:src::_i
    fi

    if [ $? -eq 0 ]; then
        if [ "$format" == "latex" ]; then
            echo "Generated $output_file"
        else
            echo "Opening $format in Preview..."
            open "$output_file"
        fi
        return 0
    else
        echo "Generation failed!"
        return 1
    fi
}