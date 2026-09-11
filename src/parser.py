import xml.etree.ElementTree as ET
from pathlib import Path
import pandas as pd

# Dossier principal contenant les données téléchargées
DATA_DIR = Path("data")
PROCESSED_DIR = DATA_DIR / "processed"
OUTPUT_CSV = PROCESSED_DIR / "rgp_kpi_cleaned.csv"


def safe_float(val, default=0.0):
    """Convertit une valeur en float en sécurisant les tirets '-' ou None."""
    if not val or val == "-":
        return default
    try:
        return float(val)
    except ValueError:
        return default


def parse_time_to_minutes(latency_str):
    """Convertit 'HH:MM:SS' en minutes décimales."""
    if not latency_str:
        return 0.0
    try:
        parts = latency_str.split(":")
        if len(parts) == 3:
            return int(parts[0]) * 60 + int(parts[1]) + int(parts[2]) / 60.0
    except Exception:
        pass
    return 0.0


def parse_single_xml(file_path):
    """
    Parse un fichier XML de contrôle qualité RGP et extrait les indicateurs du dernier contrôle.
    """
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
    except Exception as e:
        print(f"Erreur de lecture sur {file_path.name} : {e}")
        return []

    global_date = root.attrib.get("Date", "")
    day_of_year = root.attrib.get("DayOfYear", "")
    year = root.attrib.get("Year", "")

    records = []

    for station in root.findall("station"):
        station_name = station.attrib.get("name", "UNKNOWN")

        for file_node in station.findall("file"):
            file_name = file_node.attrib.get("name", "")
            interval = file_node.attrib.get("interval", "30")
            session = file_node.attrib.get("session", "")
            error_code = int(file_node.attrib.get("error", 0))

            controls = file_node.findall("control")
            if not controls:
                continue

            # On conserve uniquement le DERNIER contrôle effectué (le plus récent)
            last_control = controls[-1]
            ctrl_date = last_control.attrib.get("date", "")

            # Extraction des statistiques de fichier (latence et taille)
            file_stats = last_control.find("file_statistics")
            latency_str = (
                file_stats.attrib.get("latency", "00:00:00")
                if file_stats is not None
                else "00:00:00"
            )
            size = (
                int(file_stats.attrib.get("size", 0))
                if file_stats is not None
                else 0
            )
            latency_min = parse_time_to_minutes(latency_str)

            # Extraction des observations et des masques d'élévation
            obs_node = last_control.find("observations")
            epochs_ratio = 0.0
            obs_ratio_3deg = 0.0
            obs_ratio_10deg = 0.0
            obs_ratio_15deg = 0.0

            if obs_node is not None:
                epochs_ratio = safe_float(
                    obs_node.attrib.get("epochs_ratio", 0.0)
                )

                for mask in obs_node.findall("mask"):
                    elev = mask.attrib.get("elevation", "")
                    ratio = safe_float(mask.attrib.get("obs_ratio", 0.0))

                    if "03" in elev or "3" in elev:
                        obs_ratio_3deg = ratio
                    elif "10" in elev:
                        obs_ratio_10deg = ratio
                    elif "15" in elev:
                        obs_ratio_15deg = ratio

            # Évaluation du statut selon les seuils du sujet
            if error_code != 0 or epochs_ratio < 50.0:
                status = "Indisponible"
            elif (
                epochs_ratio < 95.0
                or obs_ratio_3deg < 90.0
                or obs_ratio_10deg < 95.0
                or latency_min > 15
            ):
                status = "Dégradé"
            else:
                status = "Nominal"

            records.append({
                "station": station_name,
                "year": year,
                "day_of_year": day_of_year,
                "global_date": global_date,
                "control_date": ctrl_date,
                "file_name": file_name,
                "interval": interval,
                "session": session,
                "error_code": error_code,
                "latency_str": latency_str,
                "latency_min": latency_min,
                "file_size": size,
                "epochs_ratio": epochs_ratio,
                "obs_ratio_3deg": obs_ratio_3deg,
                "obs_ratio_10deg": obs_ratio_10deg,
                "obs_ratio_15deg": obs_ratio_15deg,
                "status": status,
            })

    return records


def parse_and_clean_all():
    """Parcourt l'arborescence des fichiers XML téléchargés et génère le CSV final."""
    xml_files = list(DATA_DIR.rglob("*.xml"))

    if not xml_files:
        print("Aucun fichier XML trouvé dans le dossier data/.")
        return

    print(f"Début du parsing de {len(xml_files)} fichiers XML...")

    all_records = []
    for file_path in xml_files:
        records = parse_single_xml(file_path)
        all_records.extend(records)

    if not all_records:
        print("Aucune donnée extraite.")
        return

    df = pd.DataFrame(all_records)

    # Nettoyage & typage des colonnes
    df["epochs_ratio"] = df["epochs_ratio"].round(2)
    df["obs_ratio_3deg"] = df["obs_ratio_3deg"].round(2)
    df["obs_ratio_10deg"] = df["obs_ratio_10deg"].round(2)
    df["obs_ratio_15deg"] = df["obs_ratio_15deg"].round(2)

    # Création du dossier de sortie et sauvegarde
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_CSV, index=False)

    print("\n" + "=" * 70)
    print(f"PARSING TERMINÉ : {len(df)} lignes extraites")
    print(f"Fichier sauvegardé sous : {OUTPUT_CSV}")
    print("=" * 70)

    # Aperçu du statut des stations
    print("\nRépartition des statuts :")
    print(df["status"].value_counts())


if __name__ == "__main__":
    parse_and_clean_all()