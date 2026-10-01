# Hash-bound critic report and release check

Run `scripts/review_gate.py` with Python and Pillow. `prepare` only creates an
`UNREVIEWED` record. The assigned independent critic must inspect the actual
referenced source, three STYLE originals, optional scoped references and every
saved crop before filling the record. Never turn a template into PASS yourself
or copy an old verdict onto changed image bytes.

## Prepare each preview

```sh
python3 scripts/review_gate.py prepare --phase preview \
  --source /absolute/candidate.png --main /absolute/candidate.png \
  --case-id example --variant-id A --author-id generator-agent \
  --reviewer-id critic-agent --surfaces /absolute/surfaces.json \
  --output /absolute/variant-A-preview-review.json
```

The three package STYLE images are included automatically as separate references.
Optional repeatable `--category`, `--content` and `--brand` arguments bind additional
images with the specified roles. All recorded paths are relative to the report;
move the report together with its image/reference tree, preserving relative
positions. Paths and original dimensions are bound to SHA256 file hashes.

`surfaces.json` is a list of actual named material surfaces with integer native
pixel ROIs in `[left, top, right, bottom]` order, for example:

```json
[
  {"material": "lavender plastic front", "asset": "main", "roi": [100, 100, 600, 700]}
]
```

Prepare saves exact unscaled evidence PNG crops in a new sibling directory. Supply
enough overlapping ROIs to cover every surface and its lit/mid/shadow/edge regions.
The helper cannot judge whether that coverage is sufficient. Inspect each crop at
100% original pixel scale; a reduced overview is insufficient. If a different
crop is needed, prepare another record with its own evidence paths rather than
inventing crop hashes. Every preparation starts unchecked.

## Critic fields

Keep the generated IDs, phase, paths, hashes and dimensions. Populate `status`
with `PASS` only after all reviews pass. Each `gates` object has `status` and a
nonempty `finding`. Required preview gates are `geometry`, `composition`,
`style_family`, `color` and `material`. All require PASS: absence of purple can
be explained in the color finding, but the entire palette still needs review.
When a BRAND reference is supplied, `prepare` adds a required `branding` gate
initially UNREVIEWED; it too needs an explicit PASS and finding.
Any FAIL, UNCERTAIN, NOT_APPLICABLE, missing field or
missing evidence prevents release. BRAND fidelity or source limitations must be
recorded in findings; do not infer hidden geometry from a small raster reference.

`native_100_material_review.status` must be `PASS`; its `surfaces` must be nonempty.
Each requires a named `material`, an `asset` of `source` or `main`, valid `roi`,
`finding`, `light_mid_shadow_edge_checked: true`,
`full_surface_sweep_checked: true`, and the generated `evidence` path/hash/size.
The validator verifies that each crop contains the exact original ROI pixels.
It rejects resized, changed, stale or missing crops. A checked flag alone does
not prove inspection; the independent critic remains responsible for it.

```sh
python3 scripts/review_gate.py validate /absolute/variant-A-preview-review.json --phase preview
```

Successful preview validation returns `PREVIEW_PASS`. A request for only a main
image can use this phase; it does not certify transparency or an alpha export.
Preview `source` and viewed `main` must have identical SHA256 bytes, so the critic
and designer review the actual render later used for export.

## Prepare the selected final export separately

After export, prepare a **new final record**, review final materials and edges on
main/white/black, and fill its own findings. Preview acceptance does not certify
the exported image.
Final preparation requires the actual selected `PREVIEW_PASS` report and a
recorded selection decision. Use `designer` only for a real designer choice;
use `delegated` only when the user explicitly authorized autonomous selection.
Record that choice/authorization in the selection finding; never infer approval.

```sh
python3 scripts/review_gate.py prepare --phase final \
  --source /absolute/candidate.png --main /absolute/main.png \
  --alpha /absolute/alpha.png --white /absolute/white.png --black /absolute/black.png \
  --case-id example --variant-id A --author-id generator-agent \
  --reviewer-id critic-agent --surfaces /absolute/final-surfaces.json \
  --preview-report /absolute/variant-A-preview-review.json \
  --selection-mode designer --selection-finding "Actual recorded designer choice of variant A" \
  --output /absolute/variant-A-final-review.json
python3 scripts/review_gate.py validate /absolute/variant-A-final-review.json --phase final
```

Final additionally requires `alpha_visual` PASS with a finding. Every named
material/ROI must have paired native evidence from both `source` and final `main`;
use identical material names and ROI coordinates for each pair. Each saved crop
covers the entire declared ROI exactly, with no gaps or resampling. Use multiple
overlapping pairs when a surface is too large to inspect in one view. This checks
coverage of declared rectangles, not whether the critic declared every surface.
`alpha_visual` also requires `full_boundary_sweep_checked: true` and an `evidence`
list containing at least one saved native proof for **each** of `main`, `white`
and `black`. Each proof contains `asset`, `roi`, `checked: true`, nonempty
`finding`, and `evidence` path/SHA256/size. Preparation creates unchecked full-frame
copies by default. Optional `--edge-rois /absolute/edge-rois.json` uses a JSON list
of integer ROI arrays, saving each ROI from all three assets. Use enough overlapping
tiles for all boundaries, holes and thin parts and inspect at native 100% scale.
The validator verifies exact ROI pixels and presence of all three backgrounds;
complete semantic boundary coverage is the critic's responsibility.
The validator recomputes exact
main (#535353), white and black composition from the RGBA export, checks opaque
RGB against source, checks all dimensions and ICC bytes, and requires actual fully
transparent and opaque pixels. It never trusts a supplied numeric PASS flag.

Those numeric checks cannot detect whether a wheel was mistakenly removed or a
closed recess became transparent. The critic must inspect topology, silhouette,
thin parts, false holes, edge teeth and fringes on source/main/white/black. They
also must assess camera consistency, geometry, material texture, blotches,
unwanted patterns, blur, purple fidelity and style/reference fit.

Recorded author/reviewer IDs must differ. This catches declared self review but
cannot authenticate actual agent independence. Evidence files prove pixel
provenance, not that someone looked at them. No automated check guarantees style,
hidden geometry or an ideal visual result. Acceptance is the independent visual
verdict **and** a successful final validator run.
Successful final validation returns `FULL_PASS`; it cannot be replaced by a
preview verdict or a manually added numeric PASS flag.
The final record hash-binds the selected preview report. Validation reruns its
preview gate and requires the same case, variant, source SHA256, and reference
roles/SHA256. Missing selection, changed preview bytes, changed source, changed
variant or different references reject release. Selection fields document a
decision; they do not authenticate who made it or replace explicit authorization.
The final reviewer must also differ from the selected preview's original render
author, even when a different agent performs the export. Different exporters are
allowed; changing the exporter does not authorize the renderer to review its own
result.
