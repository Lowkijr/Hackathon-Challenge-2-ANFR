import os
import xml.etree.ElementTree as ET
import pandas as pd

def safe_float(val, default=0.0):
    """Convertit une valeur XML en float en gérant les tirets '-' ou None."""
    if not val or val == "-":
        return default
    try:
        return float(val)
    except ValueError:
        return default

def parse_time_to_minutes(latency_str):
    """Convertit 'HH:MM:SS' en minutes."""
    if not latency_str:
        return 0.0
    try:
        parts = latency_str.split(':')
        if len(parts) == 3:
            return int(parts[0]) * 60 + int(parts[1]) + int(parts[2]) / 60.0
    except Exception:
        pass
    return 0.0

def parse_qc_xml(file_path):
    """Parse le fichier XML QC du RGP et extrait les derniers contrôles de chaque fichier."""
    tree = ET.parse(file_path)
    root = tree.getroot()
    
    global_date = root.attrib.get('Date', '')
    day_of_year = root.attrib.get('DayOfYear', '')
    year = root.attrib.get('Year', '')
    
    records = []

    for station in root.findall('station'):
        station_name = station.attrib.get('name', 'UNKNOWN')
        
        for file_node in station.findall('file'):
            file_name = file_node.attrib.get('name', '')
            interval = file_node.attrib.get('interval', '30')
            session = file_node.attrib.get('session', '')
            error_code = int(file_node.attrib.get('error', 0))
            
            controls = file_node.findall('control')
            if not controls:
                continue
            
            # On conserve le DERNIER contrôle effectué (le plus récent)
            last_control = controls[-1]
            ctrl_date = last_control.attrib.get('date', '')
            
            # Statistiques du fichier
            file_stats = last_control.find('file_statistics')
            latency_str = file_stats.attrib.get('latency', '00:00:00') if file_stats is not None else '00:00:00'
            size = int(file_stats.attrib.get('size', 0)) if file_stats is not None else 0
            latency_min = parse_time_to_minutes(latency_str)
            
            # Observations
            obs_node = last_control.find('observations')
            epochs_ratio = 0.0
            obs_ratio_3deg = 0.0
            obs_ratio_10deg = 0.0
            obs_ratio_15deg = 0.0
            
            if obs_node is not None:
                epochs_ratio = safe_float(obs_node.attrib.get('epochs_ratio', 0.0))
                
                for mask in obs_node.findall('mask'):
                    elev = mask.attrib.get('elevation', '')
                    ratio = safe_float(mask.attrib.get('obs_ratio', 0.0))
                    
                    if '03' in elev or '3' in elev:
                        obs_ratio_3deg = ratio
                    elif '10' in elev:
                        obs_ratio_10deg = ratio
                    elif '15' in elev:
                        obs_ratio_15deg = ratio
            
            # Détermination du statut selon les seuils du sujet
            if error_code != 0 or epochs_ratio < 50.0:
                status = "Indisponible"
            elif epochs_ratio < 95.0 or obs_ratio_3deg < 90.0 or obs_ratio_10deg < 95.0 or latency_min > 15:
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
                "status": status
            })

    return pd.DataFrame(records)

if __name__ == "__main__":
    # Remplace par le chemin de ton fichier local téléchargé
    xml_file = "./data/raw_xml/1mel002.24.xml"
    if os.path.exists(xml_file):
        df = parse_qc_xml(xml_file)
        print("=== Extrait des données parsées ===")
        print(df[["station", "session", "epochs_ratio", "obs_ratio_3deg", "status"]].head())
    else:
        print(f"Fichier {xml_file} non trouvé.")