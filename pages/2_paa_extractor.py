# app.py
import streamlit as st
import pandas as pd
import requests
from lxml import html
from io import BytesIO

st.set_page_config(
    layout="wide",
    page_title="PAA Extract",
    page_icon="🥝"
)

# Configuration des headers pour les requêtes
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.90 Safari/537.36',
    'Accept-Language': 'fr-FR',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9'
}

# Fonction pour lire les requêtes et les volumes depuis un fichier Excel
def lire_requetes_et_volumes(fichier):
    df = pd.read_excel(fichier)
    return df.values.tolist()

# Fonction pour envoyer une requête et analyser la réponse
def envoyer_requete_et_analyser(query):
    response = requests.get(f'https://www.google.com/search?q={query}&start=0', headers=headers).text
    tree = html.fromstring(response)
    return tree.xpath('//@data-q')

# Interface utilisateur Streamlit
st.title("People Also Ask Extractor")

# Options d'importation des données
option = st.radio("Comment souhaitez-vous importer les données?", ('Télécharger un fichier Excel', 'Copier-coller les valeurs'))

if option == 'Télécharger un fichier Excel':
    fichier = st.file_uploader("Téléchargez votre fichier Excel", type=["xlsx"])
    if fichier is not None:
        requetes_et_volumes = lire_requetes_et_volumes(fichier)
elif option == 'Copier-coller les valeurs':
    donnees = st.text_area("Collez les valeurs de requêtes et de volume ici (séparées par des virgules, une par ligne)", height=200)
    if donnees:
        requetes_et_volumes = [ligne.split(',') for ligne in donnees.strip().split('\n')]

# Analyse et traitement des requêtes
if st.button('Analyser les requêtes'):
    if 'requetes_et_volumes' in locals():
        resultats_et_infos = {}

        for requete, volume in requetes_et_volumes:
            volume = int(volume)  # Convertir le volume en entier pour les calculs
            resultats = envoyer_requete_et_analyser(requete)
            for resultat in resultats:
                if resultat not in resultats_et_infos:
                    resultats_et_infos[resultat] = {'requetes': [], 'volumes': [], 'volume_total': 0}
                resultats_et_infos[resultat]['requetes'].append(requete)
                resultats_et_infos[resultat]['volumes'].append(volume)
                resultats_et_infos[resultat]['volume_total'] += volume
        
        # Convertir les résultats en DataFrame pour affichage
        resultats_data = []
        for resultat_unique, infos in resultats_et_infos.items():
            max_volume_index = infos['volumes'].index(max(infos['volumes']))
            mot_cle_associe = infos['requetes'][max_volume_index]
            resultats_data.append({
                'Résultat Unique': resultat_unique,
                'Volume Total': infos['volume_total'],
                'Requête': ', '.join(infos['requetes']),
                'Mot clé Associé': mot_cle_associe
            })

        resultats_df = pd.DataFrame(resultats_data)

        # Réorganiser l'ordre des colonnes
        resultats_df = resultats_df[['Résultat Unique', 'Volume Total', 'Mot clé Associé', 'Requête']]
        
        st.dataframe(resultats_df)

        # Générer le fichier Excel pour téléchargement
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            resultats_df.to_excel(writer, index=False, sheet_name='Résultats')

        fichier_excel = output.getvalue()

        # Bouton pour télécharger le fichier Excel
        st.download_button(label="Télécharger les résultats en Excel", data=fichier_excel, file_name='resultats_analyse.xlsx', mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    else:
        st.error("Veuillez télécharger un fichier ou copier-coller des données avant de lancer l'analyse.")

        # Ajouter l'icône Twitter et le texte en bas à gauche
st.sidebar.markdown(
    """
    <div style="position: fixed; bottom: 10px; left: 20px;">
        <a href="https://github.com/Psimon8" target="_blank" style="text-decoration: none;">
            <img src="https://github.githubassets.com/assets/pinned-octocat-093da3e6fa40.svg" 
                 alt="GitHub Simon le Coz" style="width:20px; vertical-align: middle; margin-right: 5px;">
            <span style="color: white; font-size: 14px;"></span>
        </a>    
        <a href="https://www.linkedin.com/in/simon-le-coz/" target="_blank" style="text-decoration: none;">
            <img src="https://static.licdn.com/aero-v1/sc/h/8s162nmbcnfkg7a0k8nq9wwqo" 
                 alt="LinkedIn Simon Le Coz" style="width:20px; vertical-align: middle; margin-right: 5px;">
            <span style="color: white; font-size: 14px;"></span>
        </a>
        <a href="https://twitter.com/lekoz_simon" target="_blank" style="text-decoration: none;">
            <img src="https://abs.twimg.com/favicons/twitter.3.ico" 
                 alt="Twitter Simon Le Coz" style="width:20px; vertical-align: middle; margin-right: 5px;">
            <span style="color: white; font-size: 14px;">@lekoz_simon</span>
        </a>
    </div>
    """,
    unsafe_allow_html=True
)        