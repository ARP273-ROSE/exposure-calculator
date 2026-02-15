#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Calcul de Temps d'Exposition Unitaire Ideal  ©Benoit_SAINTOT
Ideal Sub-Exposure Time Calculator
Cross-platform, auto-install, auto-language.
"""

__version__ = "1.01"
__author__ = "©Benoit_SAINTOT — GUI by NGC4565"

import subprocess, sys, importlib, os, math, locale, platform, webbrowser, json, threading
from pathlib import Path

def _ensure_package(pip_name, import_name=None):
    import_name = import_name or pip_name
    try: importlib.import_module(import_name)
    except ImportError:
        print(f"[setup] Installing {pip_name}...")
        try: subprocess.check_call([sys.executable,"-m","pip","install","--quiet",pip_name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except: subprocess.check_call([sys.executable,"-m","pip","install","--quiet","--break-system-packages",pip_name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        importlib.invalidate_caches()

_ensure_package("matplotlib")

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import matplotlib; matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

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
            if brand not in db: db[brand] = {}
            for m in models:
                db[brand][f"{m}  [{sn}]"] = {"sensor":sn,"gains":s["gains"],"temps":s["temps"],"bits":s["bits"]}
    return {b: dict(sorted(db[b].items())) for b in sorted(db.keys())}

CAMERA_DB = _build_camera_db()

# === TRANSLATIONS ===
T = {}
def _init_translations():
    global T
    T = {
        "win_title":{"fr":"Calculateur de Temps d'Exposition — ©Benoit_SAINTOT","en":"Exposure Time Calculator — ©Benoit_SAINTOT"},
        "lang_btn":{"fr":"English","en":"Francais"}, "recalc":{"fr":"Recalculer","en":"Recalculate"},
        "export":{"fr":"Exporter","en":"Export"},
        "fill_yellow":{"fr":"Remplir uniquement les cases jaunes — resultats automatiques","en":"Fill only yellow fields — results update automatically"},
        "tab_params":{"fr":"Parametres","en":"Parameters"}, "tab_a1":{"fr":"Swamp Factor","en":"Swamp Factor"},
        "tab_a2":{"fr":"Temps Optimal","en":"Optimal Time"}, "tab_compare":{"fr":"Comparaison","en":"Comparison"},
        "tab_charts":{"fr":"Graphiques","en":"Charts"}, "tab_tables":{"fr":"Tables","en":"Tables"}, "tab_help":{"fr":"Aide","en":"Help"},
        "sec_sky":{"fr":"Niveaux de fond de ciel (e-/pixel/s)","en":"Sky background levels (e-/pixel/s)"},
        "sky_link":{"fr":"Obtenir via SharpCap : https://tools.sharpcap.co.uk/","en":"Obtain via SharpCap: https://tools.sharpcap.co.uk/"},
        "lbl_L":{"fr":"Luminance (L)","en":"Luminance (L)"}, "lbl_RGB":{"fr":"R, G, B","en":"R, G, B"},
        "lbl_NB12":{"fr":"Narrowband 12 nm","en":"Narrowband 12 nm"}, "lbl_NB7":{"fr":"Narrowband 7 nm","en":"Narrowband 7 nm"},
        "lbl_NB3":{"fr":"Narrowband 3 nm (= NB12/4, auto)","en":"Narrowband 3 nm (= NB12/4, auto)"},
        "warn_qe":{"fr":"Prendre la Qe max dans la plage lineaire, pas la Qe max absolue.","en":"Use max Qe in linear range, not absolute max Qe."},
        "sec_sensor":{"fr":"Parametres du capteur","en":"Sensor parameters"},
        "lbl_rn":{"fr":"Read Noise (e- rms)","en":"Read Noise (e- rms)"}, "lbl_ge":{"fr":"Gain (e-/ADU)","en":"Gain (e-/ADU)"},
        "lbl_dc":{"fr":"Dark Current (e-/s/px)","en":"Dark Current (e-/s/px)"}, "lbl_bits":{"fr":"Bits","en":"Bits"}, "lbl_offset":{"fr":"Offset (ADU)","en":"Offset (ADU)"},
        "tip_rn":{"fr":"Depend du gain choisi","en":"Depends on chosen gain"}, "tip_ge":{"fr":"e-/ADU, pas le gain commercial","en":"e-/ADU, not commercial gain"},
        "tip_dc":{"fr":"Depend de la temperature","en":"Depends on cooling temp."},
        "sec_cam":{"fr":"Base de donnees cameras — remplissage auto","en":"Camera database — auto-fill"},
        "lbl_brand":{"fr":"Marque","en":"Brand"}, "lbl_model":{"fr":"Modele","en":"Model"}, "lbl_gain":{"fr":"Gain","en":"Gain"}, "lbl_temp":{"fr":"T refroid.","en":"Cool. temp."},
        "btn_apply":{"fr":"Appliquer","en":"Apply"}, "cam_count":{"fr":"{n} cameras ({s} capteurs)","en":"{n} cameras ({s} sensors)"},
        "a1_title":{"fr":"1ere Approche — Swamp Factor","en":"1st Approach — Swamp Factor"},
        "a1_explain":{"fr":"Le Swamp Factor (SF) est le rapport signal fond de ciel / bruit de lecture. Viser entre 3 et 10.","en":"The Swamp Factor (SF) is sky background signal / read noise ratio. Aim for 3 to 10."},
        "lbl_sf":{"fr":"Swamp Factor souhaite","en":"Desired Swamp Factor"}, "sf_range":{"fr":"Min 3 — Max 10","en":"Min 3 — Max 10"},
        "lbl_median":{"fr":"Valeur mediane de fond de ciel visee (ADU) :","en":"Target sky background median (ADU):"},
        "tip_median1":{"fr":"Sur une brute, selectionner une zone de ciel sans signal et verifier la valeur mediane (Process Statistics dans PixInsight).","en":"On a raw frame, select sky area without signal and check median (Process Statistics in PixInsight)."},
        "tip_median2":{"fr":"Comparer a la cible et ajuster le temps de pose.","en":"Compare to target and adjust exposure time."},
        "a2_title":{"fr":"2e Approche — Temps de pose optimal","en":"2nd Approach — Optimal exposure time"},
        "a2_explain":{"fr":"On accepte un leger surcout en bruit par rapport a une pose unique infiniment longue.","en":"Accept small additional noise cost vs infinitely long single exposure."},
        "lbl_noise_pct":{"fr":"Bruit supplementaire accepte (%)","en":"Accepted additional noise (%)"},
        "lbl_c":{"fr":"Facteur C","en":"C Factor"},
        "lbl_examples":{"fr":"Exemples: 1%->C~50 | 2%->C~25 | 5%->C~10 | 10%->C~4","en":"Examples: 1%->C~50 | 2%->C~25 | 5%->C~10 | 10%->C~4"},
        "sec_opti":{"fr":"Temps de pose unitaire conseille","en":"Recommended sub-exposure time"},
        "col_filter":{"fr":"Filtre","en":"Filter"}, "col_sec":{"fr":"Secondes","en":"Seconds"}, "col_mmss":{"fr":"mm:ss","en":"mm:ss"},
        "tip_opti":{"fr":"Si mediane FDC entre SF x3 et SF x10 = zone optimale.\nSi mediane < SF x3 = augmenter le temps.\nSi mediane trop elevee = possible de reduire.",
                    "en":"If FDC median between SF x3 and SF x10 = optimal zone.\nIf median < SF x3 = increase time.\nIf median too high = can reduce."},
        "sec_gain_long":{"fr":"Bruit additionnel pour un temps donne","en":"Additional noise for a given exposure time"},
        "cmp_title_L":{"fr":"Comparaison 2 strategies en L","en":"Compare 2 strategies in L"},
        "cmp_title_RGB":{"fr":"Comparaison 2 strategies en RGB","en":"Compare 2 strategies in RGB"},
        "lbl_strat1":{"fr":"Strategie 1 (s)","en":"Strategy 1 (s)"}, "lbl_strat2":{"fr":"Strategie 2 (s)","en":"Strategy 2 (s)"},
        "lbl_noise":{"fr":"Bruit add.","en":"Add. noise"}, "lbl_delta":{"fr":"Delta RSB :","en":"Delta SNR:"},
        "ch1_title":{"fr":"Bruit additionnel L / RGB","en":"Additional noise L / RGB"},
        "ch2_title":{"fr":"Bruit additionnel Narrowband","en":"Additional noise Narrowband"},
        "ch_x":{"fr":"Temps de pose (s)","en":"Exposure time (s)"}, "ch_y":{"fr":"Bruit additionnel (%)","en":"Additional noise (%)"},
        "ch_thresh":{"fr":"Seuil accepte","en":"Accepted threshold"},
        "tbl_lrgb":{"fr":"Table — L / RGB","en":"Table — L / RGB"}, "tbl_nb":{"fr":"Table — Narrowband","en":"Table — Narrowband"},
        "tbl_exp":{"fr":"Temps (s)","en":"Time (s)"}, "tbl_thresh":{"fr":"Seuil","en":"Threshold"},
        "help_title":{"fr":"Aide — Theorie et mode d'emploi","en":"Help — Theory and user guide"},
        "update_available":{"fr":"Mise a jour disponible","en":"Update available"},
        "update_restart":{"fr":"La version {v} a ete installee. Redemarrez l'application pour en profiter.","en":"Version {v} has been installed. Restart the application to use it."},
        "update_manual":{"fr":"La version {v} est disponible.\nTelechargez-la depuis :\n{url}","en":"Version {v} is available.\nDownload it from:\n{url}"},
    }
_init_translations()
def tr(key, lang): return T.get(key,{}).get(lang, key)

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
"""

# === CALCULATIONS ===
def additional_noise(t, sky, rn):
    if rn==0 or t<=0 or sky<=0: return 0.0
    r = t*sky/(rn*rn); return math.sqrt((r+1)/r)-1

def c_factor(npct):
    if npct<=0: return float("inf")
    ratio = ((100+npct)/100)**2-1
    return round(1.0/ratio,1) if ratio>0 else float("inf")

def optimal_time(c, rn, sky):
    if sky<=0 or c==float("inf"): return float("inf")
    return math.ceil(c*rn*rn/sky)

def target_median(sf, rn, ge, offset, bits):
    if ge==0: return 0
    return int((sf*rn*rn/ge+offset)*65536/(2**bits))

def sec_to_mmss(s):
    if s is None or s==float("inf") or s<0: return "—"
    m,sec = divmod(int(s),60); return f"{m:02d}:{sec:02d}"

# === THEME ===
CL={"bg":"#0d1117","bg2":"#161b22","card":"#1c2333","border":"#30363d","accent":"#f0883e","accent2":"#58a6ff","red":"#f85149","green":"#3fb950","purple":"#bc8cff","text":"#e6edf3","dim":"#8b949e","input":"#fffbe6","input_fg":"#1c2333","white":"#ffffff"}
TIMES_LRGB=[4,10,20,30,40,50,60,100,200,300,400,500,600,1000,2000]
TIMES_NB=[100,200,300,400,500,600,1000,2000]
FILTERS=[("L","sky_L"),("RGB","sky_RGB"),("NB 12 nm","sky_NB12"),("NB 7 nm","sky_NB7"),("NB 3 nm","sky_NB3")]

# === APP ===
class App:
    def __init__(self, root):
        self.root = root; self.lang = _detect_language()
        self.v_sky_L=tk.DoubleVar(value=1.76); self.v_sky_RGB=tk.DoubleVar(value=1.31)
        self.v_sky_NB12=tk.DoubleVar(value=0.12); self.v_sky_NB7=tk.DoubleVar(value=0.07)
        self.v_rn=tk.DoubleVar(value=1.375); self.v_ge=tk.DoubleVar(value=0.244)
        self.v_dc=tk.DoubleVar(value=0.0017); self.v_bits=tk.IntVar(value=16); self.v_offset=tk.IntVar(value=20)
        self.v_sf=tk.IntVar(value=10); self.v_noise_pct=tk.DoubleVar(value=5.0)
        self.v_exp={"L":tk.IntVar(value=90),"RGB":tk.IntVar(value=90),"NB 12 nm":tk.IntVar(value=180),"NB 7 nm":tk.IntVar(value=300),"NB 3 nm":tk.IntVar(value=300)}
        self.v_cL1=tk.IntVar(value=120); self.v_cL2=tk.IntVar(value=180)
        self.v_cR1=tk.IntVar(value=120); self.v_cR2=tk.IntVar(value=180)
        self.v_brand=tk.StringVar(value="ZWO"); self.v_model=tk.StringVar(); self.v_gain=tk.StringVar(); self.v_temp=tk.StringVar()
        self._rl={}; self._chart_canvas=None; self._recalc_id=None; self._charts_dirty=True; self._chart_tab_idx=4
        for v in [self.v_sky_L,self.v_sky_RGB,self.v_sky_NB12,self.v_sky_NB7,self.v_rn,self.v_ge,self.v_dc,self.v_bits,self.v_offset,self.v_sf,self.v_noise_pct,self.v_cL1,self.v_cL2,self.v_cR1,self.v_cR2]+list(self.v_exp.values()):
            v.trace_add("write", lambda *_: self._sched())
        self._build(); self._recalc()

    def _t(self,k): return tr(k,self.lang)
    @property
    def sky_NB3(self):
        try: return self.v_sky_NB12.get()/4.0
        except: return 0.03
    def _sky(self,k):
        m={"sky_L":self.v_sky_L,"sky_RGB":self.v_sky_RGB,"sky_NB12":self.v_sky_NB12,"sky_NB7":self.v_sky_NB7}
        if k=="sky_NB3": return self.sky_NB3
        try: return m[k].get()
        except: return 0
    def _sched(self):
        if self._recalc_id: self.root.after_cancel(self._recalc_id)
        self._recalc_id = self.root.after(150, self._recalc)
    def _entry(self,p,v,w=10):
        fnt=("Consolas",11,"bold") if platform.system()=="Windows" else ("Menlo",11,"bold")
        return tk.Entry(p,textvariable=v,width=w,font=fnt,bg=CL["input"],fg=CL["input_fg"],relief="flat",bd=0,highlightthickness=2,highlightcolor=CL["accent"],highlightbackground=CL["border"],insertbackground=CL["input_fg"])
    def _lbl(self,p,t,**kw):
        d={"font":("Helvetica",10),"fg":CL["text"],"bg":CL["card"],"anchor":"w"}; d.update(kw); return tk.Label(p,text=t,**d)
    def _card(self,p,t): return tk.LabelFrame(p,text=f"  {t}  ",font=("Helvetica",11,"bold"),fg=CL["accent"],bg=CL["card"],bd=1,relief="solid",highlightbackground=CL["border"],highlightthickness=1,padx=12,pady=10)
    def _scrollable(self,p):
        c=tk.Canvas(p,bg=CL["bg"],highlightthickness=0,bd=0); sb=ttk.Scrollbar(p,orient="vertical",command=c.yview)
        inner=tk.Frame(c,bg=CL["bg"]); inner.bind("<Configure>",lambda e:c.configure(scrollregion=c.bbox("all")))
        c.create_window((0,0),window=inner,anchor="nw",tags="inner"); c.configure(yscrollcommand=sb.set)
        c.bind("<Configure>",lambda e:c.itemconfig("inner",width=e.width))
        def w(e):
            d=-1*e.delta if platform.system()=="Darwin" else int(-1*(e.delta/120))
            c.yview_scroll(d,"units")
        c.bind("<MouseWheel>",w); inner.bind("<MouseWheel>",w)
        def ba(ww): ww.bind("<MouseWheel>",w);[ba(ch) for ch in ww.winfo_children()]
        inner.bind("<Map>",lambda e:ba(inner)); c.pack(side="left",fill="both",expand=True); sb.pack(side="right",fill="y")
        return inner

    def _build(self):
        r=self.root; r.title(self._t("win_title")); r.configure(bg=CL["bg"])
        # Adaptive window: 85% of screen
        sw,sh=r.winfo_screenwidth(),r.winfo_screenheight()
        ww=max(1200,min(int(sw*0.85),1600)); wh=max(800,min(int(sh*0.85),1000))
        r.geometry(f"{ww}x{wh}+{(sw-ww)//2}+{max(0,(sh-wh)//2-30)}"); r.minsize(1100,750)
        sty=ttk.Style(); sty.theme_use("clam")
        sty.configure("TNotebook",background=CL["bg"],borderwidth=0,tabmargins=[2,5,2,0])
        sty.configure("TNotebook.Tab",background=CL["bg2"],foreground=CL["dim"],padding=[14,6],font=("Helvetica",10,"bold"))
        sty.map("TNotebook.Tab",background=[("selected",CL["card"])],foreground=[("selected",CL["accent"])])
        # Top bar with grid layout so buttons never clip
        top=tk.Frame(r,bg=CL["bg2"],pady=5); top.pack(fill="x"); top.columnconfigure(1,weight=1)
        tk.Label(top,text="  ",font=("Helvetica",18),bg=CL["bg2"],fg=CL["accent"]).grid(row=0,column=0,padx=(10,2))
        tk.Label(top,text=self._t("win_title"),font=("Helvetica",12,"bold"),fg=CL["accent"],bg=CL["bg2"]).grid(row=0,column=1,sticky="w",padx=4)
        bf=tk.Frame(top,bg=CL["bg2"]); bf.grid(row=0,column=2,padx=8,sticky="e")
        for txt,cmd,bg in [(self._t("recalc"),self._recalc,CL["green"]),(self._t("export"),self._export,CL["accent2"]),(self._t("lang_btn"),self._toggle_lang,CL["purple"])]:
            tk.Button(bf,text=txt,command=cmd,font=("Helvetica",9,"bold"),bg=bg,fg=CL["bg"],activebackground=bg,activeforeground=CL["white"],relief="flat",padx=10,pady=2,cursor="hand2",bd=0).pack(side="left",padx=3)
        tk.Label(r,text=self._t("fill_yellow"),font=("Helvetica",9),bg=CL["accent"],fg=CL["bg"],pady=2).pack(fill="x")
        self.nb=ttk.Notebook(r); self.nb.pack(fill="both",expand=True,padx=6,pady=(3,6))
        for key,builder in [("tab_params",self._bp),("tab_a1",self._b1),("tab_a2",self._b2),("tab_compare",self._bc),("tab_charts",self._bch),("tab_tables",self._bt),("tab_help",self._bh)]:
            f=tk.Frame(self.nb,bg=CL["bg"]); self.nb.add(f,text=f" {self._t(key)} ",padding=2); builder(f)
        self.nb.bind("<<NotebookTabChanged>>", self._on_tab_changed)

    def _bp(self,p):
        inner=self._scrollable(p); inner.columnconfigure(0,weight=1,uniform="h"); inner.columnconfigure(1,weight=1,uniform="h")
        cs=self._card(inner,self._t("sec_sky")); cs.grid(row=0,column=0,sticky="new",padx=6,pady=6)
        lnk=tk.Label(cs,text=self._t("sky_link"),font=("Helvetica",9,"underline"),fg=CL["accent2"],bg=CL["card"],cursor="hand2")
        lnk.grid(row=0,column=0,columnspan=3,sticky="w",pady=(0,6)); lnk.bind("<Button-1>",lambda e:webbrowser.open("https://tools.sharpcap.co.uk/"))
        for i,(lk,var) in enumerate([("lbl_L",self.v_sky_L),("lbl_RGB",self.v_sky_RGB),("lbl_NB12",self.v_sky_NB12),("lbl_NB7",self.v_sky_NB7)],1):
            self._lbl(cs,self._t(lk)).grid(row=i,column=0,sticky="w",pady=3); self._entry(cs,var,10).grid(row=i,column=1,sticky="w",padx=8,pady=3)
        self._lbl(cs,self._t("lbl_NB3"),fg=CL["dim"],font=("Helvetica",9,"italic")).grid(row=6,column=0,sticky="w",pady=3)
        self._r_nb3=self._lbl(cs,"0.030",fg=CL["green"],font=("Consolas",11,"bold")); self._r_nb3.grid(row=6,column=1,sticky="w",padx=8)
        self._lbl(cs,self._t("warn_qe"),fg=CL["red"],font=("Helvetica",8,"italic"),wraplength=350,justify="left").grid(row=7,column=0,columnspan=3,sticky="w",pady=(6,0))
        cp=self._card(inner,self._t("sec_sensor")); cp.grid(row=0,column=1,sticky="new",padx=6,pady=6)
        for i,(lk,var,tip) in enumerate([("lbl_rn",self.v_rn,"tip_rn"),("lbl_ge",self.v_ge,"tip_ge"),("lbl_dc",self.v_dc,"tip_dc"),("lbl_bits",self.v_bits,None),("lbl_offset",self.v_offset,None)]):
            self._lbl(cp,self._t(lk)).grid(row=i,column=0,sticky="w",pady=3); self._entry(cp,var,10).grid(row=i,column=1,sticky="w",padx=8,pady=3)
            if tip: self._lbl(cp,self._t(tip),font=("Helvetica",8,"italic"),fg=CL["dim"]).grid(row=i,column=2,sticky="w")
        cc=self._card(inner,self._t("sec_cam")); cc.grid(row=1,column=0,columnspan=2,sticky="new",padx=6,pady=6)
        nc=sum(len(m) for m in CAMERA_DB.values())
        self._lbl(cc,self._t("cam_count").format(n=nc,s=len(_SENSORS)),fg=CL["dim"],font=("Helvetica",9,"italic")).pack(anchor="w",pady=(0,6))
        rf=tk.Frame(cc,bg=CL["card"]); rf.pack(fill="x")
        self._combos={}
        for i,(lk,var,vals,cmd) in enumerate([("lbl_brand",self.v_brand,list(CAMERA_DB.keys()),self._ob),("lbl_model",self.v_model,[],self._om),("lbl_gain",self.v_gain,[],None),("lbl_temp",self.v_temp,[],None)]):
            self._lbl(rf,self._t(lk)).grid(row=0,column=i*2,padx=(8,3),pady=6)
            w=22 if lk=="lbl_model" else 16
            cb=ttk.Combobox(rf,textvariable=var,values=vals,width=w,state="readonly",font=("Helvetica",9))
            cb.grid(row=0,column=i*2+1,padx=(0,8),pady=6)
            if cmd: cb.bind("<<ComboboxSelected>>",cmd)
            self._combos[lk]=cb
        tk.Button(rf,text=self._t("btn_apply"),command=self._ac,font=("Helvetica",10,"bold"),bg=CL["accent"],fg=CL["bg"],relief="flat",padx=14,pady=4,cursor="hand2",bd=0).grid(row=0,column=8,padx=10,pady=6)
        self._lbl_ci=self._lbl(cc,"",fg=CL["green"],font=("Helvetica",9,"italic")); self._lbl_ci.pack(anchor="w",padx=5,pady=(2,0))
        self._ob()

    def _b1(self,p):
        inner=self._scrollable(p); inner.columnconfigure(0,weight=1)
        tk.Label(inner,text=self._t("a1_title"),font=("Helvetica",13,"bold"),fg=CL["accent"],bg=CL["bg"]).grid(row=0,column=0,pady=(10,2),sticky="w",padx=15)
        tk.Label(inner,text=self._t("a1_explain"),font=("Helvetica",9),fg=CL["dim"],bg=CL["bg"],wraplength=900,justify="left").grid(row=1,column=0,sticky="w",padx=15,pady=(0,8))
        card=self._card(inner,self._t("lbl_sf")); card.grid(row=2,column=0,sticky="new",padx=10,pady=6)
        sf_r=tk.Frame(card,bg=CL["card"]); sf_r.pack(fill="x",pady=5)
        self._lbl(sf_r,self._t("lbl_sf")+" :").pack(side="left",padx=5); self._entry(sf_r,self.v_sf,6).pack(side="left",padx=5)
        self._lbl(sf_r,self._t("sf_range"),fg=CL["dim"],font=("Helvetica",9,"italic")).pack(side="left",padx=15)
        tk.Label(card,text=self._t("lbl_median"),font=("Helvetica",11,"bold"),fg=CL["text"],bg=CL["card"]).pack(anchor="w",padx=5,pady=(12,5))
        res=tk.Frame(card,bg=CL["card"]); res.pack(fill="x",padx=5)
        self._r_sf={}
        for lb,co in [("SF x3",CL["accent2"]),("SF xN",CL["accent"]),("SF x10",CL["green"])]:
            f=tk.Frame(res,bg=CL["bg2"],padx=20,pady=8,highlightbackground=CL["border"],highlightthickness=1); f.pack(side="left",padx=8,pady=5)
            tk.Label(f,text=lb,font=("Helvetica",10,"bold"),fg=co,bg=CL["bg2"]).pack()
            l=tk.Label(f,text="--",font=("Consolas",22,"bold"),fg=CL["white"],bg=CL["bg2"]); l.pack(); self._r_sf[lb]=l
        for k in ["tip_median1","tip_median2"]:
            tk.Label(card,text=self._t(k),font=("Helvetica",9),fg=CL["dim"],bg=CL["card"],justify="left",wraplength=800).pack(anchor="w",padx=5,pady=1)

    def _b2(self,p):
        inner=self._scrollable(p); inner.columnconfigure(0,weight=1)
        tk.Label(inner,text=self._t("a2_title"),font=("Helvetica",13,"bold"),fg=CL["accent"],bg=CL["bg"]).grid(row=0,column=0,pady=(10,2),sticky="w",padx=15)
        tk.Label(inner,text=self._t("a2_explain"),font=("Helvetica",9),fg=CL["dim"],bg=CL["bg"],wraplength=900,justify="left").grid(row=1,column=0,sticky="w",padx=15,pady=(0,8))
        c1=self._card(inner,self._t("lbl_noise_pct")); c1.grid(row=2,column=0,sticky="new",padx=10,pady=6)
        r1=tk.Frame(c1,bg=CL["card"]); r1.pack(fill="x",pady=4)
        self._lbl(r1,self._t("lbl_noise_pct")+" :").pack(side="left",padx=5); self._entry(r1,self.v_noise_pct,6).pack(side="left",padx=5)
        self._lbl(r1,"%",font=("Helvetica",11,"bold")).pack(side="left")
        self._lbl(r1,"|",fg=CL["border"],font=("Helvetica",14)).pack(side="left",padx=15)
        self._lbl(r1,self._t("lbl_c")+" :").pack(side="left",padx=5)
        self._r_c=self._lbl(r1,"--",fg=CL["green"],font=("Consolas",14,"bold")); self._r_c.pack(side="left",padx=5)
        tk.Label(c1,text=self._t("lbl_examples"),font=("Helvetica",9,"italic"),fg=CL["dim"],bg=CL["card"]).pack(anchor="w",padx=5,pady=(2,0))
        c2=self._card(inner,self._t("sec_opti")); c2.grid(row=3,column=0,sticky="new",padx=10,pady=6)
        hdr=tk.Frame(c2,bg=CL["card"]); hdr.pack(fill="x")
        for t,w in [(self._t("col_filter"),12),(self._t("col_sec"),10),(self._t("col_mmss"),10)]:
            tk.Label(hdr,text=t,font=("Helvetica",10,"bold"),fg=CL["accent2"],bg=CL["card"],width=w).pack(side="left",padx=10)
        self._r_opti={}
        for fn,_ in FILTERS:
            row=tk.Frame(c2,bg=CL["card"]); row.pack(fill="x",pady=1)
            tk.Label(row,text=fn,font=("Helvetica",10),fg=CL["text"],bg=CL["card"],width=12,anchor="w").pack(side="left",padx=10)
            ls=tk.Label(row,text="--",font=("Consolas",12,"bold"),fg=CL["green"],bg=CL["card"],width=10); ls.pack(side="left",padx=10)
            lm=tk.Label(row,text="--",font=("Consolas",12),fg=CL["dim"],bg=CL["card"],width=10); lm.pack(side="left",padx=10)
            self._r_opti[fn]=(ls,lm)
        tk.Label(c2,text=self._t("tip_opti"),font=("Helvetica",9),fg=CL["dim"],bg=CL["card"],justify="left").pack(anchor="w",padx=10,pady=(8,0))
        c3=self._card(inner,self._t("sec_gain_long")); c3.grid(row=4,column=0,sticky="new",padx=10,pady=6)
        self._r_gl={}
        for fn,_ in FILTERS:
            row=tk.Frame(c3,bg=CL["card"]); row.pack(fill="x",pady=2)
            tk.Label(row,text=fn,font=("Helvetica",10),fg=CL["text"],bg=CL["card"],width=12,anchor="w").pack(side="left",padx=10)
            self._entry(row,self.v_exp[fn],8).pack(side="left",padx=5); self._lbl(row,"s").pack(side="left")
            self._lbl(row,"->",fg=CL["dim"]).pack(side="left",padx=10)
            lr=self._lbl(row,"--",fg=CL["accent"],font=("Consolas",12,"bold")); lr.pack(side="left",padx=5); self._r_gl[fn]=lr

    def _bc(self,p):
        p.columnconfigure(0,weight=1,uniform="c"); p.columnconfigure(1,weight=1,uniform="c")
        for col,(tk_k,sk,v1,v2,dk) in enumerate([("cmp_title_L","sky_L",self.v_cL1,self.v_cL2,"dL"),("cmp_title_RGB","sky_RGB",self.v_cR1,self.v_cR2,"dR")]):
            card=self._card(p,self._t(tk_k)); card.grid(row=0,column=col,sticky="nsew",padx=8,pady=10)
            for lk,var,nk in [("lbl_strat1",v1,f"n{dk}1"),("lbl_strat2",v2,f"n{dk}2")]:
                rf=tk.Frame(card,bg=CL["card"]); rf.pack(fill="x",pady=4)
                self._lbl(rf,self._t(lk)+" :").pack(side="left",padx=5); self._entry(rf,var,8).pack(side="left",padx=5)
                self._lbl(rf,"s").pack(side="left"); self._lbl(rf,"|",fg=CL["border"],font=("Helvetica",14)).pack(side="left",padx=10)
                self._lbl(rf,self._t("lbl_noise")+" :").pack(side="left",padx=5)
                nl=self._lbl(rf,"--",fg=CL["accent2"],font=("Consolas",11,"bold")); nl.pack(side="left",padx=5); self._rl[nk]=nl
            tk.Frame(card,bg=CL["border"],height=1).pack(fill="x",padx=5,pady=8)
            df=tk.Frame(card,bg=CL["card"]); df.pack(fill="x",pady=4)
            self._lbl(df,self._t("lbl_delta"),font=("Helvetica",12,"bold"),fg=CL["accent"]).pack(side="left",padx=10)
            dl=tk.Label(df,text="--",font=("Consolas",18,"bold"),fg=CL["green"],bg=CL["card"]); dl.pack(side="left",padx=10); self._rl[dk]=dl

    def _bch(self,p):
        # Inner container with propagate OFF — matplotlib can never push parent bigger
        self._chart_box=tk.Frame(p,bg=CL["bg"])
        self._chart_box.pack(fill="both",expand=True)
        self._chart_box.pack_propagate(False)
        self._resize_id=None; self._chart_drawn_size=(0,0)
        def _on_resize(e):
            try:
                if self.nb.index(self.nb.select())!=self._chart_tab_idx: return
            except: return
            if self._resize_id: self.root.after_cancel(self._resize_id)
            self._resize_id=self.root.after(200, self._redraw_if_size_changed)
        p.bind("<Configure>",_on_resize)
    def _on_tab_changed(self,event=None):
        try:
            idx=self.nb.index(self.nb.select())
            if idx==self._chart_tab_idx and self._charts_dirty:
                self.root.after(80, self._draw_charts_now)
        except: pass
    def _redraw_if_size_changed(self):
        self._chart_box.update_idletasks()
        w,h=self._chart_box.winfo_width(),self._chart_box.winfo_height()
        if w<50 or h<50: return
        if (w,h)!=self._chart_drawn_size:
            self._charts_dirty=True; self._draw_charts_now()
    def _draw_charts_now(self):
        self._chart_box.update_idletasks()
        # Lire les dimensions AVANT de détruire les enfants (sinon winfo peut renvoyer des valeurs fausses après ~0.1s)
        try:
            box_w = self._chart_box.winfo_width()
            box_h = self._chart_box.winfo_height()
            parent = self._chart_box.master
            max_w = parent.winfo_width() if parent else box_w
            max_h = parent.winfo_height() if parent else box_h
        except Exception:
            box_w = box_h = 400
            max_w = max_h = 400
        fw = min(box_w, max_w) if max_w > 50 else box_w
        fh = min(box_h, max_h) if max_h > 50 else box_h
        if fw < 50 or fh < 50:
            for w in self._chart_box.winfo_children(): w.destroy()
            return
        for w in self._chart_box.winfo_children(): w.destroy()
        rn=self.v_rn.get(); thr=self.v_noise_pct.get()/100
        dpi=100
        # Taille en pixels strictement inférieure au conteneur (marge 3%) pour éviter tout débordement
        margin = 0.03
        fig_w_px = max(100, int(fw * (1 - margin)))
        max_h_ratio = 0.52
        fig_h_px = max(80, int(min(fh * (1 - margin), fig_w_px * max_h_ratio)))
        fig_w_in = fig_w_px / dpi
        fig_h_in = fig_h_px / dpi
        fig=Figure(figsize=(fig_w_in, fig_h_in),dpi=dpi,facecolor=CL["bg"])
        fig.set_tight_layout(True)
        for idx,(times,skies,colors,names,tk_k) in enumerate([
            (TIMES_LRGB,[self._sky("sky_L"),self._sky("sky_RGB")],[CL["red"],CL["accent"]],["L","RGB"],"ch1_title"),
            (TIMES_NB,[self._sky("sky_NB12"),self._sky("sky_NB7"),self.sky_NB3],[CL["red"],CL["accent"],CL["accent2"]],["NB12","NB7","NB3"],"ch2_title")]):
            ax=fig.add_subplot(1,2,idx+1); ax.set_facecolor(CL["bg2"]); allv=[]
            for sky,co,nm in zip(skies,colors,names):
                v=[additional_noise(t,sky,rn)*100 for t in times]; allv.extend(v)
                ax.plot(times,v,"o-",color=co,label=nm,linewidth=2,markersize=4)
            ax.axhline(y=thr*100,color=CL["green"],linestyle="--",linewidth=1.5,label=self._t("ch_thresh"))
            ymax=max(max(allv) if allv else 1, thr*100)*1.15; ax.set_ylim(0,ymax)
            ax.set_xlabel(self._t("ch_x"),color=CL["text"],fontsize=9); ax.set_ylabel(self._t("ch_y"),color=CL["text"],fontsize=9)
            ax.set_title(self._t(tk_k),color=CL["accent"],fontsize=11,fontweight="bold")
            ax.legend(fontsize=8,facecolor=CL["bg2"],edgecolor=CL["border"],labelcolor=CL["text"])
            ax.tick_params(colors=CL["dim"],labelsize=8); ax.grid(True,alpha=0.15,color=CL["dim"])
            for sp in ax.spines.values(): sp.set_color(CL["border"])
        c=FigureCanvasTkAgg(fig,master=self._chart_box); c.draw()
        cw=c.get_tk_widget()
        cw.config(width=fig_w_px, height=fig_h_px)
        cw.pack(anchor="nw")
        self._charts_dirty=False; self._chart_drawn_size=(fw,fh)

    def _bt(self,p):
        self._tbl_frame=self._scrollable(p); self._tbl_frame.columnconfigure(0,weight=1)
    def _update_tables(self):
        for w in self._tbl_frame.winfo_children(): w.destroy()
        rn=self.v_rn.get(); thr=self.v_noise_pct.get()/100
        for tk_k,times,series in [("tbl_lrgb",TIMES_LRGB,[("L",[additional_noise(t,self._sky("sky_L"),rn) for t in TIMES_LRGB]),("RGB",[additional_noise(t,self._sky("sky_RGB"),rn) for t in TIMES_LRGB])]),
            ("tbl_nb",TIMES_NB,[("NB12",[additional_noise(t,self._sky("sky_NB12"),rn) for t in TIMES_NB]),("NB7",[additional_noise(t,self._sky("sky_NB7"),rn) for t in TIMES_NB]),("NB3",[additional_noise(t,self.sky_NB3,rn) for t in TIMES_NB])])]:
            card=self._card(self._tbl_frame,self._t(tk_k)); card.pack(fill="x",padx=8,pady=6)
            hdr=tk.Frame(card,bg=CL["bg2"]); hdr.pack(fill="x")
            tk.Label(hdr,text=self._t("tbl_exp"),font=("Helvetica",9,"bold"),fg=CL["accent2"],bg=CL["bg2"],width=10).pack(side="left",padx=2)
            for t in times: tk.Label(hdr,text=str(t),font=("Consolas",9,"bold"),fg=CL["accent2"],bg=CL["bg2"],width=7).pack(side="left",padx=1)
            for nm,vals in series:
                row=tk.Frame(card,bg=CL["card"]); row.pack(fill="x")
                tk.Label(row,text=nm,font=("Helvetica",9,"bold"),fg=CL["text"],bg=CL["card"],width=10,anchor="w").pack(side="left",padx=2)
                for v in vals:
                    fg=CL["green"] if v<=thr else CL["red"]
                    tk.Label(row,text=f"{v*100:.1f}%",font=("Consolas",9),fg=fg,bg=CL["card"],width=7).pack(side="left",padx=1)
            thr_r=tk.Frame(card,bg=CL["bg2"]); thr_r.pack(fill="x")
            tk.Label(thr_r,text=self._t("tbl_thresh"),font=("Helvetica",9,"italic"),fg=CL["green"],bg=CL["bg2"],width=10,anchor="w").pack(side="left",padx=2)
            for _ in times: tk.Label(thr_r,text=f"{thr*100:.0f}%",font=("Consolas",9,"italic"),fg=CL["green"],bg=CL["bg2"],width=7).pack(side="left",padx=1)

    def _bh(self,p):
        tk.Label(p,text=self._t("help_title"),font=("Helvetica",13,"bold"),fg=CL["accent"],bg=CL["bg"]).pack(pady=(10,5))
        fnt=("Consolas",10) if platform.system()=="Windows" else ("Menlo",10)
        t=tk.Text(p,wrap="word",font=fnt,bg=CL["bg2"],fg=CL["text"],relief="flat",padx=25,pady=15,highlightthickness=0,bd=0,insertbackground=CL["text"])
        t.pack(fill="both",expand=True,padx=10,pady=(0,8))
        t.insert("1.0",HELP_FR if self.lang=="fr" else HELP_EN); t.configure(state="disabled")

    # Camera selection
    def _ob(self,e=None):
        ms=list(CAMERA_DB.get(self.v_brand.get(),{}).keys()); self._combos["lbl_model"]["values"]=ms
        if ms: self.v_model.set(ms[0]); self._om()
    def _om(self,e=None):
        cam=CAMERA_DB.get(self.v_brand.get(),{}).get(self.v_model.get())
        if not cam: return
        gs=list(cam["gains"].keys()); self._combos["lbl_gain"]["values"]=gs
        if gs: self.v_gain.set(gs[0])
        ts=[str(t) for t in cam["temps"].keys()]; self._combos["lbl_temp"]["values"]=ts
        if ts: self.v_temp.set(ts[0])
    def _ac(self):
        cam=CAMERA_DB.get(self.v_brand.get(),{}).get(self.v_model.get())
        if not cam: return
        gk=self.v_gain.get()
        if gk in cam["gains"]:
            g=cam["gains"][gk]; self.v_rn.set(g["rn"]); self.v_ge.set(g["ge"]); self.v_offset.set(g.get("offset",20))
        self.v_bits.set(cam["bits"])
        for k,v in cam["temps"].items():
            if str(k)==self.v_temp.get(): self.v_dc.set(v); break
        self._lbl_ci.config(text=f"  {self.v_brand.get()} {self.v_model.get()} | {gk} | T={self.v_temp.get()}C | RN={self.v_rn.get()} Gain={self.v_ge.get()} e-/ADU Dc={self.v_dc.get()} {cam['bits']}bit Off={self.v_offset.get()}")
        self._recalc()

    def _recalc(self,*_):
        try: rn=self.v_rn.get();ge=self.v_ge.get();bits=self.v_bits.get();off=self.v_offset.get();sf=self.v_sf.get();npct=self.v_noise_pct.get()
        except: return
        if rn<=0 or ge<=0: return
        try: self._r_nb3.config(text=f"{self.sky_NB3:.4f}")
        except: pass
        try:
            self._r_sf["SF x3"].config(text=str(target_median(3,rn,ge,off,bits)))
            self._r_sf["SF xN"].config(text=str(target_median(sf,rn,ge,off,bits)))
            self._r_sf["SF x10"].config(text=str(target_median(10,rn,ge,off,bits)))
        except: pass
        try:
            cf=c_factor(npct); self._r_c.config(text=f"{cf:.1f}" if cf<1e6 else "inf")
            for fn,sk in FILTERS:
                t=optimal_time(cf,rn,self._sky(sk)); ls,lm=self._r_opti[fn]
                if t==float("inf"): ls.config(text="inf"); lm.config(text="--")
                else: ls.config(text=f"{t} s"); lm.config(text=sec_to_mmss(t))
        except: pass
        try:
            for fn,sk in FILTERS:
                n=additional_noise(self.v_exp[fn].get(),self._sky(sk),rn); self._r_gl[fn].config(text=f"{n*100:.2f} %")
        except: pass
        try:
            sL,sR=self._sky("sky_L"),self._sky("sky_RGB")
            n1=additional_noise(self.v_cL1.get(),sL,rn); n2=additional_noise(self.v_cL2.get(),sL,rn)
            self._rl["ndL1"].config(text=f"{n1*100:.3f}%"); self._rl["ndL2"].config(text=f"{n2*100:.3f}%"); self._rl["dL"].config(text=f"{(n2-n1)*100:+.4f}%")
            n1=additional_noise(self.v_cR1.get(),sR,rn); n2=additional_noise(self.v_cR2.get(),sR,rn)
            self._rl["ndR1"].config(text=f"{n1*100:.3f}%"); self._rl["ndR2"].config(text=f"{n2*100:.3f}%"); self._rl["dR"].config(text=f"{(n2-n1)*100:+.4f}%")
        except: pass
        self._charts_dirty=True
        try:
            idx=self.nb.index(self.nb.select())
            if idx==self._chart_tab_idx: self.root.after(80, self._draw_charts_now)
        except: pass
        try: self._update_tables()
        except: pass

    def _toggle_lang(self):
        self.lang="en" if self.lang=="fr" else "fr"
        for w in self.root.winfo_children(): w.destroy()
        self._rl={}; self._chart_canvas=None; self._charts_dirty=True; self._build(); self._recalc()

    def _export(self):
        try:
            rn,ge,bits,off=self.v_rn.get(),self.v_ge.get(),self.v_bits.get(),self.v_offset.get()
            npct=self.v_noise_pct.get(); cf=c_factor(npct)
            data={"parameters":{"sky_L":self.v_sky_L.get(),"sky_RGB":self.v_sky_RGB.get(),"sky_NB12":self.v_sky_NB12.get(),"sky_NB7":self.v_sky_NB7.get(),"sky_NB3":self.sky_NB3,"rn":rn,"ge":ge,"dc":self.v_dc.get(),"bits":bits,"offset":off},
                  "approach1":{"sf":self.v_sf.get(),"median_SF3":target_median(3,rn,ge,off,bits),"median_SF10":target_median(10,rn,ge,off,bits)},
                  "approach2":{"noise_pct":npct,"c_factor":cf,"times":{fn:optimal_time(cf,rn,self._sky(sk)) for fn,sk in FILTERS}}}
            path=filedialog.asksaveasfilename(defaultextension=".json",filetypes=[("JSON","*.json")],initialfile="exposure_results.json")
            if path:
                with open(path,"w",encoding="utf-8") as f: json.dump(data,f,indent=2,ensure_ascii=False,default=str)
                messagebox.showinfo("Export",f"{'Exporte' if self.lang=='fr' else 'Exported'}!\n{path}")
        except Exception as e: messagebox.showerror("Error",str(e))

def _create_shortcut():
    s=os.path.abspath(__file__); n="ExposureCalculator"
    if platform.system()=="Windows":
        try: (Path.home()/"Desktop"/f"{n}.bat").write_text(f'@echo off\npythonw "{s}"\n',encoding="utf-8")
        except: pass
    elif platform.system()=="Darwin":
        try: d=Path.home()/"Applications"/f"{n}.app"/"Contents"/"MacOS"; d.mkdir(parents=True,exist_ok=True); l=d/n; l.write_text(f'#!/bin/bash\npython3 "{s}"\n',encoding="utf-8"); os.chmod(str(l),0o755)
        except: pass
    else:
        try:
            d=Path.home()/".local"/"share"/"applications"; d.mkdir(parents=True,exist_ok=True)
            (d/f"{n.lower()}.desktop").write_text(f"[Desktop Entry]\nType=Application\nName={n}\nExec=python3 {s}\nTerminal=false\nCategories=Science;\n",encoding="utf-8")
        except: pass

_UPDATE_URL = "https://raw.githubusercontent.com/NGC4565/ExposureCalculator/main/ExposureCalculator.py"
_REPO_URL = "https://github.com/NGC4565/ExposureCalculator"

def _parse_version(v):
    try: return tuple(int(x) for x in v.strip().split("."))
    except: return (0,)

def _check_for_update(root, lang):
    def _worker():
        try:
            from urllib.request import urlopen, Request
            req = Request(_UPDATE_URL, headers={"User-Agent": "ExposureCalculator"})
            data = urlopen(req, timeout=10).read(2048).decode("utf-8", errors="ignore")
            remote_ver = None
            for line in data.splitlines():
                if line.startswith("__version__"):
                    remote_ver = line.split("=")[1].strip().strip('"').strip("'")
                    break
            if not remote_ver:
                return
            if _parse_version(remote_ver) <= _parse_version(__version__):
                return
            has_git = os.path.isdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".git"))
            git_ok = False
            if has_git:
                try:
                    cwd = os.path.dirname(os.path.abspath(__file__))
                    subprocess.check_call(["git", "fetch", "origin", "main"], cwd=cwd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    subprocess.check_call(["git", "reset", "--hard", "origin/main"], cwd=cwd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    git_ok = True
                except Exception:
                    pass
            def _notify():
                from tkinter import messagebox
                title = tr("update_available", lang)
                if git_ok:
                    msg = tr("update_restart", lang).format(v=remote_ver)
                else:
                    msg = tr("update_manual", lang).format(v=remote_ver, url=_REPO_URL)
                messagebox.showinfo(title, msg)
            root.after(0, _notify)
        except Exception:
            pass
    t = threading.Thread(target=_worker, daemon=True)
    t.start()

def main():
    if platform.system()=="Windows":
        try:
            from ctypes import windll; windll.shcore.SetProcessDpiAwareness(1)
        except: pass
    root=tk.Tk(); app=App(root)
    _check_for_update(root, app.lang)
    m=Path.home()/".exposure_calc_installed"
    if not m.exists():
        try: _create_shortcut(); m.touch()
        except: pass
    root.mainloop()

if __name__=="__main__": main()
