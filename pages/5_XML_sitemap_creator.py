import streamlit as st
import pandas as pd
import xml.etree.ElementTree as ET
from datetime import datetime
import os
from urllib.parse import urlparse
import io

st.set_page_config(
    page_title="Générateur de Sitemap XML",
    page_icon="🗺️",
    layout="wide"
)

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

def create_sitemap_from_dataframe(df, changefreq="weekly", priority="0.8"):
    """
    Génère un sitemap XML à partir d'un DataFrame pandas.

    Args:
        df (pandas.DataFrame): DataFrame contenant les URLs dans la première colonne
        changefreq (str): Fréquence de changement des pages
        priority (str): Priorité des pages
        
    Returns:
        tuple: (xml_string, valid_urls_count, skipped_urls_count)
    """
    urls = df.iloc[:, 0].tolist()
    
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
    invalid_urls = []

    # Pour chaque URL, créer un élément <url> et ses enfants
    for url_str in urls:
        if pd.isna(url_str) or not isinstance(url_str, str):
            skipped_urls += 1
            continue
            
        url_cleaned = url_str.strip()
        
        if not validate_url(url_cleaned):
            invalid_urls.append(url_str)
            skipped_urls += 1
            continue

        url_element = ET.SubElement(urlset, "url")
        
        loc_element = ET.SubElement(url_element, "loc")
        loc_element.text = url_cleaned
        
        lastmod_element = ET.SubElement(url_element, "lastmod")
        lastmod_element.text = current_date
        
        changefreq_element = ET.SubElement(url_element, "changefreq")
        changefreq_element.text = changefreq
        
        priority_element = ET.SubElement(url_element, "priority")
        priority_element.text = priority
        
        valid_urls += 1

    # Créer un objet ElementTree depuis l'élément racine
    tree = ET.ElementTree(urlset)
    
    # Indentation pour un XML plus lisible
    ET.indent(tree, space="  ", level=0)

    # Convertir en string XML
    xml_buffer = io.BytesIO()
    tree.write(xml_buffer, encoding='utf-8', xml_declaration=True)
    xml_string = xml_buffer.getvalue()
    
    return xml_string, valid_urls, skipped_urls, invalid_urls

def main():
    st.title("🗺️ Générateur de Sitemap XML")
    
    # Création des onglets
    tab1, tab2 = st.tabs(["🚀 Main", "ℹ️ About"])
    
    with tab1:
        # Upload du fichier Excel
        uploaded_file = st.file_uploader(
            "Choisissez votre fichier Excel",
            type=['xlsx', 'xls'],
            help="Le fichier doit contenir les URLs dans la première colonne"
        )
        
        # Configuration du sitemap (toujours visible)
        st.markdown("### ⚙️ Configuration du sitemap")
        col1, col2 = st.columns(2)
        
        with col1:
            changefreq = st.selectbox(
                "Fréquence de changement",
                ["always", "hourly", "daily", "weekly", "monthly", "yearly", "never"],
                index=3,  # "weekly" par défaut
                help="Indique à quelle fréquence la page est susceptible de changer"
            )
        
        with col2:
            priority = st.slider(
                "Priorité",
                min_value=0.0,
                max_value=1.0,
                value=0.8,
                step=0.1,
                help="Priorité relative de cette URL par rapport aux autres URLs de votre site"
            )
        
        if uploaded_file is not None:
            try:
                # Lire le fichier Excel
                df = pd.read_excel(uploaded_file, header=None, usecols=[0])
                
                st.success(f"✅ Fichier chargé avec succès ! {len(df)} lignes détectées.")
                
                # Afficher un aperçu des données
                st.markdown("### 👀 Aperçu des URLs")
                st.dataframe(
                    df.head(10),
                    column_config={
                        0: st.column_config.TextColumn("URLs")
                    },
                    use_container_width=True
                )
                
                if len(df) > 10:
                    st.info(f"Affichage des 10 premières URLs sur {len(df)} au total.")
                
                # Bouton de génération
                if st.button("🚀 Générer le sitemap", type="primary", use_container_width=True):
                    with st.spinner("Génération du sitemap en cours..."):
                        xml_content, valid_urls, skipped_urls, invalid_urls = create_sitemap_from_dataframe(
                            df, changefreq, str(priority)
                        )
                    
                    # Afficher les statistiques
                    st.markdown("### 📊 Résultats")
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("URLs valides", valid_urls, delta=None)
                    
                    with col2:
                        st.metric("URLs ignorées", skipped_urls, delta=None)
                    
                    with col3:
                        st.metric("Taille du fichier", f"{len(xml_content)} bytes", delta=None)
                    
                    # Afficher les URLs invalides si il y en a
                    if invalid_urls:
                        with st.expander(f"⚠️ URLs invalides ignorées ({len(invalid_urls)})"):
                            for url in invalid_urls[:20]:  # Limiter à 20 pour l'affichage
                                st.text(url)
                            if len(invalid_urls) > 20:
                                st.info(f"... et {len(invalid_urls) - 20} autres URLs invalides")
                    
                    # Bouton de téléchargement
                    st.markdown("### 📥 Téléchargement")
                    
                    filename = f"sitemap_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xml"
                    
                    st.download_button(
                        label="📥 Télécharger le sitemap XML",
                        data=xml_content,
                        file_name=filename,
                        mime="application/xml",
                        type="primary",
                        use_container_width=True
                    )
                    
                    # Aperçu du XML généré
                    with st.expander("👁️ Aperçu du XML généré"):
                        st.code(xml_content.decode('utf-8')[:2000] + "..." if len(xml_content) > 2000 else xml_content.decode('utf-8'), language="xml")
                    
                    st.success("✨ Sitemap généré avec succès !")
            
            except Exception as e:
                st.error(f"❌ Erreur lors de la lecture du fichier : {str(e)}")
        
        else:
            st.info("👆 Veuillez télécharger un fichier Excel pour commencer.")
    
    with tab2:
        st.markdown("## 📚 Guidelines et Informations")
        
        st.markdown("""
        ### 📋 Instructions
        1. **Téléchargez** votre fichier Excel (.xlsx ou .xls)
        2. **Configurez** les paramètres du sitemap (optionnel)
        3. **Générez** et téléchargez votre sitemap XML
        
        ⚠️ **Important :** Les URLs doivent être dans la première colonne (A) de votre fichier Excel.
        """)
        
        st.markdown("""
        ### 🎯 Qu'est-ce qu'un sitemap XML ?
        
        Un sitemap XML est un fichier qui liste les URLs d'un site web pour informer les moteurs de recherche 
        de la structure du site et faciliter l'indexation. Il s'agit d'un protocole standardisé qui aide Google, 
        Bing et autres moteurs de recherche à découvrir et indexer vos pages plus efficacement.
        """)
        
        st.markdown("""
        ### 📋 Format requis pour votre fichier Excel
        
        **Structure attendue :**
        - 📄 **Format :** `.xlsx` ou `.xls`
        - 📍 **Colonne A (première colonne) :** Une URL par ligne
        - ✅ **Avec en-têtes ou sans en-têtes** (peu importe)
        
        **Exemple de structure :**
        ```
        | A                           |
        |-----------------------------|
        | https://monsite.com         |
        | https://monsite.com/about   |
        | https://monsite.com/contact |
        | https://monsite.com/blog    |
        ```
        """)
        
        st.markdown("""
        ### 🔧 Éléments du sitemap XML
        
        Chaque URL dans le sitemap contient les éléments suivants :
        
        - **`<loc>`** : L'URL complète de la page (obligatoire)
        - **`<lastmod>`** : Date de dernière modification (générée automatiquement)
        - **`<changefreq>`** : Fréquence de changement estimée
        - **`<priority>`** : Priorité relative de 0.0 à 1.0
        """)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            #### 🔄 Fréquences de changement
            
            - **always** : Change à chaque visite
            - **hourly** : Change toutes les heures
            - **daily** : Change tous les jours
            - **weekly** : Change toutes les semaines *(recommandé)*
            - **monthly** : Change tous les mois
            - **yearly** : Change tous les ans
            - **never** : Ne change jamais
            """)
        
        with col2:
            st.markdown("""
            #### ⭐ Priorités recommandées
            
            - **1.0** : Page d'accueil
            - **0.8** : Pages importantes *(par défaut)*
            - **0.6** : Pages de catégories
            - **0.4** : Pages de contenu
            - **0.2** : Pages d'archives
            - **0.1** : Pages peu importantes
            """)
        
        st.markdown("""
        ### ✅ Formats d'URLs acceptés
        
        **URLs valides :**
        - ✅ `https://example.com`
        - ✅ `http://example.com/page`
        - ✅ `https://subdomain.example.com/path/to/page`
        - ✅ `https://example.com/page?param=value`
        - ✅ `https://example.com/page#section`
        
        **URLs qui seront ignorées :**
        - ❌ `example.com` (sans protocole)
        - ❌ `/page` (URL relative)
        - ❌ `www.example.com` (sans protocole)
        - ❌ Cellules vides ou invalides
        """)
        
        st.markdown("""
        ### 🚀 Utilisation du sitemap généré
        
        Une fois votre sitemap XML généré :
        
        1. **Téléchargez** le fichier XML
        2. **Uploadez-le** à la racine de votre site web
        3. **Soumettez-le** dans Google Search Console
        4. **Ajoutez** l'URL du sitemap dans votre robots.txt :
           ```
           Sitemap: https://votre-site.com/sitemap.xml
           ```
        """)
        
        st.markdown("""
        ### 📊 Limites et bonnes pratiques
        
        - **Maximum 50 000 URLs** par sitemap (limite Google)
        - **Taille maximale :** 50 MB non compressé
        - **Encodage :** UTF-8 obligatoire
        - **Mise à jour :** Régulière recommandée
        - **Validation :** Testez votre sitemap avec des outils en ligne
        """)
        
        st.info("""
        💡 **Conseil :** Utilisez ce générateur pour créer des sitemaps spécialisés 
        (par exemple : sitemap pour les articles de blog, sitemap pour les pages produits, etc.)
        """)

if __name__ == "__main__":
    main()
