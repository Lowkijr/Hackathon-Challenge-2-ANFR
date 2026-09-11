"""
Niveau 3.A — Détection d'anomalies non supervisée (Isolation Forest).

Objectif : repérer, station par station, les points de mesure qui s'écartent
du comportement habituel, sans avoir besoin d'incidents labellisés
(cf. brief : "Avantage : pas de données labelisées d'incidents requises").

C'est le point d'entrée le plus rapide à obtenir un résultat démontrable en
peu de jours ; le modèle prédictif supervisé (predict.py) vient en complément
si le temps le permet.
"""
from __future__ import annotations

import pandas as pd
from sklearn.ensemble import IsolationForest

FEATURE_COLS = ["epochs_ratio", "obs_ratio_3", "obs_ratio_10", "obs_ratio_15", "latency_s"]


def _prep_features(df: pd.DataFrame) -> pd.DataFrame:
    cols = [c for c in FEATURE_COLS if c in df.columns]
    feats = df[cols].copy()
    return feats.fillna(feats.median(numeric_only=True))


def detect_anomalies(df: pd.DataFrame, contamination: float = 0.05, random_state: int = 42) -> pd.DataFrame:
    """Ajoute deux colonnes : anomaly_score (plus bas = plus anormal, sortie
    brute d'IsolationForest.decision_function) et is_anomaly (bool).

    Le modèle est ré-entraîné par station (le comportement "normal" d'une
    station côtière n'est pas celui d'une station de montagne).
    """
    df = df.copy()
    df["anomaly_score"] = 0.0
    df["is_anomaly"] = False

    for station, group in df.groupby("station"):
        if len(group) < 20:
            # Pas assez de points pour entraîner quoi que ce soit de fiable ;
            # on retombe sur les alertes à seuil fixe (scoring.py) pour ces stations.
            continue
        feats = _prep_features(group)
        if feats.empty or feats.shape[1] == 0:
            continue

        model = IsolationForest(
            n_estimators=200,
            contamination=contamination,
            random_state=random_state,
        )
        model.fit(feats)
        scores = model.decision_function(feats)
        preds = model.predict(feats)  # -1 = anomalie, 1 = normal

        df.loc[group.index, "anomaly_score"] = scores
        df.loc[group.index, "is_anomaly"] = preds == -1

    return df


if __name__ == "__main__":
    import sys

    sys.path.insert(0, ".")
    from src.parser import parse_qc_folder
    from src.scoring import add_score_and_status

    folder = sys.argv[1] if len(sys.argv) > 1 else "data/sample"
    raw = parse_qc_folder(folder)
    scored = add_score_and_status(raw)
    flagged = detect_anomalies(scored)
    print(flagged[flagged["is_anomaly"]][["station", "timestamp", "score", "status", "anomaly_score"]])
