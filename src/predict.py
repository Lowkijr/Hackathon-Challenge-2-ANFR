"""
Niveau 3.B/C — Prédiction supervisée de l'obs_ratio à t+2h / t+4h / t+6h.

Approche volontairement simple pour un hackathon de quelques jours : features
de lag + heure cyclique -> RandomForestRegressor. C'est moins "sexy" qu'un
Transformer temporel (TFT) mais ça s'entraîne en secondes, s'interprète
facilement (feature_importances_), et donne une vraie baseline à battre si
l'équipe a le temps de tenter du LSTM/TFT ensuite.

Nécessite un historique multi-jours par station pour être pertinent (le
fichier QC d'exemple ne couvre qu'un jour : voir scripts/generate_sample_data.py
pour un historique synthétique de test).
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error

TARGET_COL = "obs_ratio_3"
HORIZONS_HOURS = (2, 4, 6)


def build_lagged_features(df: pd.DataFrame, station: str, target_col: str = TARGET_COL) -> pd.DataFrame:
    """Construit, pour UNE station, un tableau de features/targets par horizon.

    Suppose que `df` a une colonne `timestamp` régulière (rééchantillonnée si
    besoin) et la colonne cible `target_col`.
    """
    g = df[df["station"] == station].sort_values("timestamp").copy()
    g = g.set_index("timestamp")

    # Ré-échantillonnage à la maille horaire (moyenne) pour stabiliser le signal.
    hourly = g[[target_col]].resample("1h").mean().interpolate(limit=6)
    hourly["hour"] = hourly.index.hour
    hourly["hour_sin"] = np.sin(2 * np.pi * hourly["hour"] / 24)
    hourly["hour_cos"] = np.cos(2 * np.pi * hourly["hour"] / 24)
    hourly["dow"] = hourly.index.dayofweek

    for lag in (1, 2, 3, 6, 12, 24):
        hourly[f"lag_{lag}h"] = hourly[target_col].shift(lag)

    for h in HORIZONS_HOURS:
        hourly[f"target_t+{h}h"] = hourly[target_col].shift(-h)

    return hourly.dropna()


def train_and_evaluate(df: pd.DataFrame, station: str, horizon: int = 2):
    """Entraîne un RandomForest pour un horizon donné et retourne (modèle, métriques).

    Split temporel simple (80/20, pas de shuffle) pour rester honnête sur une
    série temporelle.
    """
    feats = build_lagged_features(df, station)
    target_col = f"target_t+{horizon}h"
    feature_cols = [c for c in feats.columns if c not in (TARGET_COL,) and not c.startswith("target_t+")]

    n = len(feats)
    split = int(n * 0.8)
    if split < 10 or n - split < 3:
        raise ValueError(
            f"Pas assez d'historique pour la station {station} "
            f"({n} points horaires) : il faut plusieurs jours de données."
        )

    X_train, X_test = feats[feature_cols].iloc[:split], feats[feature_cols].iloc[split:]
    y_train, y_test = feats[target_col].iloc[:split], feats[target_col].iloc[split:]

    model = RandomForestRegressor(n_estimators=300, max_depth=8, random_state=42)
    model.fit(X_train, y_train)
    pred = model.predict(X_test)

    metrics = {
        "station": station,
        "horizon_h": horizon,
        "mae": mean_absolute_error(y_test, pred),
        "rmse": float(np.sqrt(mean_squared_error(y_test, pred))),
        "n_train": len(X_train),
        "n_test": len(X_test),
        "feature_importances": dict(zip(feature_cols, model.feature_importances_.round(3))),
    }
    return model, metrics


if __name__ == "__main__":
    import sys

    sys.path.insert(0, ".")
    from src.parser import parse_qc_folder

    folder = sys.argv[1] if len(sys.argv) > 1 else "data/sample"
    raw = parse_qc_folder(folder)
    for station in raw["station"].unique():
        try:
            _, metrics = train_and_evaluate(raw, station, horizon=2)
            print(metrics)
        except ValueError as e:
            print(f"[{station}] {e}")
