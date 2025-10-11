#!/bin/bash
#chmod +x gen.sh
# Requirements:
# - pandoc
# ./gen.sh

# Import des fonctions partagées
source "./templates/lib/pandoc_gen.sh"

# Params
md_source="./src/LivreContreAttaque.md"
title="Le Livre contre-attaque"
subtitle=""
author="Thierry Crouzet"
description="Le livre arme pour lutter contre la chose."
author_url="https://tcrouzet.com"
subject="essai, tracts, IA, fascisme, internet, technologie"
rights="(cc) by-nc-nd, $(date '+%Y'), Thierry Crouzet"
identifier="ISBN-0"
publisher=""
toc_level=2
cover="./src/_i/cover.jpg"
css="./templates/epub/epub.css"
fonts=""

# Génération avec format en paramètre
generate_output "$md_source" "${1:-pdf}" "$title" "$subtitle" "$author" \
               "$description" "$author_url" "$subject" "$rights" \
               "$publisher" "$toc_level" "$cover" "$css" "$fonts"
