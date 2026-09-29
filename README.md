# Erection Automation — Livio Building Systems

Project: **4898 El Camino Real, Los Altos, CA 94022**
Deliverable: erection-sequence coordination package (panelized/LGS), generated programmatically from the permit set.

## Contents

| Path | Description |
|---|---|
| `El Camino Real_Permit Set_Revised_compressed.pdf` | Permit set (source of record — authoritative) |
| `reference.pdf` | Livio reference erection-sequence methodology |
| `Livio_4898_El_Camino_Erection_Coordination_RevC.pdf` | **Rev C deliverable — 29 pages, 74 steps, wall-band erection arrows on every floor plan** |
| `Livio_4898_El_Camino_Sequence_Register.csv` | Sequence table (74 rows), matches the PDF exactly |
| `rev-c-build/` | Build inputs: `build_package.py` (PyMuPDF generator), `sequence-data.json`, `page-index.json`, aerial imagery |

## Revision history

- **Rev A** — initial 28-page / 74-step package; one flagged gap: no aerial site-context page (Google Earth retrieval failed).
- **Rev B (29 SEP 2026)** — adds page **EC-03A "Aerial site context | Independent imagery cross-check"**: Esri World Imagery retrieved at the project coordinate (37.3980, −122.1080), annotated with frontage/rear-constraint cross-checks. Imagery is labeled **SUPPORTING CONTEXT ONLY**; permit drawings remain authoritative. The 74-step sequence is unchanged — the aerial check **confirmed** the existing crane candidates (Jordan Ave A/B), frontage assumptions, and "NO NEIGHBOR STAGING" rear constraint.
- **Rev C (29 SEP 2026)** — replaces the schematic single-edge arrows with **wall-band erection runs on every floor plan (L1–L8)**: for each of the 6 wall groups per level, a red multi-segment arrow traces the group's exterior-wall band in the actual sequence direction plus its closing return toward the corridor, arrowhead on every segment, step badge tied to the run start. Runs chain visually through each level (rear L→R, near side R→L, frontage groups close the shell) and follow the `reference.pdf` arrow methodology. Runs are schematic wall-band segments pending the shop-panel map (RFI-03) — no panel IDs are invented. Roof page (steps 69–74) retains its plan-based arrows. All 74 steps unchanged and re-verified.

## Reproducing the build

```bash
pip install pymupdf pillow
cd rev-c-build
python build_package.py   # regenerates the Rev C PDF + sequence register
```

## Status / limitations

Coordination **concept** — NOT FOR ERECTION; stamped engineering and a lift plan are required before use. Crane capacity, outrigger bearing, tree survey, traffic control: **FIELD VERIFY**. Wall-band arrows are schematic group runs, not shop-panel erection maps (RFI-03 open). QA: every plan page (L1–L8 + roof) visually verified — arrows present, directioned per the sequence, clear of dimensions/labels, badges match the register; CSV verified 74 unique steps matching the drawing source exactly.
