import sys
from pathlib import Path

# Ajout du dossier src au path Python
sys.path.append(str(Path(__file__).parent / "src"))

from parser import parse_and_clean_all
# Importer votre fonction de téléchargement si elle est dans src/fetcher.py

def main():
    print("=" * 70)
    print("🚀 LANCEMENT DU PIPELINE GPS QUALITY INTELLIGENCE")
    print("=" * 70)

    # 1. Étape d'acquisition (Téléchargement des XML)
    print("\n[Étape 1/2] Téléchargement des données RGP...")
    # Appelez ici votre fonction de téléchargement (ex: fetch_qc_files())

    # 2. Étape de parsing et nettoyage (Génération du CSV)
    print("\n[Étape 2/2] Parsing XML et extraction des KPI...")
    parse_and_clean_all()

    print("\n✅ PIPELINE EXÉCUTÉ AVEC SUCCÈS !")

if __name__ == "__main__":
    main()