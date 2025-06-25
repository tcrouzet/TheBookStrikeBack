#!/usr/bin/env python
# -*- coding: utf-8 -*-

# https://impagina.org/scribus-scripter-api/text-style/

import scribus
import re
import os
import json


def clean_markdown(text):
    """Nettoie et prépare le texte Markdown"""
    # Normaliser les fins de ligne
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    
    # Remplacer les multiples sauts de ligne par un seul (préserve les paragraphes)
    text = re.sub(r'\n{2,}', '\n', text)
    
    return text

def replace_nbsp(text):
    """Remplace toutes les formes d'espaces insécables par des demi-quadratins"""
    # U+00A0 = espace insécable standard
    # U+202F = espace insécable étroit
    # &nbsp; = entité HTML
    return re.sub(r'(&nbsp;|[\u00A0\u202F])', ' ', text)

def insert_position(text_frame):
    initial_length = scribus.getTextLength(text_frame)
    return initial_length if initial_length != -1 else 0


def caracter_style(text_frame, insert_pos, content, pattern, style_name):
    # Appliquer le gras aux portions marquées
    matches = list(pattern.finditer(content))
    current_pos = 0
    
    for match in matches:
        bold_start = match.start() - current_pos
        bold_text = match.group(1)
        bold_length = len(bold_text)
        
        # Calculer la position dans le texte inséré
        text_start = insert_pos + bold_start
        
        # Sélectionner et mettre en gras
        scribus.selectText(text_start, bold_length, text_frame)

        if style_name == "Bold" or style_name == "Italic":
            font_name = scribus.getFont(text_frame)
            new_font= font_name.replace("Regular", style_name)
            scribus.setFont(new_font, text_frame)
        elif style_name == "sup":
            scribus.setCharacterStyle("Exposant", text_frame)
            continue

            # scribus.setFontFeatures("+smcp", text_frame) # Small caps
            current_size = scribus.getFontSize(text_frame)
            scribus.setFontSize(current_size * 0.7, text_frame)
            scribus.setFontFeatures("sups=1", text_frame) 
            
        elif style_name == "sub":
            scribus.setCharacterStyle("Indice", text_frame)


def insert_column_break(text_frame):
    return
    insert_pos = insert_position(text_frame)
    scribus.insertText(chr(12), insert_pos, text_frame)


def insert_paragraph(text_frame, text, style_name, prefix_length):
    """Applique un style de paragraphe à la position donnée"""

    if len(text) == 0:
        return 0

    try:

        if style_name == "h1" or style_name == "h2":
            insert_column_break(text_frame)

        insert_pos = insert_position(text_frame)

        content = text[prefix_length:]

        # Rechercher les marqueurs
        bold_pattern = re.compile(r'\*\*(.*?)\*\*')
        ital_pattern = re.compile(r'(?<!\*)\*((?!\*).+?)\*(?!\*)')
        sup_pattern = re.compile(r'<sup>(.*?)</sup>')
        sub_pattern = re.compile(r'<sub>(.*?)</sub>')

        # Remplacer les marqueurs par le texte simple
        to_insert = bold_pattern.sub(r'\1', content)
        to_insert = ital_pattern.sub(r'\1', to_insert)
        to_insert = sup_pattern.sub(r'\1', to_insert)
        to_insert = sub_pattern.sub(r'\1', to_insert)
        to_insert += "\r"

        # Insérer le texte nettoyé
        scribus.insertText(to_insert, insert_pos, text_frame)

        # Appliquer le style de paragraphe
        end_pos = insert_position(text_frame)
        count = end_pos - insert_pos
        scribus.selectText(insert_pos, count, text_frame)
        scribus.setParagraphStyle(style_name, text_frame)

        caracter_style(text_frame, insert_pos, content, bold_pattern, "Bold")
        caracter_style(text_frame, insert_pos, content, ital_pattern, "Italic")
        caracter_style(text_frame, insert_pos, content, sup_pattern, "sup")
        caracter_style(text_frame, insert_pos, content, sub_pattern, "sub")


    except Exception as e:
        scribus.messageBox("Erreur", 
            f"Erreur: {str(e)}\n"
            f"Texte: {text}\n"
            f"Longueur du texte: {len(text)}\n"
            f"Position: {insert_pos}\n"
            f"Style: {style_name}\n"
            f"Longueur totale: {scribus.getTextLength(text_frame)}"
        )
        exit()
        
def markdown_to_scribus():

    if not scribus.haveDoc():
        scribus.messageBox("Erreur", "Veuillez d'abord créer un document")
        return
    
    scribus.setRedraw(False)

    # Obtenir le chemin du script actuel
    script_dir = os.path.dirname(os.path.realpath(__file__))
    config_file = os.path.join(script_dir, "markdown.json")

    # Charger le dernier répertoire s'il existe
    last_directory = ""
    try:
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                config = json.load(f)
                last_directory = config.get("last_directory", "")
                if last_directory and os.path.exists(last_directory):
                    os.chdir(last_directory)
    except:
        pass
    
    md_file = scribus.fileDialog("Ouvrir un fichier Markdown", "*.md")

    if not md_file:
        return
    
    new_directory = os.path.dirname(md_file)

    # Enregistrer le nouveau répertoire
    try:
        with open(config_file, 'w') as f:
            json.dump({"last_directory": new_directory}, f)
    except:
        pass

    # Créer un cadre de texte si aucun n'est sélectionné
    try:
        text_frame = scribus.getSelectedObject()
        if scribus.getObjectType(text_frame) != "TextFrame":
            raise Exception
    except:
        # Aucun cadre de texte sélectionné, on en crée un
        page_width = scribus.getPageWidth()
        page_height = scribus.getPageHeight()
        margins = scribus.getPageMargins()
        text_frame = scribus.createText(margins[1], margins[0], 
                                        page_width - margins[1] - margins[3], 
                                        page_height - margins[0] - margins[2])
    

    # Lire le fichier Markdown
    with open(md_file, 'r', encoding='utf-8') as f:
        md_content = f.read()
    md_content = clean_markdown(md_content)
    md_content = replace_nbsp(md_content)

    # Insérer le texte brut
    # scribus.insertText(md_content, 0, text_frame)
    
    # Définir les noms des styles à créer
    style_names = {
                    "h1": "# ",
                    "h2": "## ",
                    "h3": "### ",
                    "h4": "#### ",
                    "h5": "##### ",
                    "h6": "###### ",
                    "blockquote": ">",
                    "normal": ""
                }

    # Créer les styles s'ils n'existent pas déjà
    existing_styles = scribus.getParagraphStyles()
    for style_name in style_names:
        if style_name not in existing_styles:
            scribus.createParagraphStyle(style_name)

    existing_character_styles = scribus.getCharStyles()
    # scribus.messageBox("Erreur", "Styles de caractères existants : " + str(existing_character_styles))
    if "Exposant" not in existing_character_styles:
         scribus.createCharStyle("Exposant")
    if "Indice" not in existing_character_styles:
         scribus.createCharStyle("Indice")


    # Parcourir le texte et appliquer les styles
    lines = md_content.split('\n')
    
    scribus.deleteText(text_frame)

    for line in lines:

        done = False
        for style_name, prefix in style_names.items():
            if style_name == "normal":
                continue
            if line.startswith(prefix):
                insert_paragraph(text_frame, line, style_name, len(prefix))
                done = True

        if not done:
            insert_paragraph(text_frame, line, "normal", 0)

    scribus.setRedraw(True)
    scribus.redrawAll()
    scribus.hyphenateText(text_frame)
    scribus.redrawAll()


if __name__ == '__main__':
    markdown_to_scribus()