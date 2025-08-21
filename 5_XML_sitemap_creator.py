import pandas as pd
import xml.etree.ElementTree as ET
from datetime import datetime
import os
from urllib.parse import urlparse

def validate_url(url):
    """
    Valide qu'une URL est correctement formatée.
    
    Args:
        url (str): L'URL à valider
        
    Returns:
        bool: True si l'URL est valide, False sinon
    """
    try:
        result = urlparse(url.strip())
        return all([result.scheme, result.netloc])
    except:
        return False

def create_sitemap_from_excel(excel_file_path, output_sitemap_path='sitemap.xml'):
    """
    Génère un sitemap XML à partir d'une liste d'URLs dans un fichier Excel.

    Args:
        excel_file_path (str): Le chemin vers le fichier .xlsx.
                               Les URLs sont attendues dans la première colonne (colonne A).
        output_sitemap_path (str): Le chemin où le sitemap.xml sera sauvegardé.
    """
    print(f"📊 Lecture du fichier Excel : {excel_file_path}")
    
    try:
        # Lire les URLs depuis la première colonne du fichier Excel
        df = pd.read_excel(excel_file_path, header=None, usecols=[0])
        urls = df[0].tolist()
        print(f"✅ {len(urls)} URLs trouvées dans le fichier")
    except FileNotFoundError:
        print(f"❌ Erreur : Le fichier '{excel_file_path}' n'a pas été trouvé.")
        return False
    except Exception as e:
        print(f"❌ Erreur lors de la lecture du fichier Excel : {e}")
        return False

    # Créer l'élément racine <urlset>
    urlset_attributes = {
        "xmlns": "http://www.sitemaps.org/schemas/sitemap/0.9",
        "xmlns:xhtml": "http://www.w3.org/1999/xhtml"
    }
    urlset = ET.Element("urlset", attrib=urlset_attributes)

    # Obtenir la date actuelle pour <lastmod>
    current_date = datetime.now().astimezone().isoformat(timespec='seconds')

    valid_urls = 0
    skipped_urls = 0

    # Pour chaque URL, créer un élément <url> et ses enfants
    for url_str in urls:
        if pd.isna(url_str) or not isinstance(url_str, str):
            skipped_urls += 1
            continue
            
        url_cleaned = url_str.strip()
        
        if not validate_url(url_cleaned):
            print(f"⚠️  URL invalide ignorée : {url_str}")
            skipped_urls += 1
            continue

        url_element = ET.SubElement(urlset, "url")
        
        loc_element = ET.SubElement(url_element, "loc")
        loc_element.text = url_cleaned
        
        lastmod_element = ET.SubElement(url_element, "lastmod")
        lastmod_element.text = current_date
        
        # Optionnel : Ajouter <changefreq> et <priority>
        changefreq_element = ET.SubElement(url_element, "changefreq")
        changefreq_element.text = "weekly"
        
        priority_element = ET.SubElement(url_element, "priority")
        priority_element.text = "0.8"
        
        valid_urls += 1

    print(f"✅ {valid_urls} URLs valides ajoutées au sitemap")
    if skipped_urls > 0:
        print(f"⚠️  {skipped_urls} URLs ignorées (invalides ou vides)")

    # Créer un objet ElementTree depuis l'élément racine
    tree = ET.ElementTree(urlset)
    
    # Indentation pour un XML plus lisible
    ET.indent(tree, space="  ", level=0)

    # Écrire le XML dans un fichier
    try:
        tree.write(output_sitemap_path, encoding='utf-8', xml_declaration=True)
        file_size = os.path.getsize(output_sitemap_path)
        print(f"🎉 Sitemap généré avec succès : '{output_sitemap_path}' ({file_size} bytes)")
        return True
    except Exception as e:
        print(f"❌ Erreur lors de l'écriture du fichier sitemap : {e}")
        return False

def main():
    """
    Fonction principale avec interface utilisateur.
    """
    print("=" * 60)
    print("🗺️  GÉNÉRATEUR DE SITEMAP XML")
    print("=" * 60)
    print("Ce script génère un sitemap XML à partir d'un fichier Excel.")
    print("Les URLs doivent être dans la première colonne (A) du fichier Excel.")
    print()
    
    # Demander le chemin du fichier Excel
    while True:
        excel_path = input("📁 Entrez le chemin vers votre fichier Excel : ").strip()
        
        if not excel_path:
            print("❌ Veuillez entrer un chemin de fichier.")
            continue
            
        if not os.path.exists(excel_path):
            print(f"❌ Le fichier '{excel_path}' n'existe pas.")
            continue
            
        if not excel_path.lower().endswith(('.xlsx', '.xls')):
            print("❌ Le fichier doit être un fichier Excel (.xlsx ou .xls).")
            continue
            
        break
    
    # Demander le nom du fichier de sortie
    output_path = input("📄 Nom du fichier sitemap (par défaut: sitemap.xml) : ").strip()
    if not output_path:
        output_path = "sitemap.xml"
    
    if not output_path.endswith('.xml'):
        output_path += '.xml'
    
    print()
    print("🚀 Génération du sitemap en cours...")
    print("-" * 40)
    
    # Générer le sitemap
    success = create_sitemap_from_excel(excel_path, output_path)
    
    print("-" * 40)
    if success:
        print("✨ Génération terminée avec succès !")
        print(f"📍 Fichier créé : {os.path.abspath(output_path)}")
    else:
        print("💥 Échec de la génération du sitemap.")

if __name__ == "__main__":
    main()
