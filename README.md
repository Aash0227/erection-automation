# Erection Automation — Livio Building Systems

Project: **4898 El Camino Real, Los Altos, CA 94022**
Deliverable: erection-sequence coordination package (panelized/LGS), generated programmatically from the permit set.

## Contents

| Path | Description |
|---|---|
| `El Camino Real_Permit Set_Revised_compressed.pdf` | Permit set (source of record — authoritative) |
| `reference.pdf` | Livio reference erection-sequence methodology |
| `Livio_4898_El_Camino_Erection_Coordination_RevB.pdf` | **Rev B deliverable — 29 pages, 74 steps** |
| `Livio_4898_El_Camino_Sequence_Register.csv` | Sequence table (74 rows), matches the PDF exactly |
| `rev-b-build/` | Build inputs: `build_package.py` (PyMuPDF generator), `sequence-data.json`, `page-index.json`, aerial imagery |

## Revision history

- **Rev A** — initial 28-page / 74-step package; one flagged gap: no aerial site-context page (Google Earth retrieval failed).
- **Rev B (29 SEP 2026)** — adds page **EC-03A "Aerial site context | Independent imagery cross-check"**: Esri World Imagery retrieved at the project coordinate (37.3980, −122.1080), annotated with frontage/rear-constraint cross-checks. Imagery is labeled **SUPPORTING CONTEXT ONLY**; permit drawings remain authoritative. Footer bumped to REV B; metadata and filename updated. The 74-step sequence itself is unchanged — the aerial check **confirmed** the existing crane candidates (Jordan Ave A/B), frontage assumptions, and "NO NEIGHBOR STAGING" rear constraint. Build made self-contained (imagery copied into `rev-b-build/`, no Temp-path dependency).

## Reproducing the build

```bash
pip install pymupdf pillow
cd rev-b-build
python build_package.py   # regenerates the Rev B PDF + sequence register
```

## Status / limitations

Coordination **concept** — NOT FOR ERECTION; stamped engineering and a lift plan are required before use. Crane capacity, outrigger bearing, tree survey, traffic control: **FIELD VERIFY**. QA: visual inspection passed (sequence badges, arrows, crane candidates, TPZ holds, legend, new aerial page); register verified 74 unique sequential steps matching the drawing.
