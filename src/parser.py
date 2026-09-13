import re
import xml.etree.ElementTree as ET
from pathlib import Path
import pandas as pd

def parse_time_to_minutes(latency_str: str) -> float:
    """Gère 'HH:MM:SS' et 'X day(s) HH:MM:SS'."""
    if not latency_str:
        return 0.0
    try:
        days = 0
        if "day" in latency_str:
            match = re.search(r"(\d+)\s*day\(s\)\s*(.*)", latency_str)
            if match:
                days = int(match.group(1))
                latency_str = match.group(2)
        
        parts = latency_str.split(":")
        if len(parts) == 3:
            hours, minutes, seconds = map(float, parts)
            return days * 1440 + hours * 60 + minutes + seconds / 60.0
    except Exception:
        pass
    return 0.0

def parse_single_xml(file_path: Path) -> list[dict]:
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
    except Exception:
        return []

    records = []
    for station in root.findall("station"):
        station_name = station.attrib.get("name", "UNKNOWN")

        for file_node in station.findall("file"):
            file_name = file_node.attrib.get("name", "")
            interval = int(file_node.attrib.get("interval", 30))
            session = file_node.attrib.get("session", "")
            error_code = int(file_node.attrib.get("error", 0))

            controls = file_node.findall("control")
            if not controls:
                continue

            # On prend le contrôle initial (index 0) pour la latence temps réel
            # ou le dernier (index -1) pour les métriques consolidées
            last_control = controls[-1]
            first_control = controls[0]

            file_stats = last_control.find("file_statistics")
            first_stats = first_control.find("file_statistics")

            latency_str = first_stats.attrib.get("latency", "00:00:00") if first_stats is not None else "00:00:00"
            latency_min = parse_time_to_minutes(latency_str)

            obs_node = last_control.find("observations")
            if obs_node is None:
                continue

            epoch_first_str = obs_node.attrib.get("epoch_first", "")
            timestamp = pd.to_datetime(epoch_first_str, errors="coerce")

            epochs_ratio = float(obs_node.attrib.get("epochs_ratio", 0.0))
            obs_ratios = {"obs_ratio_3": 0.0, "obs_ratio_10": 0.0, "obs_ratio_15": 0.0}

            for mask in obs_node.findall("mask"):
                elev = mask.attrib.get("elevation", "")
                ratio_val = mask.attrib.get("obs_ratio", "0.0")
                ratio = 0.0 if ratio_val == "-" else float(ratio_val)

                if "03" in elev or "3" in elev:
                    obs_ratios["obs_ratio_3"] = ratio
                elif "10" in elev:
                    obs_ratios["obs_ratio_10"] = ratio
                elif "15" in elev:
                    obs_ratios["obs_ratio_15"] = ratio

            records.append({
                "station": station_name,
                "timestamp": timestamp,
                "session": session,
                "interval": interval,
                "file_name": file_name,
                "error_code": error_code,
                "latency_s": latency_min * 60,
                "epochs_ratio": epochs_ratio,
                **obs_ratios
            })

    return records