# Exposure Time Calculator

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)]()
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg)]()

**Ideal sub-exposure time calculator for astrophotography** — helps you choose optimal exposure times for deep-sky imaging based on sky background, sensor parameters, and proven mathematical models.

> This application is based on the original Excel spreadsheet created by **Benoit Saintot**.

---

## Features

### Calculation

- **Two complementary approaches**
  - **Swamp Factor** (SF 3-10): target sky background median (ADU)
  - **Optimal time**: recommended sub-exposure per filter for an accepted additional noise %

- **Camera database** — 40+ models (ZWO, QHY, Moravian, ATIK, Player One, ToupTek) with auto-fill of Read Noise, Gain, Dark Current, etc.

- **Multi-filter support** — L, RGB, Narrowband 12 nm, 7 nm, 3 nm (NB3 = NB12/4, automatic)

- **Interactive tools** — Comparison of two strategies, charts, tables, JSON export/import

### Interface

- **Modern PyQt6 GUI** — dark-themed tabbed interface (migrated from tkinter in v2.0.0)

- **Bilingual** — Auto-detected English / Francais; switch with one click

- **Settings persistence** — All parameters auto-saved and restored on next launch; import/export settings as JSON

### Deployment & Updates

- **Zero-config install** — Launcher scripts auto-create local venv and install dependencies

- **NAS multi-PC portability** — Project folder can live on a NAS/synced drive; venv is created locally per PC, not in the project directory

- **Automatic updates** — Background thread checks GitHub for newer version; Python fallback with download link

- **Desktop shortcut** — Offered on first run; targets the launcher script for portability across PCs

### Privacy & Reliability

- **Anonymized bug reporting** — Error logs and bug reports automatically anonymize user paths (replaced with `~`) and omit specific OS version details

- **Automatic error logging** — All unhandled errors saved to `.exposure_calc_errors.log` (in the program directory) with auto-rotation at 500 KB

- **One-click bug report** — Red button opens a pre-filled GitHub Issue with anonymized environment info and last logged error

- **Windows EXE** — Standalone `.exe` via PyInstaller, no Python installation needed

---

## Quick start

### Windows (Recommended — Launcher)
1. Double-click `launch.bat`
2. The venv is created automatically with all dependencies
3. A desktop shortcut is offered on first run

### Windows (EXE)
1. Download `ExposureCalculator.exe` from [Releases](https://github.com/ARP273-ROSE/exposure-calculator/releases)
2. Double-click — no installation needed, no Python required

### Linux / macOS
```bash
chmod +x launch.sh
./launch.sh
```
The venv is created automatically with all dependencies.

---

## Requirements

- **Python 3.8+**
- **PyQt6** — installed automatically by the launcher
- **matplotlib** — installed automatically by the launcher

---

## Usage

1. **Parameters** — Enter sky background levels (e.g. from [SharpCap](https://tools.sharpcap.co.uk/)) and sensor data, or select a camera from the database.
2. **Swamp Factor** — Set desired SF (3-10), read target medians (SF x3, SF xN, SF x10).
3. **Optimal Time** — Set accepted additional noise (%), read recommended times per filter.
4. **Comparison** — Compare two exposure strategies in L and RGB.
5. **Charts & Tables** — Visualize noise vs. exposure time.

Only the yellow input fields need to be edited; results update automatically.

---

## NAS Multi-PC Portability

The project folder can live on a NAS or synced drive and be used from **multiple PCs** without conflict:

- **Virtual environment** is created locally on each PC (`%LOCALAPPDATA%\ExposureCalculator\venv` on Windows, `$XDG_DATA_HOME/ExposureCalculator/venv` on Linux/macOS) — never inside the project folder.
- **Launcher scripts** (`launch.bat` / `launch.sh`) detect Python, create the local venv, install dependencies from `requirements.txt`, and launch the app.
- **Desktop shortcut** targets the launcher script, not a specific Python path — so it works regardless of where Python is installed on each PC.
- **Icon** is copied locally for reliable display in Windows shortcuts from network paths.
- **App data** (settings, error log) is stored alongside the script in the project directory, so it follows the code across machines.

### First launch on a new PC
1. Double-click `launch.bat` (Windows) or run `./launch.sh` (Linux/macOS)
2. The venv is created automatically with all dependencies
3. A desktop shortcut is offered on first run

---

## Bug Reporting

**Automatic logging**: All unhandled errors are saved to `.exposure_calc_errors.log` (in the program directory) with timestamp, version, OS, Python version, and full traceback. Log is auto-rotated at 500 KB. **User paths are automatically anonymized** (replaced with `~`) for privacy.

**Manual report**: Click the red **"Report a bug"** / **"Signaler un bug"** button. A GitHub Issue opens pre-filled with your anonymized environment info and the last logged error. Just describe the problem and submit.

---

## Automatic Updates

The application checks for updates via a background thread:

| Method | When | How |
|--------|------|-----|
| **Launcher** (`launch.bat` / `launch.sh`) | Every launch | Detects Python, ensures venv, installs deps |
| **Python fallback** | Direct `python ExposureCalculator.py` | Background thread checks remote `__version__` via GitHub, updates if newer |

| Scenario | Behavior |
|----------|----------|
| Git + internet | Auto-update via `git pull --ff-only`, restart message shown |
| No git | Python shows download link |
| No internet | App starts normally, no notification |
| Zip download (no .git) | `.git` check skips update, Python shows download link |

---

## Project Structure

```
exposure-calculator/
├── ExposureCalculator.py          # Main application (single-file, PyQt6)
├── ExposureCalculator_Manual.pdf  # Theory & user manual (PDF)
├── shortcut_helper.py             # Desktop shortcut auto-creation (portable)
├── requirements.txt               # Python dependencies (PyQt6, matplotlib)
├── launch.bat                     # Windows launcher (local venv, portable)
├── launch.sh                      # Linux/macOS launcher (local venv, portable)
├── run.bat                        # Legacy Windows launcher
├── run.sh                         # Legacy Linux/macOS launcher
├── build.bat                      # Build script for Windows EXE (PyInstaller)
├── logo-expo.png                  # Application icon (PNG)
├── logo-expo.ico                  # Application icon (Windows ICO, multi-size)
├── .gitignore                     # Exclusions (build/, dist/, __pycache__/)
└── README.md                      # This file
```

---

## Settings & Export

**Auto-save**: All parameters are automatically saved to `.exposure_calc_settings.json` (in the program directory) and restored on next launch.

**Export**: Click **Export** to save parameters and results to JSON:
- `settings`: all input parameters (importable)
- `parameters`: sky levels, read noise, gain, dark current, bits, offset
- `approach1`: swamp factor, medians at SF x3 and SF x10
- `approach2`: noise %, C factor, optimal times per filter

**Import**: Click **Import** to load parameters from a previously exported JSON file.

---

## Theory (summary)

**Noise sources:** useful signal + sky background + read noise + dark current + photon noise.

**Total noise:** sigma = sqrt(RN^2 + DC*t + Sky*t)
**SNR when stacking N subs:** SNR = Signal * sqrt(N) / sigma

**Swamp Factor:** SF = (Sky * t) / RN^2
- SF < 3: read noise dominates -> increase exposure
- 3 <= SF <= 10: optimal zone
- SF > 10: diminishing returns

**Additional noise (2nd approach):**
Add_noise = sqrt((T*Sky/RN^2 + 1) / (T*Sky/RN^2)) - 1
C = 1 / ((1 + %noise/100)^2 - 1)
T_optimal = ceil(C * RN^2 / Sky)

See the in-app Help tab or `ExposureCalculator_Manual.pdf` for full theory.

---

## Credits

- **Theory & original spreadsheet:** (c) Benoit Saintot
- **GUI & Python application:** NGC4565
- **Version:** 2.0.2

---

## License

Use and share with attribution as above.
