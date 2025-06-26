#!/usr/bin/env python
# -*- coding: utf-8 -*-

# https://impagina.org/scribus-scripter-api

import scribus
import re
import os
import json
import tempfile
import xml.etree.ElementTree as ET
from xml.dom import minidom

def dump(items_list, title=""):
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



class Markdown2Scribus:

    def __init__(self):
        
        # Obtenir le chemin du script actuel
        self.script_dir = os.path.dirname(os.path.realpath(__file__))
        self.config_file = os.path.join(self.script_dir, "markdown.json")

        # Charger le dernier répertoire de travail s'il existe
        self.directory = ""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    self.directory = config.get("last_directory", "")
                    if self.directory and os.path.exists(self.directory):
                        os.chdir(self.directory)
        except Exception as e:
            pass

        self.md_content = ""
        self.text_frame = None

    def update_directory(self, md_file):
        self.directory = os.path.dirname(md_file)
        try:
            with open(self.config_file, 'w') as f:
                json.dump({"last_directory": self.directory}, f)
        except:
            pass


    def get_md(self):
        if not scribus.haveDoc():
            scribus.messageBox("Erreur", "Veuillez d'abord créer un document")
            return
        
        md_file = scribus.fileDialog("Ouvrir un fichier Markdown", "*.md")

        if not md_file:
            return
        
        self.update_directory(md_file)

        # Tester si frame selected
        try:
            self.text_frame = scribus.getSelectedObject()
            if scribus.getObjectType(self.text_frame) != "TextFrame":
                raise Exception
        except:
            scribus.messageBox("Information", "Aucun cadre de texte sélectionné")
            return True
        
        # Lire le fichier Markdown
        try:
            with open(md_file, 'r', encoding='utf-8') as f:
                self.md_content = f.read()
        except Exception as e:
            scribus.messageBox("Erreur", f"Impossible de lire le fichier: {str(e)}")
            return True
        
        # Update MD
        self.md_content = self.replace_nbsp(self.md_content)
        self.md_content = self.clean_blockquote_spaces(self.md_content)
        self.md_content = self.tag_ln(self.md_content)
        self.md_content = self.tag_stars_in_code(self.md_content)
        
    def via_html(self):
        # Créer un fichier HTML temporaire
        try:
            temp_file = tempfile.NamedTemporaryFile(suffix='.md', delete=False, mode='w', encoding='utf-8')
            temp_file.write(self.md_content)
            temp_html_path = temp_file.name
            temp_file.close()

            # Copier le contenu du fichier temporaire dans le fichier de débogage
            debug_html_path = os.path.join(self.script_dir, "_debug_markdown.md")
            with open(debug_html_path, 'w', encoding='utf-8') as debug_file:
                debug_file.write(self.md_content)

        except Exception as e:
            scribus.messageBox("Erreur", f"Impossible de créer le fichier HTML temporaire: {str(e)}")
            return
        
        # Supprimer le contenu actuel du cadre
        scribus.deleteText(self.text_frame)
        
        # Insérer le HTML dans Scribus
        try:
            scribus.insertHtmlText(temp_html_path, self.text_frame)

            # handle_text_overflow(text_frame)
            scribus.hyphenateText(self.text_frame)
        except Exception as e:
            scribus.messageBox("Erreur", f"Erreur lors de l'insertion du HTML: {str(e)}")

        # Supprimer le fichier temporaire
        try:
            os.unlink(temp_html_path)
        except:
            pass
        
        scribus.redrawAll()


    def markdown_formatting(self):
        """Applique le formatage Markdown directement sans passer par HTML"""
        
        # dump(scribus.getParagraphStyles())
        # dump(scribus.getCharStyles())

        scribus.setRedraw(False)
        self.init_frame()
        
        self.md_content = self.md_content.replace('\n\n', '\n')
        scribus.insertText(self.md_content, 0, self.text_frame)
    
        self.apply_heading()
        self.process_blockquotes()
        self.process_bold()
        self.process_italic()
        self.process_superscript()
        self.process_subscript()
        self.restore_ln()
        self.process_spacer()
        self.process_code()
        self.restore_stars()

        scribus.setRedraw(True)
        scribus.hyphenateText(self.text_frame)

        return True

    def init_frame(self):
        scribus.deleteText(self.text_frame)

        # Créer une frame temporaire
        temp_frame = scribus.createText(0, 0, 50, 50)
        scribus.insertText("1", 0, temp_frame)
        newtext = scribus.getFrameText(temp_frame)
        scribus.deleteObject(temp_frame)
        
        scribus.insertText(newtext, 0, self.text_frame)
        scribus.deleteText(self.text_frame)
        return True


    def apply_heading(self):
        
        # Analyser d'abord toutes les modifications à faire
        modifications = []
        lines = self.md_content.splitlines()
        pos = 0
        
        for line in lines:
            line_length = len(line)
            
            # Détecter les titres et stocker les modifications
            if line.startswith('###### '):
                modifications.append({'pos': pos, 'length': line_length, 'level': 6, 'prefix_len': 7})
            elif line.startswith('##### '):
                modifications.append({'pos': pos, 'length': line_length, 'level': 5, 'prefix_len': 6})
            elif line.startswith('#### '):
                modifications.append({'pos': pos, 'length': line_length, 'level': 4, 'prefix_len': 5})
            elif line.startswith('### '):
                modifications.append({'pos': pos, 'length': line_length, 'level': 3, 'prefix_len': 4})
            elif line.startswith('## '):
                modifications.append({'pos': pos, 'length': line_length, 'level': 2, 'prefix_len': 3})
            elif line.startswith('# '):
                modifications.append({'pos': pos, 'length': line_length, 'level': 1, 'prefix_len': 2})
                
            pos += line_length + 1  # +1 pour le \n
        
        # Appliquer les modifications de la FIN vers le DÉBUT
        for mod in reversed(modifications):
            self.apply_heading_safe(mod['level'], mod['pos'], mod['length'], mod['prefix_len'])
    

    def apply_heading_safe(self, level, pos, line_length, prefix_len):
        """Applique le style de titre de manière sécurisée"""
        # D'abord appliquer le style au paragraphe entier
        scribus.selectText(pos, line_length, self.text_frame)
        scribus.setParagraphStyle(f'h{level}', self.text_frame)
        
        # Ensuite supprimer le préfixe (# )
        scribus.selectText(pos, prefix_len, self.text_frame)
        scribus.deleteText(self.text_frame)


    def process_blockquotes(self):
        """Traite les blockquotes - version simple"""
        
        frame_text = scribus.getAllText(self.text_frame)
        lines = frame_text.splitlines()
        # scribus.messageBox("line", str(len(lines)))
        # return 

        pos = 0
        chars_removed = 0
        
        for line in lines:
            line_length = len(line)
            
            if line.startswith('>'):

                # Position ajustée avec les caractères déjà supprimés
                current_pos = pos - chars_removed
                
                # Appliquer le style blockquote
                scribus.selectText(current_pos, line_length, self.text_frame)
                scribus.setParagraphStyle('blockquote', self.text_frame)
                
                # Supprimer le ">"
                scribus.selectText(current_pos, 1, self.text_frame)
                scribus.deleteText(self.text_frame)
                
                # Compter qu'on a supprimé 1 caractère
                chars_removed += 1
            
            pos += line_length + 1  # +1 pour le \n


    def process_italic(self):
        """Traite l'italique - trouve tous les matches puis les traite"""
        
        # Récupérer le texte
        frame_text = scribus.getAllText(self.text_frame)
        
        # Trouver TOUS les matches
        matches = list(re.finditer(r'\*([^*]+)\*', frame_text))
        
        # Traiter de la fin vers le début pour éviter les décalages
        for match in reversed(matches):
            match_start = match.start()
            match_end = match.end()
            
            # Sélectionner *texte*
            scribus.selectText(match_start, match_end - match_start, self.text_frame)
            scribus.setCharacterStyle('Italic', self.text_frame)
            
            scribus.selectText(match_end-1, 1, self.text_frame)
            scribus.deleteText(self.text_frame)
            scribus.selectText(match_start, 1, self.text_frame)
            scribus.deleteText(self.text_frame)
            

    def process_bold(self):
        """Traite le gras - trouve tous les matches puis les traite"""
        
        # Récupérer le texte
        frame_text = scribus.getAllText(self.text_frame)
        
        # Trouver TOUS les matches
        matches = list(re.finditer(r'\*\*([^*]+)\*\*', frame_text))
        
        # Traiter de la fin vers le début pour éviter les décalages
        for match in reversed(matches):
            match_start = match.start()
            match_end = match.end()
            
            # Sélectionner **texte**
            scribus.selectText(match_start, match_end - match_start, self.text_frame)
            scribus.setCharacterStyle('Bold', self.text_frame)
            
            # Supprimer les ** de la fin
            scribus.selectText(match_end-2, 2, self.text_frame)
            scribus.deleteText(self.text_frame)
            
            # Supprimer les ** du début
            scribus.selectText(match_start, 2, self.text_frame)
            scribus.deleteText(self.text_frame)


    def process_superscript(self):
        """Traite les exposants - trouve tous les matches puis les traite"""
        
        # Récupérer le texte
        frame_text = scribus.getAllText(self.text_frame)
        
        # Trouver TOUS les matches <sup>texte</sup>
        matches = list(re.finditer(r'<sup>([^<]+)</sup>', frame_text))
        
        # Traiter de la fin vers le début pour éviter les décalages
        for match in reversed(matches):
            match_start = match.start()
            match_end = match.end()
            
            # Sélectionner <sup>texte</sup>
            scribus.selectText(match_start, match_end - match_start, self.text_frame)
            scribus.setCharacterStyle('Exposant', self.text_frame)  # ou votre nom de style
            
            # Supprimer </sup> de la fin
            scribus.selectText(match_end-6, 6, self.text_frame)
            scribus.deleteText(self.text_frame)
            
            # Supprimer <sup> du début
            scribus.selectText(match_start, 5, self.text_frame)
            scribus.deleteText(self.text_frame)


    def process_subscript(self):
        """Traite les exposants - trouve tous les matches puis les traite"""
        
        # Récupérer le texte
        frame_text = scribus.getAllText(self.text_frame)
        
        # Trouver TOUS les matches <sup>texte</sup>
        matches = list(re.finditer(r'<sub>([^<]+)</sub>', frame_text))
        
        # Traiter de la fin vers le début pour éviter les décalages
        for match in reversed(matches):
            match_start = match.start()
            match_end = match.end()
            
            # Sélectionner <sup>texte</sup>
            scribus.selectText(match_start, match_end - match_start, self.text_frame)
            scribus.setCharacterStyle('Indice', self.text_frame)  # ou votre nom de style
            
            # Supprimer </sup> de la fin
            scribus.selectText(match_end-6, 6, self.text_frame)
            scribus.deleteText(self.text_frame)
            
            # Supprimer <sup> du début
            scribus.selectText(match_start, 5, self.text_frame)
            scribus.deleteText(self.text_frame)


    def process_spacer(self):
        """Traite les lignes --- - trouve tous les matches puis les traite"""
        
        # Récupérer le texte
        frame_text = scribus.getAllText(self.text_frame)
        
        
        # Trouver TOUTES les lignes contenant seulement ---
        matches = list(re.finditer(r'---', frame_text, re.MULTILINE))
        
        # Traiter de la fin vers le début pour éviter les décalages
        for match in reversed(matches):
            match_start = match.start()
            match_end = match.end()
            
            # Sélectionner la ligne ---
            scribus.selectText(match_start, match_end - match_start, self.text_frame)
            scribus.setParagraphStyle('spacer', self.text_frame)
            
            # Remplacer --- par *
            scribus.deleteText(self.text_frame)
            scribus.insertText('*', match_start, self.text_frame)


    def process_code(self):
        """Traite les blocs de code - trouve tous les matches puis les traite"""
        
        # Récupérer le texte
        frame_text = scribus.getAllText(self.text_frame)
        
        # Regex pour trouver les blocs de code
        matches = list(re.finditer(r'```[a-zA-Z]*[\r\n]+(.*?)[\r\n]+```', frame_text, re.DOTALL))
        
        # Traiter de la fin vers le début pour éviter les décalages
        for match in reversed(matches):
            match_start = match.start()
            match_end = match.end()
            code_content = match.group(1)
            
            # Remplacer les \n par des line breaks Unicode (comme dans restore_ln)
            code_with_linebreaks = code_content.replace('\n', '\u2028')
            code_with_linebreaks = code_content.replace('\r', '\u2028')
            
            # Supprimer tout le bloc ```...```
            scribus.selectText(match_start, match_end - match_start, self.text_frame)
            scribus.deleteText(self.text_frame)
            
            # Insérer le code avec line breaks
            scribus.insertText(code_with_linebreaks, match_start, self.text_frame)
            
            # Sélectionner le contenu inséré et appliquer le style de paragraphe
            scribus.selectText(match_start, len(code_with_linebreaks), self.text_frame)
            scribus.setParagraphStyle('code', self.text_frame)


    def add_page_breaks(self, style):
        """Force un style donné sur page impaire"""
        
        frame_text = scribus.getAllText(self.text_frame)
        lines = frame_text.splitlines()
        pos = 0
        
        for line in lines:
            line_length = len(line)
            
            # Vérifier le style du début de cette ligne
            if line_length > 0:
                scribus.selectText(pos, 1, self.text_frame)
                para_style = scribus.getParagraphStyle(self.text_frame)
                
                if para_style == style:
                    # Insérer un saut de page avant ce paragraphe
                    scribus.insertText('\x0C', pos, self.text_frame)
                    pos += 1  # Ajuster pour le caractère ajouté
            
            pos += line_length + 1


    def clean_blockquote_spaces(self, text):
        """Remplace les '\n> ' par '\n>'"""
        return re.sub(r'\n> ', '\n>', text)
    
    def replace_nbsp(self, text):
        """Remplace toutes les formes d'espaces insécables par des demi-quadratins"""
        # U+00A0 = espace insécable standard
        # U+202F = espace insécable étroit
        # &nbsp; = entité HTML
        return re.sub(r'(&nbsp;|[\u00A0\u202F])', ' ', text)

    def tag_ln(self, text):
        return re.sub(r'  \n', '<SAUT>', text)
    
    def restore_ln(self):
        """Remplace les <SAUT> par des line breaks DANS le paragraphe"""
        
        # Récupérer le texte
        frame_text = scribus.getAllText(self.text_frame)
        
        # Trouver TOUS les <SAUT>
        matches = list(re.finditer(r'<SAUT>', frame_text))
        
        # Traiter de la fin vers le début pour éviter les décalages
        for match in reversed(matches):
            match_start = match.start()
            match_end = match.end()
            
            # Sélectionner <SAUT>
            scribus.selectText(match_start, match_end - match_start, self.text_frame)
            
            # Remplacer par line break (Shift+Enter)
            scribus.deleteText(self.text_frame)
            scribus.insertText('\u2028', match_start, self.text_frame)  # Line Separator Unicode

    def tag_stars_in_code(self, text):
        """Remplace les * par <STAR> dans les blocs de code uniquement"""
        
        def replace_stars_in_match(match):
            # Récupérer le contenu du bloc de code (groupe 1)
            code_content = match.group(1)
            # Remplacer les * par <STAR>
            code_content = code_content.replace('*', '<STAR>')
            # Reconstruire le bloc complet
            return f"```{match.group(0).split('```')[0].split('\n')[0]}\n{code_content}\n```"
        
        # Regex pour capturer les blocs de code
        pattern = r'```[a-zA-Z]*\n(.*?)\n```'
        
        return re.sub(pattern, replace_stars_in_match, text, flags=re.DOTALL)
    
    def restore_stars(self):        
        # Récupérer le texte
        frame_text = scribus.getAllText(self.text_frame)
        
        # Trouver TOUS les <SAUT>
        matches = list(re.finditer(r'<STAR>', frame_text))
        
        # Traiter de la fin vers le début pour éviter les décalages
        for match in reversed(matches):
            match_start = match.start()
            match_end = match.end()
            
            # Sélectionner <SAUT>
            scribus.selectText(match_start, match_end - match_start, self.text_frame)
            
            # Remplacer par line break (Shift+Enter)
            scribus.deleteText(self.text_frame)
            scribus.insertText('*', match_start, self.text_frame)

    def handle_text_overflow(self):
        """Déroule automatiquement les gabarits page droite/gauche selon le débordement"""
        
        if not self.text_frame:
            return
        
        current_frame = self.text_frame
        pages_created = 0
        
        # Tant qu'il y a du débordement
        while scribus.textOverflows(current_frame):
            last_page = scribus.pageCount()
            
            # Déterminer le gabarit à appliquer (page paire/impaire)
            if last_page % 2 == 0:  # Dernière page paire -> prochaine sera impaire
                template_name = "Right Page"  # ou le nom de votre gabarit page droite
            else:  # Dernière page impaire -> prochaine sera paire  
                template_name = "Left Page"   # ou le nom de votre gabarit page gauche
            
            # Créer une nouvelle page avec le bon gabarit
            try:
                scribus.newPage(-1, template_name)
                pages_created += 1
                
                # Aller à la nouvelle page
                new_page = scribus.pageCount()
                scribus.gotoPage(new_page)
                
                # Trouver le bloc de texte du gabarit (assumant qu'il s'appelle "TextFrame" ou similar)
                # Vous devrez adapter le nom selon votre gabarit
                page_objects = scribus.getPageItems()
                new_frame = None
                
                for obj_name, obj_type, _ in page_objects:
                    if obj_type == 4:  # TextFrame
                        new_frame = obj_name
                        break
                
                if new_frame:
                    # Chaîner avec le bloc précédent
                    scribus.linkTextFrames(current_frame, new_frame)
                    current_frame = new_frame
                else:
                    scribus.messageBox("Erreur", f"Aucun bloc de texte trouvé dans le gabarit page {new_page}")
                    break
                    
            except Exception as e:
                scribus.messageBox("Erreur", f"Impossible d'appliquer le gabarit: {str(e)}")
                break
            
            # Sécurité
            if pages_created > 50:
                scribus.messageBox("Attention", "Plus de 50 pages créées, arrêt par sécurité")
                break
        
        if pages_created > 0:
            scribus.messagebarText(f"{pages_created} page(s) créée(s) avec gabarits")
        
        return pages_created

    def frame_creation(self):
        # Aucun cadre de texte sélectionné, on en crée un
        page_width = scribus.getPageWidth()
        page_height = scribus.getPageHeight()
        margins = scribus.getPageMargins()
        self.text_frame = scribus.createText(
            margins[1], margins[0], 
            page_width - margins[1] - margins[3], 
            page_height - margins[0] - margins[2]
        )

if __name__ == '__main__':
    convert = Markdown2Scribus()
    convert.get_md()
    # convert.via_html()
    convert.markdown_formatting()
