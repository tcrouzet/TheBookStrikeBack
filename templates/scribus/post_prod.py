import scribus
import os
import xml.etree.ElementTree as ET
from xml.dom import minidom
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

        self.insert_breakframes_before()

        return


    def insert_breakframes_before(self, styles=["h1", "h2", "h4"]):
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
            root = tree.getroot()

            if root is None:
                scribus.messageBox("Erreur", f"Impossible de parser le fichier SLA. La racine est vide.")
                return False

            modified_count = 0
                        
            # Trouver tous les cadres de texte
            for item_elem in root.findall(".//PAGEOBJECT[@PTYPE='4']"):
                # Trouver l'élément qui contient le flux de texte (souvent <StoryText>)
                story_text_elem = item_elem.find(".//StoryText")
                if story_text_elem is None:
                    continue

                children_of_story = list(story_text_elem) # Convertir en liste pour modifier pendant l'itération
                j = 0 # Index pour parcourir les enfants de StoryText

                while j < len(children_of_story):
                    current_elem = children_of_story[j]

                    # Cible la balise <ITEXT>
                    if current_elem.tag == "ITEXT":
                        # Vérifie l'élément suivant pour voir si c'est <para PARENT="h2"/>
                        if j + 1 < len(children_of_story):
                            next_elem = children_of_story[j+1]
                            
                            # Cible : <para PARENT="h2"/> (ou h1 si vous adaptez)
                            # Attention: assurez-vous que 'h2' correspond bien à la valeur de l'attribut PARENT dans votre XML
                            # et non au nom du style de Scribus (qui pourrait être "Heading 2" mais se traduire en "h2" dans le XML).
                            # Vérifiez votre fichier SLA directement pour la valeur exacte.
                            if next_elem.tag == "para" and next_elem.get('PARENT') in styles:
                                # Vérifie si un <breakframe/> n'est PAS déjà juste avant cette séquence
                                # On regarde l'élément précédent dans la liste des enfants de story_text_elem
                                if j > 0:
                                    prev_elem = children_of_story[j-1]
                                    if prev_elem.tag == "breakframe":
                                        # Un breakframe existe déjà, ne rien faire
                                        j += 1 # Passer à l'ITEXT actuel
                                        continue

                                # Si pas de breakframe existant, insérer un nouveau <breakframe/>
                                breakframe_elem = ET.Element("breakframe")
                                story_text_elem.insert(j, breakframe_elem) # Insérer AVANT l'ITEXT courant
                                
                                # Après l'insertion, la liste des enfants de 'story_text_elem' a changé.
                                # Nous devons la rafraîchir et ajuster l'index.
                                children_of_story = list(story_text_elem)
                                j += 1 # Avancer l'index pour passer l'élément breakframe nouvellement inséré
                                modified_count += 1
                    j += 1 # Avancer l'index pour passer à l'élément suivant dans la liste

            if modified_count == 0:
                scribus.messageBox("Erreur", "Aucune modificaytion")
            else:
                scribus.messageBox("Bilan", f"Total de {modified_count} sauts de cadre marqués pour insertion.")

            # Sauvegarder le XML modifié dans self.output
            # Utiliser minidom pour un formatage lisible du XML
            raw_xml_string = ET.tostring(root, encoding='utf-8', xml_declaration=True)
            reparsed_xml = minidom.parseString(raw_xml_string)
            
            with open(self.output, "wb") as f: # Écrire dans self.output
                f.write(reparsed_xml.toprettyxml(indent="  ", encoding="utf-8"))

            return True #

        except ET.ParseError as e:
            scribus.messageBox("Erreur d'analyse XML", f"Le fichier '{self.sla}' n'est pas un XML valide. {e}")
            return False
        except Exception as e:
            scribus.messageBox("Erreur", f)
            return False

if __name__ == "__main__":

    postprod = PostProdScribus()
    postprod.opensla()
    