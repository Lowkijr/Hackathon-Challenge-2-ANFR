Voici le bloc de texte au format Markdown exact. Tu peux le copier et le coller directement dans ton fichier `README.md` sur VS Code.

```markdown
# Hackathon-Challenge-2-ANFR

> **Challenge 2 : GPS Quality Intelligence** — Tableau de bord et prédiction IA des indisponibilités GNSS pour le réseau RGP (IGN / ANFR / ISEP - FR Hack 2026).

---

## 📌 Présentation du Projet

Le réseau **RGP (Réseau GNSS Permanent)** de l'IGN est l'infrastructure française de référence pour la géodésie de haute précision. Avec plus de 300 stations sur le territoire national et les DOM-TOM, il reçoit en continu les signaux des constellations satellite GPS, Galileo, GLONASS et BeiDou[cite: 1].

Ce projet vise à automatiser l'analyse de la qualité de réception GNSS en temps quasi-réel, générer une carte interactive de qualité de service et déployer un modèle prédictif d'IA capable d'anticiper les dégradations réseau (2h à 6h à l'avance)[cite: 1].

---

## 📂 Structure du Projet

```text
Hackathon-Challenge-2-ANFR/
│
├── data/
│   ├── raw_xml/        # Fichiers QC XML téléchargés depuis rgpdata.ign.fr
│   └── processed/      # CSV / Parquet structurés après extraction des KPI
├── src/
│   ├── fetcher.py      # Module d'ingestion et scraping depuis rgpdata.ign.fr
│   ├── parser.py       # Module de parsing XML et extraction des KPI
│   └── dashboard.py    # Interface web / Dashboard de supervision
├── requirements.txt    # Liste des dépendances Python
└── README.md           # Documentation du projet

```

---

## 🚀 Installation & Configuration

### 1. Cloner le dépôt Git

```bash
git clone <URL_DU_DEPOT>
cd Hackathon-Challenge-2-ANFR

```

### 2. Créer un environnement virtuel (recommandé)

```bash
python -m venv venv
# Sur Linux / macOS :
source venv/bin/activate
# Sur Windows :
.\venv\Scripts\activate

```

### 3. Installer les dépendances

```bash
pip install -r requirements.txt

```

---

## ⚙️ Utilisation

### Étape 1 : Récupérer les données QC XML (`fetcher.py`)

Télécharge automatiquement les fichiers XML de contrôle qualité depuis le serveur officiel `rgpdata.ign.fr` pour une année et un jour de l'année (DOY) donnés :

```bash
python src/fetcher.py

```

### Étape 2 : Parser les fichiers et extraire les KPI (`parser.py`)

Lit les fichiers XML bruts, extrait les indicateurs clés et enregistre le résultat nettoyé sous `./data/processed/kpi_extracted.csv` :

```bash
python src/parser.py

```

---

## 📊 Indicateurs Clés de Performance (KPI) Extraits

| Indicateur | Description | Seuil d'Alerte |
| --- | --- | --- |
| **`epochs_ratio`** | % d'époques reçues sur le total attendu | `< 95%` |
| **`obs_ratio (3°)`** | % d'observations reçues avec masque d'élévation $\ge 3^\circ$ | `< 90%` |
| **`obs_ratio (10°)`** | % d'observations reçues avec masque d'élévation $\ge 10^\circ$ | `< 95%` |
| **`latency`** | Délai de livraison du fichier XML | `> 15 min` |
| **`error`** | Code d'erreur lors de la génération du fichier | `!= 0` |
| **`size`** | Taille du fichier XML de contrôle | Chute brutale |

---

## 🛠 Tech Stack

* **Langage :** Python 3.10+
* **Ingestion & Scraping :** `requests`, `beautifulsoup4`, `lxml`
* **Traitement de données :** `pandas`, `numpy`
* **Source de données :** [rgpdata.ign.fr](https://rgpdata.ign.fr/)

---

## 📝 Licence

Projet développé dans le cadre du **FR Hack 2026** (ANFR × ISEP).

```

```
