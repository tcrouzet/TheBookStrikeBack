import scribus
import os
import xml.etree.ElementTree as ET
import json

class PostProdScribus:

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

        self.sla = None
        self.output = None
        self.root = None
        # self.headers_list = [("h4","Exergues"),("h2","Conver­sa­tion hy­per­sphé­rique"),("h1","Pre­mière par­tie")]

    def update_directory(self, md_file):
        self.directory = os.path.dirname(md_file)
        try:
            with open(self.config_file, 'w') as f:
                json.dump({"last_directory": self.directory}, f)
        except:
            pass


    def opensla(self):
        
        self.sla = scribus.fileDialog("Ouvrir un fichier Scribus", "*.sla")

        if not self.sla:
            return
        
        self.update_directory(self.sla)
        self.output = self.sla.replace(".sla", "_postprod.sla")

        self.sla_mod()

        scribus.openDoc(self.output)

        # self.del_pages(140)

        self.add_pages()

        scribus.gotoPage(1)

        return


    def sla_mod(self, styles=["h1", "h2", "h4"]):
        if not os.path.exists(self.sla):
            scribus.messageBox("Erreur", f"Le fichier source '{self.sla}' n'existe pas.")
            return False

        # Vérifier que self.output est bien défini
        if not self.output:
            print("Erreur : Le chemin du fichier de sortie (self.output) n'est pas défini.")
            return False

        try:
            # Charger le fichier SLA comme XML
            tree = ET.parse(self.sla)
            self.root = tree.getroot()

            if self.root is None:
                scribus.messageBox("Erreur", f"Impossible de parser le fichier SLA. La racine est vide.")
                return False
            
            # self.cesures()
            breaks = self.linebreaks(styles)

            tree.write(self.output, encoding='utf-8', xml_declaration=True)

            scribus.messageBox("Bilan", f"{breaks} nouveau sauts de page.")

            return True

        except ET.ParseError as e:
            scribus.messageBox("Erreur d'analyse XML", f"Le fichier '{self.sla}' n'est pas un XML valide. {e}")
            return False
        except Exception as e:
            scribus.messageBox("Erreur", e)
            return False


    def linebreaks(self, styles):
        modified_count = 0
                    
        # Trouver tous les cadres de texte
        for item_elem in self.root.findall(".//PAGEOBJECT[@PTYPE='4']"):
            # Trouver l'élément qui contient le flux de texte (souvent <StoryText>)
            story_text_elem = item_elem.find(".//StoryText")
            if story_text_elem is None:
                continue

            children_of_story = list(story_text_elem) # Convertir en liste pour modifier pendant l'itération
            j = 0 # Index pour parcourir les enfants de StoryText

            fist_page = True

            while j < len(children_of_story):
                current_elem = children_of_story[j]

                # Cible la balise <ITEXT>
                if current_elem.tag == "ITEXT":
                    # Vérifie l'élément suivant pour voir si c'est <para PARENT="h2"/>
                    if j + 1 < len(children_of_story):
                        next_elem = children_of_story[j+1]
                        
                        if next_elem.tag == "para" and next_elem.get('PARENT') in styles:

                            # Sauvegarde le texte du header                            
                            header_text = current_elem.get('CH', '').strip()

                            # Vérifie si un <breakframe/> n'est PAS déjà juste avant cette séquence
                            # On regarde l'élément précédent dans la liste des enfants de story_text_elem
                            if j > 0:
                                prev_elem = children_of_story[j-1]
                                if prev_elem.tag == "breakframe":
                                    # Un breakframe existe déjà, ne rien faire
                                    fist_page = False
                                    j += 1
                                    continue

                            # Pas en tout début de doc
                            if fist_page:
                                fist_page = False
                                j +=1
                                continue
                                
                            # Si pas de breakframe existant, insérer un nouveau <breakframe/>
                            # if header_text in [h[1] for h in self.headers_list]:
                            #     breaks_added = self.add_breakframes(story_text_elem, j, 2)  # 2 sauts
                            # else:
                            breaks_added = self.add_breakframes(story_text_elem, j, 1)  # 1 saut normal

                             
                            # Après l'insertion, la liste des enfants de 'story_text_elem' a changé.
                            # Nous devons la rafraîchir et ajuster l'index.
                            children_of_story = list(story_text_elem)
                            j += breaks_added # Avancer l'index pour passer l'élément breakframe nouvellement inséré
                            modified_count += breaks_added
                j += 1 # Avancer l'index pour passer à l'élément suivant dans la liste

        return modified_count

    def add_breakframes(self, story_text_elem, position, count=1):
        """Ajoute un ou plusieurs breakframes"""
        for i in range(count):
            breakframe = ET.Element("breakframe")
            story_text_elem.insert(position + i, breakframe)
        return count

    def cesures(self):
        hyphen_element = self.root.find('.//HYPHEN')

        if hyphen_element is not None:
            # Modifier les attributs pour de meilleures règles françaises
            hyphen_element.set('AUTO', '1')           # Césure automatique activée
            hyphen_element.set('LANGUAGE', 'fr')      # Langue française
            hyphen_element.set('LEFTMIN', '3')        # Min 2 caractères avant césure
            hyphen_element.set('RIGHTMIN', '3')       # Min 3 caractères après césure
            hyphen_element.set('MINWORDLEN', '7')     # Longueur min du mot : 6 caractères
            hyphen_element.set('MAXCHARS', '2')       # Max 2 césures consécutives


    def del_pages(self, start):
        total_pages = scribus.pageCount()
        for page_num in range(total_pages, start, -1):
            scribus.deletePage(page_num)
        return 0


    def del_empty_pages(self):
        total_pages = scribus.pageCount()

        # for page_num in range(total_pages, 150, -1):
        #     scribus.deletePage(page_num)
        # return 0

        
        # Supprimer pages de la fin tant qu'aucun débordement
        while total_pages > 1:
            scribus.gotoPage(total_pages)  # Avant-dernière page
            
            # Chercher un débordement
            page_items = scribus.getPageItems()
            overflow = False
            
            for item_name, item_type, _ in page_items:
                overflow = scribus.textOverflows(item_name, 0)
                scribus.messageBox("Info", f"item {item_name} type : {item_type} overflow : {overflow}")
                return 0
                if item_type == 4 and scribus.textOverflows(item_name, 0):
                    overflow = True
                    break
            
            if overflow:
                break  # Garder la dernière page
            
            # Supprimer la dernière page
            scribus.deletePage(total_pages)
            total_pages -= 1
        
        return scribus.pageCount()


    def add_pages(self, gabarit=["Normal droite", "Normal gauche"]):
        """Ajoute des pages si le texte déborde"""
        
        while self.add_one_page(gabarit):
            pass


    def add_one_page(self, gabarit=["Normal droite", "Normal gauche"]):
        
        # Trouver le dernier cadre de texte
        last_page = scribus.pageCount()
        item_name = self.get_page_frame(last_page)
    
        if not item_name:
            return False
        
        overflow = scribus.textOverflows(item_name, 1)

        # r = scribus.messageBox("Question",
        #                     f"page {last_page} overflow : {overflow}\nContinuer ?",
        #                     button1=scribus.BUTTON_YES,
        #                     button2=scribus.BUTTON_NO)
        # if r != 16384:
        #     return False
        
        if not overflow:
            return False
        
        if last_page % 2 != 0:
            # Dernière page est impaire, utiliser gabarit de droite
            new_gabarit = gabarit[1]
        else:
            # Dernière page est paire, utiliser gabarit de gauche
            new_gabarit = gabarit[0]

        scribus.newPage(-1, new_gabarit)

        return True


    def get_page_frame(self, page_num):
        scribus.gotoPage(page_num)        
        page_items = scribus.getPageItems()
        
        for item_name, item_type, _ in page_items:
            if item_type == 4:  # TextFrame
                return item_name
        
        return False


    def analyze_headers_pagination(self, styles=["h1", "h2", "h4"]):
        """Première passe : analyser quels headers ne sont pas sur des pages de droite"""
        
        message = ", ".join(self.headers_list)
        scribus.messageBox("Info", message)

        total_pages = scribus.pageCount()        
        for page_num in range(1, total_pages + 1):

            frame_name = self.get_page_frame(page_num)
            if not frame_name:
                continue

            text = scribus.getFrameText(frame_name)
            lines = text.splitlines()
            for line in lines:
                line_stripped = line.strip()
                if line_stripped:
                    for header in self.headers_list:
                        if line_stripped.startswith(header.strip()):
                            # Header trouvé sur cette page
                            if page_num % 2 == 0:  # Page de gauche
                                self.headers_to_fix.append(header)
                            break
                break
        
        message = ", ".join(self.headers_to_fix)
        scribus.messageBox("Info", message)

        return True


    def page_starts_with_header(self, frame_name, styles):
        """Vérifie si un cadre de texte commence par un header spécifique"""
        try:
            # Sélectionner le cadre
            scribus.selectObject(frame_name)
            
            # Aller au début du texte dans ce cadre
            scribus.selectText(0, 0, frame_name)
            
            # Obtenir le style du premier paragraphe
            try:
                current_style = scribus.getStyle(frame_name)
                return current_style in styles
            except:
                return False
                
        except Exception as e:
            return False

if __name__ == "__main__":

    postprod = PostProdScribus()
    postprod.opensla()
    