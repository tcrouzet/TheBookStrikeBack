#!/usr/bin/env python
# -*- coding: utf-8 -*-

# https://impagina.org/scribus-scripter-api

import scribus
import re
import os
import json
import tempfile


def dump(title, items_list):
    if not items_list:
        scribus.messageBox("Information", f"La liste '{title}' est vide.")
        return False
    
    message = f"Contenu de la liste '{title}' ({len(items_list)} éléments):\n\n"
    
    for i, item in enumerate(items_list, 1):
        message += f"{i}. {item}\n"
    
    scribus.messageBox(title, message)
    return True

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

def replace_and_delete_styles(text_frame):
    """
    Remplace les styles nouvellement créés par des styles existants dans un cadre de texte,
    puis supprime les styles nouvellement créés.
    
    Args:
        text_frame (str): Nom du cadre de texte contenant le texte
    
    Returns:
        tuple: (paragraphe_remplacés, caractères_remplacés, styles_supprimés)
    """
    # Tables de substitution pour les styles de paragraphe et de caractère
    # Format: 'style_nouveau': 'style_existant'
    para_style_map = {
        'Text1_Heading 1': 'h1',
        'Text1_Heading 2': 'h2',
        'Text1_Heading 3': 'h3',
        # 'Text1_Normal': 'p',
        # 'Text1_Blockquote': 'blockquote',
        # 'Text1_Code Block': 'pre'
    }
    
    char_style_map = {
        'Text1_Bold': 'Bold',
        'Text1_Italic': 'Italic',
        # 'Text1_Inline Code': 'code',
        # 'Text1_Link': 'a'
    }
    
   
    try:
        # Vérifier quels styles de la table de substitution existent réellement
        all_p_styles = scribus.getParagraphStyles()
        all_c_styles = scribus.getCharStyles()
        
        # Filtrer les mappages pour ne garder que ceux où les deux styles existent
        valid_para_maps = {}
        for new_style, target_style in para_style_map.items():
            if new_style in all_p_styles and target_style in all_p_styles:
                valid_para_maps[new_style] = target_style
        
        valid_char_maps = {}
        for new_style, target_style in char_style_map.items():
            if new_style in all_c_styles and target_style in all_c_styles:
                valid_char_maps[new_style] = target_style
        
        # Obtenir la longueur du texte dans le cadre
        text_length = scribus.getTextLength(text_frame)
        
        # Parcourir le texte une seule fois
        pos = 0
        while pos < text_length:
            # Vérifier et remplacer le style de paragraphe si nécessaire
            para_style = scribus.getParagraphStyle(text_frame, pos)
            if para_style in valid_para_maps:
                # Trouver la fin du paragraphe
                end_pos = pos
                while end_pos < text_length and scribus.getText(text_frame, end_pos, 1) != "\r":
                    end_pos += 1
                
                # Sélectionner le paragraphe entier
                para_length = end_pos - pos + 1
                scribus.selectText(pos, para_length, text_frame)
                
                # Appliquer le style cible
                scribus.setParagraphStyle(valid_para_maps[para_style], text_frame)
                            
            # Vérifier et remplacer le style de caractère si nécessaire
            try:
                char_style = scribus.getCharacterStyle(text_frame, pos)
                if char_style in valid_char_maps:
                    # Trouver la fin du segment avec ce style de caractère
                    # (Ceci est conceptuel, l'API Scribus pourrait ne pas offrir cette fonctionnalité directement)
                    # Pour simplifier, nous appliquons le style au caractère actuel seulement
                    scribus.selectText(pos, 1, text_frame)
                    scribus.setCharacterStyle(valid_char_maps[char_style], text_frame)
                    char_replaced += 1
            except:
                # Ignorer les erreurs de style de caractère
                pass
            
            # Avancer au caractère suivant
            pos += 1
        
        # Supprimer les styles nouvellement créés qui ont été remplacés
        for old_style in valid_para_maps.keys():
            try:
                scribus.deleteStyle(old_style)
            except:
                pass
        
        for old_style in valid_char_maps.keys():
            try:
                scribus.deleteCharStyle(old_style)
            except:
                pass
                
        return True
        
    except Exception as e:
        scribus.messageBox("Erreur", f"Erreur lors du remplacement des styles: {str(e)}")
        return (0, 0, 0)

def add_page_with_text_frame():
    # Récupérer le numéro de la page courante
    current_page = scribus.currentPage()
    
    # Ajouter une nouvelle page après la page courante
    scribus.newPage(-1)  # -1 signifie "après la page courante"
    new_page = scribus.currentPage()
    
    # Appliquer le même gabarit que la page précédente, si disponible
    try:
        current_master = scribus.getMasterPage(current_page)
        scribus.applyMasterPage(current_master, new_page)
    except:
        pass  # Ignorer si cette fonctionnalité n'est pas disponible
    
    # Créer un cadre de texte similaire à celui de la première page
    scribus.gotoPage(1)  # Aller à la première page
    original_frame = "TextFrame1"  # Remplacez par le nom de votre cadre original
    
    original_x, original_y = scribus.getPosition(original_frame)
    original_width, original_height = scribus.getSize(original_frame)
    
    # Aller à la nouvelle page
    scribus.gotoPage(new_page)
    
    # Créer un nouveau cadre avec les mêmes dimensions
    new_frame = scribus.createText(original_x, original_y, original_width, original_height)
    
    # Gérer les colonnes si nécessaire
    try:
        col_count = scribus.getColumns(original_frame)
        scribus.setColumns(new_frame, col_count)
        col_gap = scribus.getColumnGap(original_frame)
        scribus.setColumnGap(new_frame, col_gap)
    except:
        pass
    
    return new_frame


def handle_text_overflow(initial_frame):
    current_frame = initial_frame
    
    # Tant qu'il y a du texte en débordement
    while scribus.textOverflows(current_frame) == 1:
        # Ajouter une nouvelle page avec un cadre
        new_frame = add_page_with_text_frame()
        
        # Chaîner le cadre actuel avec le nouveau
        scribus.linkTextFrames(current_frame, new_frame)
        
        # Le nouveau cadre devient le cadre courant
        current_frame = new_frame


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
    # html_content = markdown_to_html_basic(md_content)
    html_content = replace_nbsp(md_content)
    
    # Créer un fichier HTML temporaire
    try:
        temp_file = tempfile.NamedTemporaryFile(suffix='.md', delete=False, mode='w', encoding='utf-8')
        temp_file.write(html_content)
        temp_html_path = temp_file.name
        temp_file.close()

        # Copier le contenu du fichier temporaire dans le fichier de débogage
        debug_html_path = os.path.join(script_dir, "_debug_markdown.md")
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

        # handle_text_overflow(text_frame)
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