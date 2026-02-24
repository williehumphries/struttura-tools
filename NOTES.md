# Structural Engineering TUI — Session Notes

## How to run
```bash
pip install -r requirements.txt
python rebar_calc.py
```

Or double-click `rebar_calc.bat` (opens in cmd).

For the taskbar shortcut, set target to:
```
wt.exe -d "d:\TUI" python rebar_calc.py
```

---

## Project structure
```
d:\TUI\
├── rebar_calc.py          # Main app (Textual TUI)
├── rebar_calc.bat         # Launcher batch file
├── requirements.txt       # textual>=0.80.0
├── NOTES.md               # This file
└── data\
    ├── prestress_bars.csv     # Skeleton — needs populating
    └── prestress_anchors.csv  # Skeleton — needs populating
```

---

## What's built

### Rebar tab (`rebar_calc.py`)
- Reference table: Bar name, diameter, area mm², kg/m for Y6–Y40
- Calculator panel:
  - **Count**: enter number of bars → total mm² + total kg/m
  - **Spacing**: enter c/c spacing (mm) → mm²/m + kg/m²
- Clicking a row in the reference table syncs the calculator bar selector
- Keybindings: `q` quit, `r` reset inputs
- Stack: Python + [Textual](https://github.com/Textualize/textual)

---

## Next session — Prestress tab

### Plan
Add a second tab to the existing app for prestress systems, loaded from CSV.

**Data files to populate first:**

`data/prestress_bars.csv` columns:
| Column | Description |
|---|---|
| `system` | Manufacturer/system name (e.g. `Macalloy 1030`) |
| `designation` | Bar label (e.g. `32mm`) |
| `diameter_mm` | Nominal bar diameter |
| `area_mm2` | Nominal cross-sectional area |
| `ult_strength_mpa` | Characteristic tensile strength |
| `breaking_load_kn` | Characteristic breaking load |
| `proof_load_kn` | 0.1% proof load |
| `weight_kg_per_m` | Unit weight |

`data/prestress_anchors.csv` columns:
| Column | Description |
|---|---|
| `system` | Must match `system` in bars CSV |
| `designation` | Must match `designation` in bars CSV |
| `anchor_type` | e.g. `live`, `dead`, `coupler` |
| `plate_width_mm` | Bearing plate width |
| `plate_depth_mm` | Bearing plate depth |
| `min_spacing_mm` | Minimum anchor c/c spacing |
| `min_edge_dist_mm` | Minimum edge distance |

### Implementation steps (for next session)
1. Rename app from `RebarApp` → `StructCalcApp`, update title
2. Wrap existing layout in a `TabbedContent` widget — tab 1: **Rebar**, tab 2: **Prestress**
3. Prestress tab layout:
   - Top: system selector (driven by unique `system` values from CSV)
   - Left panel: bar catalogue table (filtered by selected system)
   - Right panel: anchor info table (joined on system + designation for selected bar)
4. Load CSVs at startup with `csv.DictReader`; show a warning `Static` if files are missing/empty

---

## Tech notes
- Textual reactive pattern: `reactive` attribute + handler or direct `_recalculate()` call
- DataTable rows use `key=name` for programmatic cursor sync between table and Select widget
- CSS colour variables in use: `$primary`, `$accent`, `$success`, `$surface`, `$text-muted`, `$text-disabled`, `$surface-darken-2`
- Bar naming convention changed from `T` prefix to `Y` prefix (user edit)
