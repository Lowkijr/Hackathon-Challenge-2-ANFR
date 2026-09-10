import os
import re
import requests
from bs4 import BeautifulSoup

# Dossier local de destination
SAVE_DIR = "./data/raw_xml"

def fetch_qc_files(year="2024", doy="013", download=True):
    """
    Récupère et télécharge les fichiers QC XML depuis rgpdata.ign.fr.
    - year: Année (ex: "2024" ou "2026")
    - doy: Day of Year sur 3 chiffres (ex: "013" pour 13 janv, "094" pour 4 avril)
    - download: Si True, télécharge les fichiers sur le disque
    """
    # URL mise à jour sur rgpdata.ign.fr
    base_url = f"https://rgpdata.ign.fr/pub/data/{year}/{doy}/"
    os.makedirs(SAVE_DIR, exist_ok=True)

    print(f"Connexion au serveur : {base_url}")
    try:
        response = requests.get(base_url, timeout=15)
        if response.status_code != 200:
            print(f"Erreur {response.status_code} lors de l'accès à {base_url}")
            return []
    except Exception as e:
        print(f"Erreur de connexion : {e}")
        return []

    # Extraction des fichiers XML via Regex (Nom, Date, Heure, Taille)
    soup = BeautifulSoup(response.text, "html.parser")
    pattern = r"([a-z0-9]{4}\d{3}\.\d{2}\.xml)\s*(\d{4}-\d{2}-\d{2})\s+(\d{2}:\d{2})\s*(\d+[KMGT]?)"
    matches = re.findall(pattern, soup.get_text())

    if not matches:
        print("Aucun fichier XML trouvé.")
        return []

    print(f"-> {len(matches)} fichiers XML répertoriés pour le jour {doy}/{year}.")

    downloaded_paths = []
    if download:
        print("Début du téléchargement...")
        for idx, (filename, date_mod, time_mod, size) in enumerate(matches, 1):
            file_url = f"{base_url}{filename}"
            output_path = os.path.join(SAVE_DIR, filename)

            if not os.path.exists(output_path):
                r = requests.get(file_url, timeout=10)
                if r.status_code == 200:
                    with open(output_path, "wb") as f:
                        f.write(r.content)
                    print(f"[{idx}/{len(matches)}] Téléchargé : {filename} ({size})")
                    downloaded_paths.append(output_path)
            else:
                print(f"[{idx}/{len(matches)}] Déjà présent : {filename}")
                downloaded_paths.append(output_path)

    return downloaded_paths

if __name__ == "__main__":
    # Test d'extraction sur l'année 2024 (jour 013)
    files = fetch_qc_files(year="2024", doy="013", download=True)