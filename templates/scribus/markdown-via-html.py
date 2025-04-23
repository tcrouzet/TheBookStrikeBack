#!/usr/bin/env python
# -*- coding: utf-8 -*-

import scribus
import re
import os
import json
import tempfile

def markdown_to_html_basic(md_text):
    """Convertit le Markdown en HTML basique sans dépendances externes"""
    # Nettoyer les fins de ligne
    html = md_text.replace('\r\n', '\n').replace('\r', '\n')
    
    # Pré-traitement: préserver les balises HTML pour sup et sub
    html = re.sub(r'<(/?)(sup|sub)>', r'__HTML_TAG_\1\2__', html)
    
    # Échapper les caractères HTML spéciaux
    html = html.replace('&', '&amp;')
    html = html.replace('<', '&lt;')
    html = html.replace('>', '&gt;')
    
    # Restaurer les balises HTML préservées
    html = re.sub(r'__HTML_TAG_(/?)(sup|sub)__', r'<\1\2>', html)
    
    # Traiter les citations (blockquotes)
    blockquote_lines = []
    in_blockquote = False
    blockquote_content = []
    
    lines = html.split('\n')
    processed_lines = []
    
    for line in lines:
        if line.strip().startswith('&gt;'):  # Recherche ">" qui a été échappé en "&gt;"
            # Extraire le contenu de la citation (en supprimant le '>')
            quote_content = line.strip()[4:].strip()  # 4 est la longueur de "&gt;"
            
            if not in_blockquote:
                in_blockquote = True
            
            blockquote_content.append(quote_content)
        else:
            # Si on était dans une citation et qu'on en sort
            if in_blockquote:
                # Ajouter la citation complète avec un paragraphe à l'intérieur pour mieux isoler
                processed_lines.append(f'<blockquote><p>{" ".join(blockquote_content)}</p></blockquote>')
                # Ajouter une ligne vide après le blockquote pour assurer la séparation
                processed_lines.append('')
                blockquote_content = []
                in_blockquote = False
            
            # Ajouter la ligne normale
            processed_lines.append(line)
    
    # Ne pas oublier la dernière citation si elle existe
    if in_blockquote:
        processed_lines.append(f'<blockquote><p>{" ".join(blockquote_content)}</p></blockquote>')
        processed_lines.append('')  # Ligne vide pour séparer
    
    html = '\n'.join(processed_lines)
    
    # Convertir les titres
    html = re.sub(r'^# (.*?)$', r'<h1>\1</h1>\n', html, flags=re.MULTILINE)
    html = re.sub(r'^## (.*?)$', r'<h2>\1</h2>\n', html, flags=re.MULTILINE)
    html = re.sub(r'^### (.*?)$', r'<h3>\1</h3>\n', html, flags=re.MULTILINE)
    html = re.sub(r'^#### (.*?)$', r'<h4>\1</h4>\n', html, flags=re.MULTILINE)
    html = re.sub(r'^##### (.*?)$', r'<h5>\1</h5>\n', html, flags=re.MULTILINE)
    html = re.sub(r'^###### (.*?)$', r'<h6>\1</h6>\n', html, flags=re.MULTILINE)
    
    # Traiter le gras et l'italique avant de créer les paragraphes
    html = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', html)
    html = re.sub(r'\*(.*?)\*', r'<em>\1</em>', html)
    
    # Convertir les paragraphes
    paragraphs = []
    current_p = []
    
    for line in html.split('\n'):
        line_stripped = line.strip()
        
        # Ignorer les lignes vides
        if not line_stripped:
            if current_p:
                paragraphs.append('<p>' + ' '.join(current_p) + '</p>')
                current_p = []
            continue
            
        # Ignorer les lignes qui sont déjà des balises HTML
        if (line_stripped.startswith('<h') and line_stripped[2].isdigit()) or \
           line_stripped.startswith('<blockquote'):
            if current_p:
                paragraphs.append('<p>' + ' '.join(current_p) + '</p>')
                current_p = []
            paragraphs.append(line)
            continue
            
        # Ajouter à la ligne de paragraphe en cours
        current_p.append(line)
    
    # Ajouter le dernier paragraphe s'il existe
    if current_p:
        paragraphs.append('<p>' + ' '.join(current_p) + '</p>')
    
    # Reconstituer le HTML
    html = '\n'.join(paragraphs)
    
    # Structure HTML minimale avec quelques styles pour aider Scribus
    return """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        h1 { font-family: "Noto Sans"; }
    </style>
</head>
<body>""" + html + """</body></html>"""


def replace_nbsp(text):
    """Remplace toutes les formes d'espaces insécables par des demi-quadratins"""
    # U+00A0 = espace insécable standard
    # U+202F = espace insécable étroit
    # &nbsp; = entité HTML
    return re.sub(r'(&nbsp;|[\u00A0\u202F])', ' ', text)


def markdown_to_scribus():
    if not scribus.haveDoc():
        scribus.messageBox("Erreur", "Veuillez d'abord créer un document")
        return
    
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
    except Exception as e:
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
    try:
        with open(md_file, 'r', encoding='utf-8') as f:
            md_content = f.read()
    except Exception as e:
        scribus.messageBox("Erreur", f"Impossible de lire le fichier: {str(e)}")
        return
    
    # Convertir le Markdown en HTML basique
    html_content = markdown_to_html_basic(md_content)
    html_content = replace_nbsp(html_content)
    
    # Créer un fichier HTML temporaire
    try:
        temp_file = tempfile.NamedTemporaryFile(suffix='.html', delete=False, mode='w', encoding='utf-8')
        temp_file.write(html_content)
        temp_html_path = temp_file.name
        temp_file.close()

        # Copier le contenu du fichier temporaire dans le fichier de débogage
        debug_html_path = os.path.join(script_dir, "debug_markdown.html")
        with open(debug_html_path, 'w', encoding='utf-8') as debug_file:
            debug_file.write(html_content)

    except Exception as e:
        scribus.messageBox("Erreur", f"Impossible de créer le fichier HTML temporaire: {str(e)}")
        return
    
    # Supprimer le contenu actuel du cadre
    scribus.deleteText(text_frame)
    
    # Insérer le HTML dans Scribus
    try:
        scribus.insertHtmlText(temp_html_path, text_frame)
        scribus.hyphenateText(text_frame)
    except Exception as e:
        scribus.messageBox("Erreur", f"Erreur lors de l'insertion du HTML: {str(e)}")
    
    # Supprimer le fichier temporaire
    try:
        os.unlink(temp_html_path)
    except:
        pass
    
    scribus.redrawAll()

if __name__ == '__main__':
    markdown_to_scribus()