# 🌌 Exposure Time Calculator

[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)]()
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg)]()

**Ideal sub-exposure time calculator for astrophotography** — helps you choose optimal exposure times for deep-sky imaging based on sky background, sensor parameters, and proven mathematical models.

> This application is based on the original Excel spreadsheet created by **Benoit Saintot**.

---

## ✨ Features

- **Two complementary approaches**  
  - **Swamp Factor** (SF 3–10): target sky background median (ADU)  
  - **Optimal time**: recommended sub-exposure per filter for an accepted additional noise %

- **Camera database** — 40+ models (ZWO, QHY, Moravian, ATIK, Player One, ToupTek) with auto-fill of Read Noise, Gain, Dark Current, etc.

- **Multi-filter support** — L, RGB, Narrowband 12 nm, 7 nm, 3 nm (NB3 = NB12/4, automatic)

- **Interactive tools** — Comparison of two strategies, charts, tables, JSON export

- **Bilingual** — Auto-detected English / Français; switch with one click

- **Zero-config install** — Run scripts auto-install Python and dependencies if missing

---

## 🚀 Quick start

### Windows
1. Double-click `run.bat`
2. If Python is missing, the script will try to install it via **winget** (Windows Package Manager)
3. If winget is missing, you’ll be guided to install it, then run `run.bat` again

### Linux
```bash
chmod +x run.sh
./run.sh
```
Python 3 + tkinter will be installed automatically via your package manager if needed.

### macOS
```bash
chmod +x run.sh
./run.sh
```
Python will be installed via Homebrew if missing.

---

## 📋 Requirements

- **Python 3.7+** (with tkinter; usually bundled with Python on Windows/Linux)
- **matplotlib** — installed automatically on first run

---

## 📖 Usage

1. **Parameters** — Enter sky background levels (e.g. from [SharpCap](https://tools.sharpcap.co.uk/)) and sensor data, or select a camera from the database.
2. **Swamp Factor** — Set desired SF (3–10), read target medians (SF×3, SF×N, SF×10).
3. **Optimal Time** — Set accepted additional noise (%), read recommended times per filter.
4. **Comparison** — Compare two exposure strategies in L and RGB.
5. **Charts & Tables** — Visualize noise vs. exposure time.

Only the yellow input fields need to be edited; results update automatically.

---

## 📂 Project structure

```
exposure calculator/
├── ExposureCalculator.py   # Main application
├── run.bat                 # Windows launcher (auto-install Python & winget)
├── run.sh                  # Linux/macOS launcher (auto-install Python)
├── README.md               # This file
├── README.txt              # Detailed user guide
├── GITHUB_PUBLISH_GUIDE.md # Guide to publish on GitHub (GitHub Desktop)
└── manual/                 # LaTeX theory & user manual
    └── ExposureCalculator_Manual.tex
```

---

## 🔬 Theory (summary)

**Noise sources:** useful signal + sky background + read noise + dark current + photon noise.

**Total noise:** σ = √(RN² + DC·t + Sky·t)  
**SNR when stacking N subs:** SNR = Signal × √N / σ

**Swamp Factor:** SF = (Sky × t) / RN²  
- SF &lt; 3: read noise dominates → increase exposure  
- 3 ≤ SF ≤ 10: optimal zone  
- SF &gt; 10: diminishing returns  

**Additional noise (2nd approach):**  
Add_noise = √((T×Sky/RN² + 1) / (T×Sky/RN²)) − 1  
C = 1 / ((1 + %noise/100)² − 1)  
T_optimal = ceil(C × RN² / Sky)

See the LaTeX manual for full theory and formulas.

---

## 📄 Export

Click **Export** to save parameters and results to JSON:

- `parameters`: sky levels, read noise, gain, dark current, bits, offset  
- `approach1`: swamp factor, medians at SF×3 and SF×10  
- `approach2`: noise %, C factor, optimal times per filter  

---

## 🙏 Credits

- **Theory & original spreadsheet:** © Benoit Saintot  
- **GUI & Python application:** NGC4565  
- **Version:** 1.00  

---

## 📜 License

Use and share with attribution as above.
