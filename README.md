# Exposure Time Calculator

[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)]()
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg)]()

**Ideal sub-exposure time calculator for astrophotography** — helps you choose optimal exposure times for deep-sky imaging based on sky background, sensor parameters, and proven mathematical models.

> This application is based on the original Excel spreadsheet created by **Benoit Saintot**.

---

## Features

- **Two complementary approaches**
  - **Swamp Factor** (SF 3-10): target sky background median (ADU)
  - **Optimal time**: recommended sub-exposure per filter for an accepted additional noise %

- **Camera database** — 40+ models (ZWO, QHY, Moravian, ATIK, Player One, ToupTek) with auto-fill of Read Noise, Gain, Dark Current, etc.

- **Multi-filter support** — L, RGB, Narrowband 12 nm, 7 nm, 3 nm (NB3 = NB12/4, automatic)

- **Interactive tools** — Comparison of two strategies, charts, tables, JSON export

- **Bilingual** — Auto-detected English / Francais; switch with one click

- **Zero-config install** — Run scripts auto-install Python and dependencies if missing

- **Automatic updates** — Launchers silently pull the latest version via git; Python fallback checks GitHub in background

- **Bug reporting** — Automatic error logging + one-click bug report button that opens a pre-filled GitHub Issue

---

## Quick start

### Windows
1. Double-click `run.bat`
2. If Python is missing, the script will try to install it via **winget** (Windows Package Manager)
3. If winget is missing, you'll be guided to install it, then run `run.bat` again

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

## Requirements

- **Python 3.7+** (with tkinter; usually bundled with Python on Windows/Linux)
- **matplotlib** — installed automatically on first run

---

## Usage

1. **Parameters** — Enter sky background levels (e.g. from [SharpCap](https://tools.sharpcap.co.uk/)) and sensor data, or select a camera from the database.
2. **Swamp Factor** — Set desired SF (3-10), read target medians (SF x3, SF xN, SF x10).
3. **Optimal Time** — Set accepted additional noise (%), read recommended times per filter.
4. **Comparison** — Compare two exposure strategies in L and RGB.
5. **Charts & Tables** — Visualize noise vs. exposure time.

Only the yellow input fields need to be edited; results update automatically.

---

## Automatic updates

The application stays up-to-date automatically with a two-level strategy:

| Method | When | How |
|--------|------|-----|
| **Launchers** (`run.bat` / `run.sh`) | Every launch | Silent `git fetch` + `git reset --hard origin/main` before starting Python |
| **Python fallback** | Direct `python ExposureCalculator.py` | Background thread checks remote `__version__` via GitHub, updates if newer |

| Scenario | Behavior |
|----------|----------|
| Git + internet | Launcher updates silently, app starts up-to-date |
| No git | Launcher block skipped, Python shows download link |
| No internet | `git fetch` fails silently, app starts normally |
| Zip download (no .git) | `.git` check skips update, Python shows download link |

---

## Bug reporting

**Automatic logging**: All unhandled errors are saved to `~/.exposure_calc_errors.log` with timestamp, version, OS, Python version, and full traceback. Log is auto-rotated at 500 KB.

**Manual report**: Click the red **"Report a bug"** / **"Signaler un bug"** button. A GitHub Issue opens pre-filled with your environment and the last logged error. Just describe the problem and submit.

---

## Project structure

```
exposure-calculator/
├── ExposureCalculator.py          # Main application (single-file)
├── ExposureCalculator_Manual.pdf  # Theory & user manual (PDF)
├── run.bat                        # Windows launcher (auto-install + auto-update)
├── run.sh                         # Linux/macOS launcher (auto-install + auto-update)
├── .gitignore                     # Python cache exclusions
├── CLAUDE.md                      # Project memory for AI-assisted development
└── README.md                      # This file
```

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

## Export

Click **Export** to save parameters and results to JSON:

- `parameters`: sky levels, read noise, gain, dark current, bits, offset
- `approach1`: swamp factor, medians at SF x3 and SF x10
- `approach2`: noise %, C factor, optimal times per filter

---

## Credits

- **Theory & original spreadsheet:** (c) Benoit Saintot
- **GUI & Python application:** NGC4565
- **Version:** 1.03

---

## License

Use and share with attribution as above.
