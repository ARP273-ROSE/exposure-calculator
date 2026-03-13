#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Calcul de Temps d'Exposition Unitaire Ideal  ©Benoit_SAINTOT
Ideal Sub-Exposure Time Calculator
Cross-platform, auto-install, auto-language.
"""

__version__ = "2.0.1"
__author__ = "©Benoit_SAINTOT — GUI by NGC4565"

import subprocess, sys, importlib, os, math, locale, platform, webbrowser, json, threading, re, traceback
from datetime import datetime
from pathlib import Path

def _resource_path(filename):
    """Return absolute path to resource — works for dev and PyInstaller bundle."""
    if getattr(sys, '_MEIPASS', None):
        return os.path.join(sys._MEIPASS, filename)
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)

# === APP DIRECTORY (store data alongside the script, not in home) ===
_APP_DIR = Path(__file__).resolve().parent

# === ERROR LOGGING ===
_LOG_PATH = _APP_DIR / ".exposure_calc_errors.log"
_LOG_MAX_BYTES = 512_000  # 500 KB

def _log_error(exc_type=None, exc_value=None, exc_tb=None):
    try:
        if exc_type is None:
            exc_type, exc_value, exc_tb = sys.exc_info()
        if exc_type is None:
            return
        tb_text = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
        entry = (
            f"[{datetime.now().isoformat(timespec='seconds')}] "
            f"v{__version__} | {platform.system()} {platform.release()} | "
            f"Python {sys.version.split()[0]}\n{tb_text}\n"
        )
        if _LOG_PATH.exists() and _LOG_PATH.stat().st_size > _LOG_MAX_BYTES:
            lines = _LOG_PATH.read_text(encoding="utf-8", errors="replace").splitlines(True)
            half = len(lines) // 2
            _LOG_PATH.write_text("".join(lines[half:]), encoding="utf-8")
        with open(_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(entry)
    except Exception:
        pass

def _excepthook(exc_type, exc_value, exc_tb):
    _log_error(exc_type, exc_value, exc_tb)
    sys.__excepthook__(exc_type, exc_value, exc_tb)

sys.excepthook = _excepthook

def _get_last_error():
    try:
        if not _LOG_PATH.exists():
            return None
        text = _LOG_PATH.read_text(encoding="utf-8", errors="replace")
        blocks = text.strip().split("\n\n")
        return blocks[-1].strip() if blocks else None
    except Exception:
        return None

# === SETTINGS PERSISTENCE ===
_SETTINGS_PATH = _APP_DIR / ".exposure_calc_settings.json"

def _load_settings():
    try:
        if _SETTINGS_PATH.exists():
            return json.loads(_SETTINGS_PATH.read_text(encoding="utf-8"))
    except Exception:
        pass
    return None

def _save_settings_to_file(data):
    try:
        tmp = _SETTINGS_PATH.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        tmp.replace(_SETTINGS_PATH)
    except Exception:
        pass

def _ensure_package(pip_name, import_name=None):
    import_name = import_name or pip_name
    try:
        importlib.import_module(import_name)
    except ImportError:
        print(f"[setup] Installing {pip_name}...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "--quiet", pip_name],
                                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "--quiet",
                                   "--break-system-packages", pip_name],
                                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        importlib.invalidate_caches()

_ensure_package("PyQt6")
_ensure_package("matplotlib")

import matplotlib
matplotlib.use("QtAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QTabWidget, QLabel, QLineEdit, QPushButton, QComboBox, QFrame, QScrollArea,
    QGroupBox, QFileDialog, QMessageBox, QSizePolicy, QSpacerItem
)
from PyQt6.QtCore import Qt, QTimer, QUrl
from PyQt6.QtGui import QFont, QIcon, QDesktopServices


def _detect_language():
    try:
        lc = locale.getlocale()[0] or ""
    except Exception:
        lc = ""
    if not lc:
        lc = os.environ.get("LANG", os.environ.get("LANGUAGE", "")) or ""
    return "fr" if lc and str(lc).lower().startswith("fr") else "en"


# === SENSOR DATABASE ===
_SENSORS = {
    "IMX571": {"bits":16, "gains":{"Gain 0":{"rn":3.25,"ge":0.75,"offset":40,"fw":50000},"Gain 100 (HCG)":{"rn":1.4,"ge":0.21,"offset":40,"fw":15000}}, "temps":{0:0.002,-5:0.00125,-10:0.00075,-15:0.00037,-20:0.00012,-25:0.00012},
        "cameras":{"ZWO":["ASI2600MM Pro","ASI2600MC Pro"],"QHY":["QHY268M","QHY268C"],"Moravian":["C3-26000"],"Player One":["Poseidon-M Pro","Poseidon-C Pro"],"ToupTek":["ATR2600M","ATR2600C"],"ATIK":["Horizon II"]}},
    "IMX455": {"bits":16, "gains":{"Gain 0":{"rn":3.5,"ge":0.78,"offset":50,"fw":51400},"Gain 100 (HCG)":{"rn":1.2,"ge":0.25,"offset":50,"fw":21000}}, "temps":{0:0.0017,-5:0.001,-10:0.0006,-15:0.0003,-20:0.00015,-25:0.00008},
        "cameras":{"ZWO":["ASI6200MM Pro","ASI6200MC Pro"],"QHY":["QHY600M","QHY600C"],"Moravian":["C3-61000"],"Player One":["Poseidon-M FF Pro"],"ToupTek":["ATR6200M"]}},
    "IMX533": {"bits":14, "gains":{"Gain 0":{"rn":3.1,"ge":3.1,"offset":5,"fw":50000},"Gain 100 (HCG)":{"rn":1.0,"ge":0.8,"offset":5,"fw":13000}}, "temps":{0:0.0008,-5:0.0004,-10:0.0002,-15:0.0001,-20:0.00005,-25:0.00003},
        "cameras":{"ZWO":["ASI533MM Pro","ASI533MC Pro"],"QHY":["QHY533M","QHY533C"],"Player One":["Ares-M Pro","Ares-C Pro"],"ToupTek":["ATR533M","ATR533C"]}},
    "IMX294": {"bits":14, "gains":{"Gain 0":{"rn":3.6,"ge":3.5,"offset":10,"fw":66400},"Gain 120 (HCG)":{"rn":1.2,"ge":0.9,"offset":10,"fw":17000}}, "temps":{0:0.01,-5:0.006,-10:0.004,-15:0.003,-20:0.0022,-25:0.0015},
        "cameras":{"ZWO":["ASI294MM Pro","ASI294MC Pro"],"QHY":["QHY294M","QHY294C"],"Player One":["Artemis-M Pro","Artemis-C Pro"]}},
    "IMX183": {"bits":12, "gains":{"Gain 0":{"rn":3.0,"ge":3.6,"offset":10,"fw":15000},"Gain 120":{"rn":2.2,"ge":1.0,"offset":10,"fw":4500}}, "temps":{0:0.007,-5:0.0042,-10:0.0035,-15:0.00298,-20:0.00298,-25:0.00298},
        "cameras":{"ZWO":["ASI183MM Pro","ASI183MC Pro"],"QHY":["QHY183M","QHY183C"]}},
    "MN34230": {"bits":12, "gains":{"Gain 0":{"rn":3.6,"ge":5.0,"offset":50,"fw":10000},"Gain 76 (Unity)":{"rn":2.5,"ge":1.65,"offset":50,"fw":6000},"Gain 139 (HCG)":{"rn":1.7,"ge":1.0,"offset":50,"fw":4000}}, "temps":{0:0.03125,-5:0.018,-10:0.0136,-15:0.009,-20:0.0062,-25:0.0062},
        "cameras":{"ZWO":["ASI1600MM Pro","ASI1600MC Pro"],"QHY":["QHY163M","QHY163C"]}},
    "IMX585": {"bits":12, "gains":{"Gain 0":{"rn":3.3,"ge":2.7,"offset":10,"fw":40000},"Gain 250":{"rn":0.8,"ge":0.12,"offset":10,"fw":5000}}, "temps":{0:0.015,-5:0.009,-10:0.005,-15:0.003,-20:0.002,-25:0.001},
        "cameras":{"ZWO":["ASI585MC"],"QHY":["QHY5III585C"],"Player One":["Neptune-C II"],"ToupTek":["ATR585MC"]}},
    "IMX174": {"bits":12, "gains":{"Gain 0":{"rn":5.7,"ge":2.58,"offset":10,"fw":32400}}, "temps":{0:0.04,-5:0.025,-10:0.015,-15:0.01,-20:0.007,-25:0.005},
        "cameras":{"ZWO":["ASI174MM","ASI174MC"]}},
    "IMX224": {"bits":12, "gains":{"Gain 0":{"rn":6.7,"ge":3.85,"offset":10,"fw":63700}}, "temps":{0:0.05,-5:0.03,-10:0.018,-15:0.011,-20:0.007,-25:0.005},
        "cameras":{"ZWO":["ASI224MC"]}},
    "AR0130": {"bits":12, "gains":{"Gain 0":{"rn":6.0,"ge":3.3,"offset":10,"fw":20000}}, "temps":{0:0.05,-5:0.03,-10:0.02,-15:0.012,-20:0.008,-25:0.005},
        "cameras":{"ZWO":["ASI120MM","ASI120MC"]}},
    "IMX290": {"bits":12, "gains":{"Gain 0":{"rn":3.3,"ge":2.12,"offset":10,"fw":14600}}, "temps":{0:0.03,-5:0.018,-10:0.011,-15:0.007,-20:0.004,-25:0.003},
        "cameras":{"ZWO":["ASI290MM","ASI290MC"],"QHY":["QHY290M","QHY290C"]}},
    "IMX461": {"bits":16, "gains":{"Gain 0":{"rn":3.6,"ge":0.78,"offset":50,"fw":51000},"Gain 100 (HCG)":{"rn":1.4,"ge":0.25,"offset":50,"fw":20000}}, "temps":{0:0.002,-5:0.0012,-10:0.0007,-15:0.0004,-20:0.0002,-25:0.0001},
        "cameras":{"QHY":["QHY461M","QHY411"],"Moravian":["C3-100000"]}},
    "IMX071": {"bits":14, "gains":{"Gain 0":{"rn":3.3,"ge":3.2,"offset":10,"fw":50000},"Gain 90":{"rn":2.5,"ge":0.8,"offset":10,"fw":12000}}, "temps":{0:0.015,-5:0.01,-10:0.006,-15:0.004,-20:0.003,-25:0.002},
        "cameras":{"ZWO":["ASI071MC Pro"]}},
    "ICX825": {"bits":16, "gains":{"Unique":{"rn":5.0,"ge":0.27,"offset":10,"fw":18000}}, "temps":{-10:0.0005},
        "cameras":{"ATIK":["One 6.0","Infinity"]}},
    "IMX410": {"bits":16, "gains":{"Gain 0":{"rn":3.4,"ge":0.93,"offset":50,"fw":75000},"Gain 100 (HCG)":{"rn":1.3,"ge":0.28,"offset":50,"fw":22000}}, "temps":{0:0.003,-5:0.002,-10:0.001,-15:0.0006,-20:0.0003,-25:0.00015},
        "cameras":{"ZWO":["ASI2400MC Pro"]}},
    "IMX678": {"bits":12, "gains":{"Gain 0":{"rn":3.2,"ge":4.5,"offset":10,"fw":18000},"Gain 200":{"rn":0.7,"ge":0.15,"offset":10,"fw":3000}}, "temps":{0:0.01,-5:0.006,-10:0.004,-15:0.002,-20:0.001,-25:0.0006},
        "cameras":{"ZWO":["ASI678MC"],"Player One":["Uranus-C Pro"]}},
}

def _build_camera_db():
    db = {}
    for sn, s in _SENSORS.items():
        for brand, models in s["cameras"].items():
            if brand not in db:
                db[brand] = {}
            for m in models:
                db[brand][f"{m}  [{sn}]"] = {"sensor": sn, "gains": s["gains"], "temps": s["temps"], "bits": s["bits"]}
    return {b: dict(sorted(db[b].items())) for b in sorted(db.keys())}

CAMERA_DB = _build_camera_db()

# === TRANSLATIONS ===
T = {}
def _init_translations():
    global T
    T = {
        "win_title": {"fr": "Calculateur de Temps d'Exposition — ©Benoit_SAINTOT", "en": "Exposure Time Calculator — ©Benoit_SAINTOT"},
        "lang_btn": {"fr": "English", "en": "Francais"}, "recalc": {"fr": "Recalculer", "en": "Recalculate"},
        "export": {"fr": "Exporter", "en": "Export"}, "import": {"fr": "Importer", "en": "Import"},
        "import_ok": {"fr": "Reglages importes avec succes !", "en": "Settings imported successfully!"},
        "import_err": {"fr": "Fichier invalide ou incompatible.", "en": "Invalid or incompatible file."},
        "fill_yellow": {"fr": "Remplir uniquement les cases jaunes — resultats automatiques", "en": "Fill only yellow fields — results update automatically"},
        "tab_params": {"fr": "Parametres", "en": "Parameters"}, "tab_a1": {"fr": "Swamp Factor", "en": "Swamp Factor"},
        "tab_a2": {"fr": "Temps Optimal", "en": "Optimal Time"}, "tab_compare": {"fr": "Comparaison", "en": "Comparison"},
        "tab_charts": {"fr": "Graphiques", "en": "Charts"}, "tab_tables": {"fr": "Tables", "en": "Tables"}, "tab_help": {"fr": "Aide", "en": "Help"},
        "sec_sky": {"fr": "Niveaux de fond de ciel (e-/pixel/s)", "en": "Sky background levels (e-/pixel/s)"},
        "sky_link": {"fr": "Obtenir via SharpCap : https://tools.sharpcap.co.uk/", "en": "Obtain via SharpCap: https://tools.sharpcap.co.uk/"},
        "lbl_L": {"fr": "Luminance (L)", "en": "Luminance (L)"}, "lbl_RGB": {"fr": "R, G, B", "en": "R, G, B"},
        "lbl_NB12": {"fr": "Narrowband 12 nm", "en": "Narrowband 12 nm"}, "lbl_NB7": {"fr": "Narrowband 7 nm", "en": "Narrowband 7 nm"},
        "lbl_NB3": {"fr": "Narrowband 3 nm (= NB12/4, auto)", "en": "Narrowband 3 nm (= NB12/4, auto)"},
        "warn_qe": {"fr": "Prendre la Qe max dans la plage lineaire, pas la Qe max absolue.", "en": "Use max Qe in linear range, not absolute max Qe."},
        "sec_sensor": {"fr": "Parametres du capteur", "en": "Sensor parameters"},
        "lbl_rn": {"fr": "Read Noise (e- rms)", "en": "Read Noise (e- rms)"}, "lbl_ge": {"fr": "Gain (e-/ADU)", "en": "Gain (e-/ADU)"},
        "lbl_dc": {"fr": "Dark Current (e-/s/px)", "en": "Dark Current (e-/s/px)"}, "lbl_bits": {"fr": "Bits", "en": "Bits"},
        "lbl_offset": {"fr": "Offset (ADU)", "en": "Offset (ADU)"},
        "tip_rn": {"fr": "Depend du gain choisi", "en": "Depends on chosen gain"},
        "tip_ge": {"fr": "e-/ADU, pas le gain commercial", "en": "e-/ADU, not commercial gain"},
        "tip_dc": {"fr": "Depend de la temperature", "en": "Depends on cooling temp."},
        "sec_cam": {"fr": "Base de donnees cameras — remplissage auto", "en": "Camera database — auto-fill"},
        "lbl_brand": {"fr": "Marque", "en": "Brand"}, "lbl_model": {"fr": "Modele", "en": "Model"},
        "lbl_gain": {"fr": "Gain", "en": "Gain"}, "lbl_temp": {"fr": "T refroid.", "en": "Cool. temp."},
        "btn_apply": {"fr": "Appliquer", "en": "Apply"},
        "cam_count": {"fr": "{n} cameras ({s} capteurs)", "en": "{n} cameras ({s} sensors)"},
        "a1_title": {"fr": "1ere Approche — Swamp Factor", "en": "1st Approach — Swamp Factor"},
        "a1_explain": {"fr": "Le Swamp Factor (SF) est le rapport signal fond de ciel / bruit de lecture. Viser entre 3 et 10.",
                       "en": "The Swamp Factor (SF) is sky background signal / read noise ratio. Aim for 3 to 10."},
        "lbl_sf": {"fr": "Swamp Factor souhaite", "en": "Desired Swamp Factor"}, "sf_range": {"fr": "Min 3 — Max 10", "en": "Min 3 — Max 10"},
        "lbl_median": {"fr": "Valeur mediane de fond de ciel visee (ADU) :", "en": "Target sky background median (ADU):"},
        "tip_median1": {"fr": "Sur une brute, selectionner une zone de ciel sans signal et verifier la valeur mediane (Process Statistics dans PixInsight).",
                        "en": "On a raw frame, select sky area without signal and check median (Process Statistics in PixInsight)."},
        "tip_median2": {"fr": "Comparer a la cible et ajuster le temps de pose.", "en": "Compare to target and adjust exposure time."},
        "a2_title": {"fr": "2e Approche — Temps de pose optimal", "en": "2nd Approach — Optimal exposure time"},
        "a2_explain": {"fr": "On accepte un leger surcout en bruit par rapport a une pose unique infiniment longue.",
                       "en": "Accept small additional noise cost vs infinitely long single exposure."},
        "lbl_noise_pct": {"fr": "Bruit supplementaire accepte (%)", "en": "Accepted additional noise (%)"},
        "lbl_c": {"fr": "Facteur C", "en": "C Factor"},
        "lbl_examples": {"fr": "Exemples: 1%->C~50 | 2%->C~25 | 5%->C~10 | 10%->C~4", "en": "Examples: 1%->C~50 | 2%->C~25 | 5%->C~10 | 10%->C~4"},
        "sec_opti": {"fr": "Temps de pose unitaire conseille", "en": "Recommended sub-exposure time"},
        "col_filter": {"fr": "Filtre", "en": "Filter"}, "col_sec": {"fr": "Secondes", "en": "Seconds"}, "col_mmss": {"fr": "mm:ss", "en": "mm:ss"},
        "tip_opti": {"fr": "Si mediane FDC entre SF x3 et SF x10 = zone optimale.\nSi mediane < SF x3 = augmenter le temps.\nSi mediane trop elevee = possible de reduire.",
                     "en": "If FDC median between SF x3 and SF x10 = optimal zone.\nIf median < SF x3 = increase time.\nIf median too high = can reduce."},
        "sec_gain_long": {"fr": "Bruit additionnel pour un temps donne", "en": "Additional noise for a given exposure time"},
        "cmp_title_L": {"fr": "Comparaison 2 strategies en L", "en": "Compare 2 strategies in L"},
        "cmp_title_RGB": {"fr": "Comparaison 2 strategies en RGB", "en": "Compare 2 strategies in RGB"},
        "lbl_strat1": {"fr": "Strategie 1 (s)", "en": "Strategy 1 (s)"}, "lbl_strat2": {"fr": "Strategie 2 (s)", "en": "Strategy 2 (s)"},
        "lbl_noise": {"fr": "Bruit add.", "en": "Add. noise"}, "lbl_delta": {"fr": "Delta RSB :", "en": "Delta SNR:"},
        "ch1_title": {"fr": "Bruit additionnel L / RGB", "en": "Additional noise L / RGB"},
        "ch2_title": {"fr": "Bruit additionnel Narrowband", "en": "Additional noise Narrowband"},
        "ch_x": {"fr": "Temps de pose (s)", "en": "Exposure time (s)"}, "ch_y": {"fr": "Bruit additionnel (%)", "en": "Additional noise (%)"},
        "ch_thresh": {"fr": "Seuil accepte", "en": "Accepted threshold"},
        "tbl_lrgb": {"fr": "Table — L / RGB", "en": "Table — L / RGB"}, "tbl_nb": {"fr": "Table — Narrowband", "en": "Table — Narrowband"},
        "tbl_exp": {"fr": "Temps (s)", "en": "Time (s)"}, "tbl_thresh": {"fr": "Seuil", "en": "Threshold"},
        "help_title": {"fr": "Aide — Theorie et mode d'emploi", "en": "Help — Theory and user guide"},
        "btn_bug": {"fr": "Signaler un bug", "en": "Report a bug"},
        "bug_no_errors": {"fr": "Aucune erreur enregistree. Si vous rencontrez un probleme, decrivez-le dans le rapport qui va s'ouvrir.",
                          "en": "No errors logged. If you have an issue, describe it in the report that will open."},
        "update_available": {"fr": "Mise a jour disponible", "en": "Update available"},
        "update_restart": {"fr": "La version {v} a ete installee. Redemarrez l'application pour en profiter.",
                           "en": "Version {v} has been installed. Restart the application to use it."},
        "update_manual": {"fr": "La version {v} est disponible.\nTelechargez-la depuis :\n{url}",
                          "en": "Version {v} is available.\nDownload it from:\n{url}"},
    }

_init_translations()

def tr(key, lang):
    return T.get(key, {}).get(lang, key)


# === HELP TEXTS ===
HELP_FR = """CALCULATEUR DE TEMPS D'EXPOSITION — AIDE COMPLETE  (c)Benoit_SAINTOT
=====================================================================

I. THEORIE
----------

SOURCES DE BRUIT:
  Chaque pixel contient: signal utile + fond de ciel + bruit de lecture
  (Read Noise) + courant d'obscurite (Dark Current) + bruit de photon.

  Bruit total: sigma = sqrt(RN^2 + DC*t + Sky*t)
  RSB a l'empilement de N poses: RSB = Signal * sqrt(N) / sigma

SWAMP FACTOR (SF):
  SF = (Sky * t) / RN^2
  SF < 3: bruit de lecture dominant -> augmenter le temps
  3 <= SF <= 10: zone optimale
  SF > 10: pas de gain supplementaire

  Mediane cible (ADU): INT(SF * RN^2 / Gain_eADU + Offset) * 2^16 / 2^Bits

BRUIT ADDITIONNEL (2e approche):
  Bruit_add = sqrt((T*Sky/RN^2 + 1) / (T*Sky/RN^2)) - 1
  Facteur C = 1 / ((1 + %bruit/100)^2 - 1)
  T_optimal = ceil(C * RN^2 / Sky)

  1% -> C~50 | 2% -> C~25 | 5% -> C~10 | 10% -> C~4

COMBINER LES 2 APPROCHES:
  1. Calculer T_optimal (approche 2)
  2. Verifier que SF est entre 3 et 10
  3. Si SF < 3 -> augmenter | Si SF > 10 -> reduire

II. MODE D'EMPLOI
-----------------
  PARAMETRES: Entrer fond de ciel (SharpCap) + parametres capteur,
              ou utiliser la base cameras (40+ modeles: ZWO, QHY,
              Moravian, ATIK, Player One, ToupTek).
  SWAMP FACTOR: Choisir SF 3-10, lire medianes cibles.
  TEMPS OPTIMAL: Choisir % bruit, lire temps conseilles par filtre.
  COMPARAISON: Comparer 2 strategies en L et RGB.
  GRAPHIQUES: Courbes bruit vs temps de pose.
  TABLES: Tableaux complets (vert = sous seuil).

III. MISE A JOUR AUTOMATIQUE
-----------------------------
  L'application se met a jour automatiquement :

  VIA LES LANCEURS (run.bat / run.sh):
    A chaque lancement, le script execute silencieusement
    git fetch + git pull pour recuperer la derniere version.
    Necessite git installe et un clone du depot (pas un zip).

  VIA PYTHON (fallback):
    Si vous lancez directement ExposureCalculator.py, un thread
    verifie en arriere-plan si une nouvelle version existe sur
    GitHub. Si oui :
    - Avec git : mise a jour automatique, message de redemarrage.
    - Sans git : lien de telechargement affiche.
    En cas d'absence d'internet, l'application demarre normalement.

IV. SIGNALEMENT DE BUGS
-------------------------
  AUTOMATIQUE:
    Toute erreur non geree est enregistree dans le fichier :
      .exposure_calc_errors.log (dans le dossier du programme)
    Format : date, version, OS, Python, traceback complet.
    Le fichier est automatiquement tronque au-dela de 500 Ko.

  MANUEL:
    Cliquer sur le bouton rouge "Signaler un bug" dans la barre
    de boutons. Un rapport pre-rempli s'ouvre sur GitHub Issues
    avec l'environnement et la derniere erreur enregistree.
    Il suffit de decrire le probleme et de valider.

V. SAUVEGARDE DES REGLAGES
----------------------------
  AUTOMATIQUE:
    Tous les parametres sont sauvegardes automatiquement dans :
      .exposure_calc_settings.json (dans le dossier du programme)
    Au prochain lancement, les reglages sont restaures.

  EXPORT / IMPORT:
    Exporter : sauvegarde parametres + resultats dans un fichier JSON.
    Importer : charge les parametres depuis un fichier JSON exporte.
"""

HELP_EN = """EXPOSURE TIME CALCULATOR — COMPLETE HELP  (c)Benoit_SAINTOT
=============================================================

I. THEORY
---------

NOISE SOURCES:
  Each pixel contains: useful signal + sky background + read noise
  + dark current + photon noise.

  Total noise: sigma = sqrt(RN^2 + DC*t + Sky*t)
  SNR when stacking N subs: SNR = Signal * sqrt(N) / sigma

SWAMP FACTOR (SF):
  SF = (Sky * t) / RN^2
  SF < 3: read noise dominates -> increase exposure time
  3 <= SF <= 10: optimal zone
  SF > 10: no further gain

  Target median (ADU): INT(SF * RN^2 / Gain_eADU + Offset) * 2^16 / 2^Bits

ADDITIONAL NOISE (2nd approach):
  Add_noise = sqrt((T*Sky/RN^2 + 1) / (T*Sky/RN^2)) - 1
  C factor = 1 / ((1 + %noise/100)^2 - 1)
  T_optimal = ceil(C * RN^2 / Sky)

  1% -> C~50 | 2% -> C~25 | 5% -> C~10 | 10% -> C~4

COMBINING BOTH APPROACHES:
  1. Compute T_optimal (approach 2)
  2. Verify SF is between 3 and 10
  3. If SF < 3 -> increase | If SF > 10 -> can reduce

II. USER GUIDE
--------------
  PARAMETERS: Enter sky background (SharpCap) + sensor params,
              or use camera database (40+ models: ZWO, QHY,
              Moravian, ATIK, Player One, ToupTek).
  SWAMP FACTOR: Choose SF 3-10, read target medians.
  OPTIMAL TIME: Choose noise %, read recommended times per filter.
  COMPARISON: Compare 2 strategies in L and RGB.
  CHARTS: Noise curves vs exposure time.
  TABLES: Complete tables (green = below threshold).

III. AUTOMATIC UPDATES
-----------------------
  The application updates itself automatically:

  VIA LAUNCHERS (run.bat / run.sh):
    On each launch, the script silently runs git fetch + git pull
    to pull the latest version. Requires git installed and a
    cloned repository (not a zip download).

  VIA PYTHON (fallback):
    If you run ExposureCalculator.py directly, a background thread
    checks GitHub for a newer version. If found:
    - With git: automatic update, restart message shown.
    - Without git: download link displayed.
    If there is no internet, the app starts normally.

IV. BUG REPORTING
------------------
  AUTOMATIC:
    All unhandled errors are logged to:
      .exposure_calc_errors.log (in the program directory)
    Format: date, version, OS, Python, full traceback.
    The file is automatically truncated beyond 500 KB.

  MANUAL:
    Click the red "Report a bug" button in the top bar.
    A pre-filled report opens on GitHub Issues with your
    environment info and the last logged error.
    Just describe the problem and submit.

V. SETTINGS PERSISTENCE
-------------------------
  AUTOMATIC:
    All parameters are automatically saved to:
      .exposure_calc_settings.json (in the program directory)
    On next launch, settings are restored.

  EXPORT / IMPORT:
    Export: saves parameters + results to a JSON file.
    Import: loads parameters from a previously exported JSON file.
"""


# === CALCULATIONS ===
def additional_noise(t, sky, rn):
    if rn == 0 or t <= 0 or sky <= 0:
        return 0.0
    r = t * sky / (rn * rn)
    return math.sqrt((r + 1) / r) - 1

def c_factor(npct):
    if npct <= 0:
        return float("inf")
    ratio = ((100 + npct) / 100) ** 2 - 1
    return round(1.0 / ratio, 1) if ratio > 0 else float("inf")

def optimal_time(c, rn, sky):
    if sky <= 0 or c == float("inf"):
        return float("inf")
    return math.ceil(c * rn * rn / sky)

def target_median(sf, rn, ge, offset, bits):
    if ge == 0:
        return 0
    return int((sf * rn * rn / ge + offset) * 65536 / (2 ** bits))

def sec_to_mmss(s):
    if s is None or s == float("inf") or s < 0:
        return "\u2014"
    m, sec = divmod(int(s), 60)
    return f"{m:02d}:{sec:02d}"


# === THEME ===
CL = {
    "bg": "#0d1117", "bg2": "#161b22", "card": "#1c2333", "border": "#30363d",
    "accent": "#f0883e", "accent2": "#58a6ff", "red": "#f85149", "green": "#3fb950",
    "purple": "#bc8cff", "text": "#e6edf3", "dim": "#8b949e", "input": "#fffbe6",
    "input_fg": "#1c2333", "white": "#ffffff"
}

DARK_STYLE = f"""
QMainWindow, QDialog {{ background-color: {CL['bg']}; }}
QWidget {{ color: {CL['text']}; font-family: "Segoe UI", "Noto Sans", sans-serif; }}
QTabWidget::pane {{ border: 1px solid {CL['border']}; background: {CL['bg']}; border-radius: 4px; }}
QTabBar::tab {{
    background: {CL['bg2']}; color: {CL['dim']}; padding: 8px 16px;
    border-top-left-radius: 4px; border-top-right-radius: 4px; margin-right: 2px;
    font-weight: bold; font-size: 10pt;
}}
QTabBar::tab:selected {{ background: {CL['card']}; color: {CL['accent']}; border-bottom: 2px solid {CL['accent']}; }}
QGroupBox {{
    color: {CL['accent']}; border: 1px solid {CL['border']}; border-radius: 6px;
    margin-top: 12px; padding-top: 16px; font-weight: bold; font-size: 11pt;
    background-color: {CL['card']};
}}
QGroupBox::title {{ subcontrol-origin: margin; left: 12px; padding: 0 6px; }}
QLineEdit {{
    background-color: {CL['input']}; color: {CL['input_fg']}; border: 2px solid {CL['border']};
    border-radius: 4px; padding: 5px 8px; font-family: "Consolas", "Menlo", monospace;
    font-size: 11pt; font-weight: bold; selection-background-color: {CL['accent']};
}}
QLineEdit:focus {{ border-color: {CL['accent']}; }}
QComboBox {{
    background-color: {CL['bg2']}; color: {CL['text']}; border: 1px solid {CL['border']};
    border-radius: 4px; padding: 5px 10px; min-width: 100px; font-size: 9pt;
}}
QComboBox:hover {{ border-color: {CL['accent']}; }}
QComboBox::drop-down {{ border: none; width: 20px; }}
QComboBox QAbstractItemView {{
    background-color: {CL['bg2']}; color: {CL['text']};
    selection-background-color: {CL['accent']}; selection-color: {CL['bg']};
    border: 1px solid {CL['border']};
}}
QPushButton {{
    border: none; border-radius: 4px; padding: 6px 14px;
    font-weight: bold; font-size: 9pt; min-height: 24px;
}}
QPushButton:hover {{ opacity: 0.9; }}
QScrollArea {{ border: none; background: transparent; }}
QScrollBar:vertical {{
    background: {CL['bg']}; width: 8px; border-radius: 4px;
}}
QScrollBar::handle:vertical {{
    background: {CL['border']}; border-radius: 4px; min-height: 30px;
}}
QScrollBar::handle:vertical:hover {{ background: {CL['accent']}; }}
QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; }}
QTextEdit {{
    background-color: {CL['bg2']}; color: {CL['text']}; border: none;
    font-family: "Consolas", "Menlo", monospace; font-size: 10pt; padding: 15px;
}}
QToolTip {{
    background-color: {CL['bg2']}; color: {CL['text']}; border: 1px solid {CL['accent']};
    border-radius: 4px; padding: 6px; font-size: 9pt;
}}
QLabel {{ background: transparent; }}
"""

TIMES_LRGB = [4, 10, 20, 30, 40, 50, 60, 100, 200, 300, 400, 500, 600, 1000, 2000]
TIMES_NB = [100, 200, 300, 400, 500, 600, 1000, 2000]
FILTERS = [("L", "sky_L"), ("RGB", "sky_RGB"), ("NB 12 nm", "sky_NB12"), ("NB 7 nm", "sky_NB7"), ("NB 3 nm", "sky_NB3")]

_UPDATE_URL = "https://raw.githubusercontent.com/ARP273-ROSE/exposure-calculator/main/ExposureCalculator.py"
_REPO_URL = "https://github.com/ARP273-ROSE/exposure-calculator"


def _parse_version(v):
    try:
        return tuple(int(x) for x in v.strip().split("."))
    except Exception:
        return (0,)


# === MAIN WINDOW ===
class ExposureCalculatorWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.lang = _detect_language()

        # Current values (dict-based instead of tkinter vars)
        self._vals = {
            "sky_L": 1.76, "sky_RGB": 1.31, "sky_NB12": 0.12, "sky_NB7": 0.07,
            "rn": 1.375, "ge": 0.244, "dc": 0.0017, "bits": 16, "offset": 20,
            "sf": 10, "noise_pct": 5.0,
            "exp_L": 90, "exp_RGB": 90, "exp_NB12": 180, "exp_NB7": 300, "exp_NB3": 300,
            "cL1": 120, "cL2": 180, "cR1": 120, "cR2": 180,
            "brand": "ZWO", "model": "", "gain_setting": "", "temp_setting": "",
        }

        # Restore saved settings
        saved = _load_settings()
        if saved:
            if "lang" in saved and saved["lang"] in ("fr", "en"):
                self.lang = saved["lang"]
            for k in self._vals:
                if k in saved:
                    try:
                        self._vals[k] = type(self._vals[k])(saved[k])
                    except (ValueError, TypeError):
                        pass
            # Handle old format nested "parameters"
            if "parameters" in saved and isinstance(saved["parameters"], dict):
                for k in ("sky_L", "sky_RGB", "sky_NB12", "sky_NB7", "rn", "ge", "dc", "bits", "offset"):
                    if k in saved["parameters"]:
                        try:
                            self._vals[k] = type(self._vals[k])(saved["parameters"][k])
                        except (ValueError, TypeError):
                            pass

        # Widget references for result labels
        self._result_labels = {}
        self._input_fields = {}
        self._combo_refs = {}
        self._save_timer = QTimer(self)
        self._save_timer.setSingleShot(True)
        self._save_timer.timeout.connect(self._do_save)
        self._recalc_timer = QTimer(self)
        self._recalc_timer.setSingleShot(True)
        self._recalc_timer.timeout.connect(self._recalc)
        self._charts_dirty = True
        self._chart_fig = None

        self._build_ui()
        self._recalc()

    def _t(self, key):
        return tr(key, self.lang)

    @property
    def sky_NB3(self):
        try:
            return self._vals["sky_NB12"] / 4.0
        except Exception:
            return 0.03

    def _sky(self, k):
        if k == "sky_NB3":
            return self.sky_NB3
        return self._vals.get(k, 0)

    def _make_input(self, val_key, width=80):
        """Create a QLineEdit bound to a value key."""
        field = QLineEdit(str(self._vals.get(val_key, "")))
        field.setFixedWidth(width)
        field.setToolTip(val_key)
        field.textChanged.connect(lambda text, k=val_key: self._on_input_changed(k, text))
        self._input_fields[val_key] = field
        return field

    def _on_input_changed(self, key, text):
        try:
            if key in ("bits", "sf", "exp_L", "exp_RGB", "exp_NB12", "exp_NB7", "exp_NB3", "cL1", "cL2", "cR1", "cR2"):
                self._vals[key] = int(text)
            else:
                self._vals[key] = float(text)
        except (ValueError, TypeError):
            return
        self._schedule_recalc()

    def _schedule_recalc(self):
        self._recalc_timer.start(150)

    def _auto_save(self):
        self._save_timer.start(500)

    def _do_save(self):
        data = dict(self._vals)
        data["version"] = __version__
        data["lang"] = self.lang
        _save_settings_to_file(data)

    def _make_label(self, text, color=None, font_size=10, bold=False, italic=False):
        lbl = QLabel(text)
        style_parts = [f"color: {color or CL['text']}"]
        if font_size:
            style_parts.append(f"font-size: {font_size}pt")
        if bold:
            style_parts.append("font-weight: bold")
        if italic:
            style_parts.append("font-style: italic")
        lbl.setStyleSheet("; ".join(style_parts))
        return lbl

    def _make_result_label(self, key, text="--", color=None, font_size=12, bold=True, mono=True):
        lbl = QLabel(text)
        font_family = '"Consolas", "Menlo", monospace' if mono else '"Segoe UI", sans-serif'
        style = f"color: {color or CL['green']}; font-size: {font_size}pt; font-family: {font_family};"
        if bold:
            style += " font-weight: bold;"
        lbl.setStyleSheet(style)
        self._result_labels[key] = lbl
        return lbl

    def _make_card(self, title):
        box = QGroupBox(f"  {title}  ")
        return box

    def _make_scrollable(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        inner = QWidget()
        scroll.setWidget(inner)
        return scroll, inner

    def _make_button(self, text, callback, bg_color):
        btn = QPushButton(text)
        btn.setStyleSheet(f"background-color: {bg_color}; color: {CL['bg']};")
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.clicked.connect(callback)
        return btn

    def _build_ui(self):
        self.setWindowTitle(self._t("win_title"))
        ico_path = _resource_path("logo-expo.ico")
        if os.path.isfile(ico_path):
            self.setWindowIcon(QIcon(ico_path))
        self.setMinimumSize(1100, 750)
        screen = QApplication.primaryScreen()
        if screen:
            sg = screen.availableGeometry()
            w = max(1200, min(int(sg.width() * 0.85), 1600))
            h = max(800, min(int(sg.height() * 0.85), 1000))
            self.resize(w, h)
            self.move((sg.width() - w) // 2, max(0, (sg.height() - h) // 2 - 30))

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Top bar
        top_bar = QWidget()
        top_bar.setStyleSheet(f"background-color: {CL['bg2']}; padding: 5px;")
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(10, 5, 10, 5)
        top_layout.addWidget(self._make_label(self._t("win_title"), CL["accent"], 12, bold=True))
        top_layout.addStretch()
        for txt, cmd, bg in [
            (self._t("recalc"), self._recalc, CL["green"]),
            (self._t("export"), self._export, CL["accent2"]),
            (self._t("import"), self._import_settings, CL["accent2"]),
            (self._t("btn_bug"), self._report_bug, CL["red"]),
            (self._t("lang_btn"), self._toggle_lang, CL["purple"]),
        ]:
            top_layout.addWidget(self._make_button(txt, cmd, bg))
        main_layout.addWidget(top_bar)

        # Yellow info bar
        info_bar = QLabel(self._t("fill_yellow"))
        info_bar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info_bar.setStyleSheet(f"background-color: {CL['accent']}; color: {CL['bg']}; padding: 3px; font-size: 9pt;")
        main_layout.addWidget(info_bar)

        # Tab widget
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)
        self.tabs.currentChanged.connect(self._on_tab_changed)

        tab_builders = [
            ("tab_params", self._build_params_tab),
            ("tab_a1", self._build_sf_tab),
            ("tab_a2", self._build_optimal_tab),
            ("tab_compare", self._build_compare_tab),
            ("tab_charts", self._build_charts_tab),
            ("tab_tables", self._build_tables_tab),
            ("tab_help", self._build_help_tab),
        ]
        for key, builder in tab_builders:
            widget = builder()
            self.tabs.addTab(widget, f" {self._t(key)} ")

    def _build_params_tab(self):
        scroll, inner = self._make_scrollable()
        layout = QGridLayout(inner)
        layout.setContentsMargins(6, 6, 6, 6)

        # Sky background card
        sky_card = self._make_card(self._t("sec_sky"))
        sky_lay = QGridLayout(sky_card)

        link = QLabel(f'<a href="https://tools.sharpcap.co.uk/" style="color: {CL["accent2"]};">{self._t("sky_link")}</a>')
        link.setOpenExternalLinks(True)
        sky_lay.addWidget(link, 0, 0, 1, 2)

        for i, (lk, vk) in enumerate([("lbl_L", "sky_L"), ("lbl_RGB", "sky_RGB"), ("lbl_NB12", "sky_NB12"), ("lbl_NB7", "sky_NB7")], 1):
            sky_lay.addWidget(self._make_label(self._t(lk)), i, 0)
            sky_lay.addWidget(self._make_input(vk), i, 1)

        sky_lay.addWidget(self._make_label(self._t("lbl_NB3"), CL["dim"], 9, italic=True), 5, 0)
        sky_lay.addWidget(self._make_result_label("nb3_val", "0.030", CL["green"], 11), 5, 1)

        warn = self._make_label(self._t("warn_qe"), CL["red"], 8, italic=True)
        warn.setWordWrap(True)
        sky_lay.addWidget(warn, 6, 0, 1, 2)

        layout.addWidget(sky_card, 0, 0)

        # Sensor params card
        sensor_card = self._make_card(self._t("sec_sensor"))
        sensor_lay = QGridLayout(sensor_card)

        tips = {"rn": "tip_rn", "ge": "tip_ge", "dc": "tip_dc"}
        for i, (lk, vk) in enumerate([("lbl_rn", "rn"), ("lbl_ge", "ge"), ("lbl_dc", "dc"), ("lbl_bits", "bits"), ("lbl_offset", "offset")]):
            sensor_lay.addWidget(self._make_label(self._t(lk)), i, 0)
            sensor_lay.addWidget(self._make_input(vk), i, 1)
            tip_key = tips.get(vk)
            if tip_key:
                sensor_lay.addWidget(self._make_label(self._t(tip_key), CL["dim"], 8, italic=True), i, 2)

        layout.addWidget(sensor_card, 0, 1)

        # Camera database card
        cam_card = self._make_card(self._t("sec_cam"))
        cam_lay = QVBoxLayout(cam_card)

        nc = sum(len(m) for m in CAMERA_DB.values())
        cam_lay.addWidget(self._make_label(self._t("cam_count").format(n=nc, s=len(_SENSORS)), CL["dim"], 9, italic=True))

        combo_row = QHBoxLayout()
        for lk, vk, vals in [
            ("lbl_brand", "brand", list(CAMERA_DB.keys())),
            ("lbl_model", "model", []),
            ("lbl_gain", "gain_setting", []),
            ("lbl_temp", "temp_setting", []),
        ]:
            combo_row.addWidget(self._make_label(self._t(lk)))
            cb = QComboBox()
            cb.addItems(vals)
            if vk == "model":
                cb.setMinimumWidth(180)
            self._combo_refs[vk] = cb
            combo_row.addWidget(cb)

        self._combo_refs["brand"].currentTextChanged.connect(self._on_brand_changed)
        self._combo_refs["model"].currentTextChanged.connect(self._on_model_changed)

        apply_btn = self._make_button(self._t("btn_apply"), self._apply_camera, CL["accent"])
        combo_row.addWidget(apply_btn)
        cam_lay.addLayout(combo_row)

        self._cam_info_label = self._make_label("", CL["green"], 9, italic=True)
        cam_lay.addWidget(self._cam_info_label)

        layout.addWidget(cam_card, 1, 0, 1, 2)
        layout.setRowStretch(2, 1)

        # Initialize brand combo
        brand = self._vals.get("brand", "ZWO")
        idx = self._combo_refs["brand"].findText(brand)
        if idx >= 0:
            self._combo_refs["brand"].setCurrentIndex(idx)
        self._on_brand_changed()

        return scroll

    def _build_sf_tab(self):
        scroll, inner = self._make_scrollable()
        layout = QVBoxLayout(inner)
        layout.setContentsMargins(15, 10, 15, 10)

        layout.addWidget(self._make_label(self._t("a1_title"), CL["accent"], 13, bold=True))
        explain = self._make_label(self._t("a1_explain"), CL["dim"], 9)
        explain.setWordWrap(True)
        layout.addWidget(explain)

        card = self._make_card(self._t("lbl_sf"))
        card_lay = QVBoxLayout(card)

        sf_row = QHBoxLayout()
        sf_row.addWidget(self._make_label(self._t("lbl_sf") + " :"))
        sf_row.addWidget(self._make_input("sf", 60))
        sf_row.addWidget(self._make_label(self._t("sf_range"), CL["dim"], 9, italic=True))
        sf_row.addStretch()
        card_lay.addLayout(sf_row)

        card_lay.addWidget(self._make_label(self._t("lbl_median"), font_size=11, bold=True))

        medians_row = QHBoxLayout()
        for label_text, color, key in [("SF x3", CL["accent2"], "sf3"), ("SF xN", CL["accent"], "sfn"), ("SF x10", CL["green"], "sf10")]:
            box = QFrame()
            box.setStyleSheet(f"background-color: {CL['bg2']}; border: 1px solid {CL['border']}; border-radius: 4px; padding: 8px;")
            box_lay = QVBoxLayout(box)
            box_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
            box_lay.addWidget(self._make_label(label_text, color, 10, bold=True))
            box_lay.addWidget(self._make_result_label(f"median_{key}", "--", CL["white"], 22))
            medians_row.addWidget(box)
        card_lay.addLayout(medians_row)

        for tip_key in ("tip_median1", "tip_median2"):
            tip = self._make_label(self._t(tip_key), CL["dim"], 9)
            tip.setWordWrap(True)
            card_lay.addWidget(tip)

        layout.addWidget(card)
        layout.addStretch()
        return scroll

    def _build_optimal_tab(self):
        scroll, inner = self._make_scrollable()
        layout = QVBoxLayout(inner)
        layout.setContentsMargins(15, 10, 15, 10)

        layout.addWidget(self._make_label(self._t("a2_title"), CL["accent"], 13, bold=True))
        explain = self._make_label(self._t("a2_explain"), CL["dim"], 9)
        explain.setWordWrap(True)
        layout.addWidget(explain)

        # Noise % card
        noise_card = self._make_card(self._t("lbl_noise_pct"))
        nc_lay = QVBoxLayout(noise_card)
        noise_row = QHBoxLayout()
        noise_row.addWidget(self._make_label(self._t("lbl_noise_pct") + " :"))
        noise_row.addWidget(self._make_input("noise_pct", 60))
        noise_row.addWidget(self._make_label("%", font_size=11, bold=True))
        noise_row.addWidget(self._make_label("|", CL["border"], 14))
        noise_row.addWidget(self._make_label(self._t("lbl_c") + " :"))
        noise_row.addWidget(self._make_result_label("c_factor", "--", CL["green"], 14))
        noise_row.addStretch()
        nc_lay.addLayout(noise_row)
        nc_lay.addWidget(self._make_label(self._t("lbl_examples"), CL["dim"], 9, italic=True))
        layout.addWidget(noise_card)

        # Optimal times card
        opti_card = self._make_card(self._t("sec_opti"))
        oc_lay = QVBoxLayout(opti_card)

        header = QHBoxLayout()
        for text, w in [(self._t("col_filter"), 100), (self._t("col_sec"), 100), (self._t("col_mmss"), 100)]:
            lbl = self._make_label(text, CL["accent2"], 10, bold=True)
            lbl.setFixedWidth(w)
            header.addWidget(lbl)
        header.addStretch()
        oc_lay.addLayout(header)

        for fn, _ in FILTERS:
            row = QHBoxLayout()
            lbl = self._make_label(fn)
            lbl.setFixedWidth(100)
            row.addWidget(lbl)
            row.addWidget(self._make_result_label(f"opti_sec_{fn}", "--", CL["green"], 12))
            self._result_labels[f"opti_sec_{fn}"].setFixedWidth(100)
            row.addWidget(self._make_result_label(f"opti_mmss_{fn}", "--", CL["dim"], 12, mono=True))
            self._result_labels[f"opti_mmss_{fn}"].setFixedWidth(100)
            row.addStretch()
            oc_lay.addLayout(row)

        tip = self._make_label(self._t("tip_opti"), CL["dim"], 9)
        tip.setWordWrap(True)
        oc_lay.addWidget(tip)
        layout.addWidget(opti_card)

        # Additional noise for given time card
        gain_card = self._make_card(self._t("sec_gain_long"))
        gc_lay = QVBoxLayout(gain_card)

        exp_key_map = {"L": "exp_L", "RGB": "exp_RGB", "NB 12 nm": "exp_NB12", "NB 7 nm": "exp_NB7", "NB 3 nm": "exp_NB3"}
        for fn, _ in FILTERS:
            row = QHBoxLayout()
            lbl = self._make_label(fn)
            lbl.setFixedWidth(100)
            row.addWidget(lbl)
            row.addWidget(self._make_input(exp_key_map[fn], 70))
            row.addWidget(self._make_label("s"))
            row.addWidget(self._make_label("->", CL["dim"]))
            row.addWidget(self._make_result_label(f"gain_noise_{fn}", "--", CL["accent"], 12))
            row.addStretch()
            gc_lay.addLayout(row)

        layout.addWidget(gain_card)
        layout.addStretch()
        return scroll

    def _build_compare_tab(self):
        widget = QWidget()
        layout = QHBoxLayout(widget)

        for title_key, sky_key, v1_key, v2_key, delta_key in [
            ("cmp_title_L", "sky_L", "cL1", "cL2", "dL"),
            ("cmp_title_RGB", "sky_RGB", "cR1", "cR2", "dR"),
        ]:
            card = self._make_card(self._t(title_key))
            card_lay = QVBoxLayout(card)

            for lk, vk, nk in [(self._t("lbl_strat1"), v1_key, f"n{delta_key}1"), (self._t("lbl_strat2"), v2_key, f"n{delta_key}2")]:
                row = QHBoxLayout()
                row.addWidget(self._make_label(lk + " :"))
                row.addWidget(self._make_input(vk, 70))
                row.addWidget(self._make_label("s"))
                row.addWidget(self._make_label("|", CL["border"], 14))
                row.addWidget(self._make_label(self._t("lbl_noise") + " :"))
                row.addWidget(self._make_result_label(nk, "--", CL["accent2"], 11))
                row.addStretch()
                card_lay.addLayout(row)

            sep = QFrame()
            sep.setFrameShape(QFrame.Shape.HLine)
            sep.setStyleSheet(f"color: {CL['border']};")
            card_lay.addWidget(sep)

            delta_row = QHBoxLayout()
            delta_row.addWidget(self._make_label(self._t("lbl_delta"), font_size=12, bold=True))
            delta_row.addWidget(self._make_result_label(delta_key, "--", CL["green"], 18))
            delta_row.addStretch()
            card_lay.addLayout(delta_row)

            card_lay.addStretch()
            layout.addWidget(card)

        return widget

    def _build_charts_tab(self):
        self._chart_widget = QWidget()
        self._chart_layout = QVBoxLayout(self._chart_widget)
        self._chart_layout.setContentsMargins(0, 0, 0, 0)
        return self._chart_widget

    def _draw_charts(self):
        # Clear existing
        while self._chart_layout.count():
            item = self._chart_layout.takeAt(0)
            w = item.widget()
            if w:
                w.setParent(None)
                w.deleteLater()

        if self._chart_fig is not None:
            try:
                self._chart_fig.clf()
                import matplotlib.pyplot as plt
                plt.close(self._chart_fig)
            except Exception:
                pass

        rn = self._vals["rn"]
        thr = self._vals["noise_pct"] / 100

        size = self._chart_widget.size()
        fw = max(400, size.width())
        fh = max(300, size.height())
        dpi = 100
        fig_w = fw / dpi
        fig_h = min(fh / dpi, fig_w * 0.52)

        fig = Figure(figsize=(fig_w, fig_h), dpi=dpi, facecolor=CL["bg"])
        fig.set_tight_layout(True)

        for idx, (times, skies, colors, names, tk_k) in enumerate([
            (TIMES_LRGB, [self._sky("sky_L"), self._sky("sky_RGB")],
             [CL["red"], CL["accent"]], ["L", "RGB"], "ch1_title"),
            (TIMES_NB, [self._sky("sky_NB12"), self._sky("sky_NB7"), self.sky_NB3],
             [CL["red"], CL["accent"], CL["accent2"]], ["NB12", "NB7", "NB3"], "ch2_title"),
        ]):
            ax = fig.add_subplot(1, 2, idx + 1)
            ax.set_facecolor(CL["bg2"])
            allv = []
            for sky, co, nm in zip(skies, colors, names):
                v = [additional_noise(t, sky, rn) * 100 for t in times]
                allv.extend(v)
                ax.plot(times, v, "o-", color=co, label=nm, linewidth=2, markersize=4)
            ax.axhline(y=thr * 100, color=CL["green"], linestyle="--", linewidth=1.5, label=self._t("ch_thresh"))
            ymax = max(max(allv) if allv else 1, thr * 100) * 1.15
            ax.set_ylim(0, ymax)
            ax.set_xlabel(self._t("ch_x"), color=CL["text"], fontsize=9)
            ax.set_ylabel(self._t("ch_y"), color=CL["text"], fontsize=9)
            ax.set_title(self._t(tk_k), color=CL["accent"], fontsize=11, fontweight="bold")
            ax.legend(fontsize=8, facecolor=CL["bg2"], edgecolor=CL["border"], labelcolor=CL["text"])
            ax.tick_params(colors=CL["dim"], labelsize=8)
            ax.grid(True, alpha=0.15, color=CL["dim"])
            for sp in ax.spines.values():
                sp.set_color(CL["border"])

        self._chart_fig = fig
        canvas = FigureCanvasQTAgg(fig)
        self._chart_layout.addWidget(canvas)
        self._charts_dirty = False

    def _build_tables_tab(self):
        scroll, inner = self._make_scrollable()
        self._tables_inner = inner
        self._tables_layout = QVBoxLayout(inner)
        self._tables_layout.setContentsMargins(8, 6, 8, 6)
        return scroll

    def _update_tables(self):
        # Clear
        while self._tables_layout.count():
            item = self._tables_layout.takeAt(0)
            w = item.widget()
            if w:
                w.setParent(None)
                w.deleteLater()

        rn = self._vals["rn"]
        thr = self._vals["noise_pct"] / 100

        for tk_k, times, series in [
            ("tbl_lrgb", TIMES_LRGB, [
                ("L", [additional_noise(t, self._sky("sky_L"), rn) for t in TIMES_LRGB]),
                ("RGB", [additional_noise(t, self._sky("sky_RGB"), rn) for t in TIMES_LRGB]),
            ]),
            ("tbl_nb", TIMES_NB, [
                ("NB12", [additional_noise(t, self._sky("sky_NB12"), rn) for t in TIMES_NB]),
                ("NB7", [additional_noise(t, self._sky("sky_NB7"), rn) for t in TIMES_NB]),
                ("NB3", [additional_noise(t, self.sky_NB3, rn) for t in TIMES_NB]),
            ]),
        ]:
            card = self._make_card(self._t(tk_k))
            card_lay = QVBoxLayout(card)

            # Header
            hdr = QHBoxLayout()
            lbl = self._make_label(self._t("tbl_exp"), CL["accent2"], 9, bold=True)
            lbl.setFixedWidth(80)
            hdr.addWidget(lbl)
            for t in times:
                cell = self._make_label(str(t), CL["accent2"], 9, bold=True)
                cell.setFixedWidth(55)
                cell.setAlignment(Qt.AlignmentFlag.AlignCenter)
                hdr.addWidget(cell)
            hdr.addStretch()
            card_lay.addLayout(hdr)

            # Data rows
            for nm, vals in series:
                row = QHBoxLayout()
                name_lbl = self._make_label(nm, font_size=9, bold=True)
                name_lbl.setFixedWidth(80)
                row.addWidget(name_lbl)
                for v in vals:
                    color = CL["green"] if v <= thr else CL["red"]
                    cell = QLabel(f"{v * 100:.1f}%")
                    cell.setFixedWidth(55)
                    cell.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    cell.setStyleSheet(f"color: {color}; font-family: 'Consolas', monospace; font-size: 9pt;")
                    row.addWidget(cell)
                row.addStretch()
                card_lay.addLayout(row)

            # Threshold row
            thr_row = QHBoxLayout()
            thr_lbl = self._make_label(self._t("tbl_thresh"), CL["green"], 9, italic=True)
            thr_lbl.setFixedWidth(80)
            thr_row.addWidget(thr_lbl)
            for _ in times:
                cell = QLabel(f"{thr * 100:.0f}%")
                cell.setFixedWidth(55)
                cell.setAlignment(Qt.AlignmentFlag.AlignCenter)
                cell.setStyleSheet(f"color: {CL['green']}; font-family: 'Consolas', monospace; font-size: 9pt; font-style: italic;")
                thr_row.addWidget(cell)
            thr_row.addStretch()
            card_lay.addLayout(thr_row)

            self._tables_layout.addWidget(card)

        self._tables_layout.addStretch()

    def _build_help_tab(self):
        from PyQt6.QtWidgets import QTextEdit
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.addWidget(self._make_label(self._t("help_title"), CL["accent"], 13, bold=True))
        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setPlainText(HELP_FR if self.lang == "fr" else HELP_EN)
        layout.addWidget(text_edit)
        return widget

    # Camera selection
    def _on_brand_changed(self, brand=None):
        if brand is None:
            brand = self._combo_refs["brand"].currentText()
        self._vals["brand"] = brand
        models = list(CAMERA_DB.get(brand, {}).keys())
        cb = self._combo_refs["model"]
        cb.blockSignals(True)
        cb.clear()
        cb.addItems(models)
        cb.blockSignals(False)
        if models:
            cb.setCurrentIndex(0)
            self._on_model_changed(models[0])

    def _on_model_changed(self, model=None):
        if model is None:
            model = self._combo_refs["model"].currentText()
        self._vals["model"] = model
        cam = CAMERA_DB.get(self._vals["brand"], {}).get(model)
        if not cam:
            return
        gains = list(cam["gains"].keys())
        cb_g = self._combo_refs["gain_setting"]
        cb_g.blockSignals(True)
        cb_g.clear()
        cb_g.addItems(gains)
        cb_g.blockSignals(False)
        if gains:
            cb_g.setCurrentIndex(0)
            self._vals["gain_setting"] = gains[0]

        temps = [str(t) for t in cam["temps"].keys()]
        cb_t = self._combo_refs["temp_setting"]
        cb_t.blockSignals(True)
        cb_t.clear()
        cb_t.addItems(temps)
        cb_t.blockSignals(False)
        if temps:
            cb_t.setCurrentIndex(0)
            self._vals["temp_setting"] = temps[0]

    def _apply_camera(self):
        brand = self._combo_refs["brand"].currentText()
        model = self._combo_refs["model"].currentText()
        cam = CAMERA_DB.get(brand, {}).get(model)
        if not cam:
            return
        gk = self._combo_refs["gain_setting"].currentText()
        if gk in cam["gains"]:
            g = cam["gains"][gk]
            self._vals["rn"] = g["rn"]
            self._vals["ge"] = g["ge"]
            self._vals["offset"] = g.get("offset", 20)
            for k in ("rn", "ge", "offset"):
                if k in self._input_fields:
                    self._input_fields[k].blockSignals(True)
                    self._input_fields[k].setText(str(self._vals[k]))
                    self._input_fields[k].blockSignals(False)
        self._vals["bits"] = cam["bits"]
        if "bits" in self._input_fields:
            self._input_fields["bits"].blockSignals(True)
            self._input_fields["bits"].setText(str(cam["bits"]))
            self._input_fields["bits"].blockSignals(False)

        temp_str = self._combo_refs["temp_setting"].currentText()
        for k, v in cam["temps"].items():
            if str(k) == temp_str:
                self._vals["dc"] = v
                if "dc" in self._input_fields:
                    self._input_fields["dc"].blockSignals(True)
                    self._input_fields["dc"].setText(str(v))
                    self._input_fields["dc"].blockSignals(False)
                break

        self._cam_info_label.setText(
            f"  {brand} {model} | {gk} | T={temp_str}C | "
            f"RN={self._vals['rn']} Gain={self._vals['ge']} e-/ADU "
            f"Dc={self._vals['dc']} {cam['bits']}bit Off={self._vals['offset']}"
        )
        self._recalc()

    def _recalc(self):
        try:
            rn = self._vals["rn"]
            ge = self._vals["ge"]
            bits = self._vals["bits"]
            off = self._vals["offset"]
            sf = self._vals["sf"]
            npct = self._vals["noise_pct"]
        except Exception:
            return
        if rn <= 0 or ge <= 0:
            return

        # NB3 auto
        if "nb3_val" in self._result_labels:
            self._result_labels["nb3_val"].setText(f"{self.sky_NB3:.4f}")

        # Swamp Factor medians
        for key, sf_val in [("median_sf3", 3), ("median_sfn", sf), ("median_sf10", 10)]:
            if key in self._result_labels:
                self._result_labels[key].setText(str(target_median(sf_val, rn, ge, off, bits)))

        # C factor & optimal times
        cf = c_factor(npct)
        if "c_factor" in self._result_labels:
            self._result_labels["c_factor"].setText(f"{cf:.1f}" if cf < 1e6 else "inf")
        for fn, sk in FILTERS:
            t = optimal_time(cf, rn, self._sky(sk))
            sec_key = f"opti_sec_{fn}"
            mmss_key = f"opti_mmss_{fn}"
            if sec_key in self._result_labels:
                if t == float("inf"):
                    self._result_labels[sec_key].setText("inf")
                    self._result_labels[mmss_key].setText("--")
                else:
                    self._result_labels[sec_key].setText(f"{t} s")
                    self._result_labels[mmss_key].setText(sec_to_mmss(t))

        # Additional noise for given exposure
        exp_key_map = {"L": "exp_L", "RGB": "exp_RGB", "NB 12 nm": "exp_NB12", "NB 7 nm": "exp_NB7", "NB 3 nm": "exp_NB3"}
        for fn, sk in FILTERS:
            key = f"gain_noise_{fn}"
            if key in self._result_labels:
                try:
                    n = additional_noise(self._vals[exp_key_map[fn]], self._sky(sk), rn)
                    self._result_labels[key].setText(f"{n * 100:.2f} %")
                except Exception:
                    pass

        # Comparison
        try:
            sL = self._sky("sky_L")
            sR = self._sky("sky_RGB")
            n1 = additional_noise(self._vals["cL1"], sL, rn)
            n2 = additional_noise(self._vals["cL2"], sL, rn)
            if "ndL1" in self._result_labels:
                self._result_labels["ndL1"].setText(f"{n1 * 100:.3f}%")
            if "ndL2" in self._result_labels:
                self._result_labels["ndL2"].setText(f"{n2 * 100:.3f}%")
            if "dL" in self._result_labels:
                self._result_labels["dL"].setText(f"{(n2 - n1) * 100:+.4f}%")
            n1 = additional_noise(self._vals["cR1"], sR, rn)
            n2 = additional_noise(self._vals["cR2"], sR, rn)
            if "ndR1" in self._result_labels:
                self._result_labels["ndR1"].setText(f"{n1 * 100:.3f}%")
            if "ndR2" in self._result_labels:
                self._result_labels["ndR2"].setText(f"{n2 * 100:.3f}%")
            if "dR" in self._result_labels:
                self._result_labels["dR"].setText(f"{(n2 - n1) * 100:+.4f}%")
        except Exception:
            pass

        # Charts
        self._charts_dirty = True
        if self.tabs.currentIndex() == 4:
            QTimer.singleShot(80, self._draw_charts)

        # Tables
        try:
            self._update_tables()
        except Exception:
            pass

        self._auto_save()

    def _on_tab_changed(self, idx):
        if idx == 4 and self._charts_dirty:
            QTimer.singleShot(80, self._draw_charts)

    def _toggle_lang(self):
        self.lang = "en" if self.lang == "fr" else "fr"
        # Rebuild UI by recreating window content
        central = self.centralWidget()
        if central:
            central.setParent(None)
            central.deleteLater()
        self._result_labels = {}
        self._input_fields = {}
        self._combo_refs = {}
        self._charts_dirty = True
        self._chart_fig = None
        self._build_ui()
        self._recalc()

    def _export(self):
        try:
            rn = self._vals["rn"]
            ge = self._vals["ge"]
            bits = self._vals["bits"]
            off = self._vals["offset"]
            npct = self._vals["noise_pct"]
            cf = c_factor(npct)
            data = {
                "settings": dict(self._vals),
                "parameters": {
                    "sky_L": self._vals["sky_L"], "sky_RGB": self._vals["sky_RGB"],
                    "sky_NB12": self._vals["sky_NB12"], "sky_NB7": self._vals["sky_NB7"],
                    "sky_NB3": self.sky_NB3, "rn": rn, "ge": ge,
                    "dc": self._vals["dc"], "bits": bits, "offset": off,
                },
                "approach1": {
                    "sf": self._vals["sf"],
                    "median_SF3": target_median(3, rn, ge, off, bits),
                    "median_SF10": target_median(10, rn, ge, off, bits),
                },
                "approach2": {
                    "noise_pct": npct, "c_factor": cf,
                    "times": {fn: optimal_time(cf, rn, self._sky(sk)) for fn, sk in FILTERS},
                },
            }
            path, _ = QFileDialog.getSaveFileName(self, "Export", "exposure_results.json", "JSON (*.json)")
            if path:
                tmp = Path(path).with_suffix(".tmp")
                tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
                tmp.replace(path)
                label = "Exporte" if self.lang == "fr" else "Exported"
                QMessageBox.information(self, "Export", f"{label}!\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def _import_settings(self):
        try:
            path, _ = QFileDialog.getOpenFileName(self, "Import", "", "JSON (*.json);;All (*.*)")
            if not path:
                return
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, dict):
                QMessageBox.critical(self, "Import", self._t("import_err"))
                return
            settings = data.get("settings", data)
            for k in self._vals:
                if k in settings:
                    try:
                        self._vals[k] = type(self._vals[k])(settings[k])
                    except (ValueError, TypeError):
                        pass
            # Handle old format
            if "parameters" in data and isinstance(data["parameters"], dict):
                for k in ("sky_L", "sky_RGB", "sky_NB12", "sky_NB7", "rn", "ge", "dc", "bits", "offset"):
                    if k in data["parameters"]:
                        try:
                            self._vals[k] = type(self._vals[k])(data["parameters"][k])
                        except (ValueError, TypeError):
                            pass
            # Update UI fields
            for k, field in self._input_fields.items():
                field.blockSignals(True)
                field.setText(str(self._vals.get(k, "")))
                field.blockSignals(False)
            self._recalc()
            QMessageBox.information(self, "Import", self._t("import_ok"))
        except Exception:
            QMessageBox.critical(self, "Import", self._t("import_err"))

    def _report_bug(self):
        from urllib.parse import quote
        last_err = _get_last_error()
        if not last_err:
            QMessageBox.information(self, self._t("btn_bug"), self._t("bug_no_errors"))
        err_snippet = last_err[:1500] if last_err else "No automatic error logged."
        env_info = (
            f"- App version: {__version__}\n"
            f"- OS: {platform.system()} {platform.release()} ({platform.machine()})\n"
            f"- Python: {sys.version.split()[0]}\n"
        )
        title = quote(f"[Bug] v{__version__} - ")
        body = quote(
            f"## Environment\n{env_info}\n"
            f"## Description\n<!-- Describe the problem here -->\n\n"
            f"## Steps to reproduce\n1. \n2. \n3. \n\n"
            f"## Last error log\n```\n{err_snippet}\n```\n"
        )
        QDesktopServices.openUrl(QUrl(f"{_REPO_URL}/issues/new?title={title}&body={body}"))


def _check_for_update(window, lang):
    def _worker():
        try:
            import ssl
            from urllib.request import urlopen, Request
            ctx = ssl.create_default_context()
            req = Request(_UPDATE_URL, headers={"User-Agent": "ExposureCalculator"})
            data = urlopen(req, timeout=10, context=ctx).read(2048).decode("utf-8", errors="ignore")
            remote_ver = None
            for line in data.splitlines():
                if line.startswith("__version__"):
                    remote_ver = line.split("=")[1].strip().strip('"').strip("'")
                    break
            if not remote_ver or not re.fullmatch(r"\d+\.\d+\.\d+", remote_ver):
                return
            if _parse_version(remote_ver) <= _parse_version(__version__):
                return
            has_git = os.path.isdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".git"))
            git_ok = False
            if has_git:
                try:
                    cwd = os.path.dirname(os.path.abspath(__file__))
                    subprocess.check_call(["git", "pull", "--ff-only", "origin", "main"],
                                          cwd=cwd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    git_ok = True
                except Exception:
                    pass

            def _notify():
                title = tr("update_available", lang)
                if git_ok:
                    msg = tr("update_restart", lang).format(v=remote_ver)
                else:
                    msg = tr("update_manual", lang).format(v=remote_ver, url=_REPO_URL)
                QMessageBox.information(window, title, msg)

            QTimer.singleShot(0, _notify)
        except Exception:
            pass

    t = threading.Thread(target=_worker, daemon=True)
    t.start()


def main():
    # Frozen exe support
    if getattr(sys, 'frozen', False):
        import multiprocessing
        multiprocessing.freeze_support()
        if sys.stdout is None:
            sys.stdout = open(os.devnull, 'w')
        if sys.stderr is None:
            sys.stderr = open(os.devnull, 'w')

    # DPI awareness
    if platform.system() == "Windows":
        try:
            from ctypes import windll
            windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            pass
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("benoit.exposurecalculator")

    app = QApplication(sys.argv)
    app.setApplicationName("ExposureCalculator")
    app.setApplicationVersion(__version__)
    app.setStyleSheet(DARK_STYLE)

    if platform.system() == "Windows":
        app.setFont(QFont("Segoe UI", 10))
    else:
        app.setFont(QFont("Noto Sans", 10))

    window = ExposureCalculatorWindow()
    window.show()

    # Desktop shortcut on first launch
    try:
        from shortcut_helper import offer_shortcut
        config_path = _APP_DIR / ".exposure_calc_config.json"

        def _get_cfg(key):
            try:
                data = json.loads(config_path.read_text(encoding="utf-8"))
                return data.get(key)
            except Exception:
                return None

        def _set_cfg(key, value):
            try:
                data = {}
                if config_path.exists():
                    data = json.loads(config_path.read_text(encoding="utf-8"))
                data[key] = value
                config_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
            except Exception:
                pass

        offer_shortcut("ExposureCalculator", "ExposureCalculator.py", "logo-expo.ico",
                       get_config=_get_cfg, set_config=_set_cfg)
    except Exception:
        pass

    # Check for updates in background
    _check_for_update(window, window.lang)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
