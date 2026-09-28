# Anatomy ledger

Complete this audit before implementation. Use one row per visible first-level block and add nested rows for repeated or structurally complex elements.

| Field | Required evidence |
| --- | --- |
| Node | Figma node id and exact role/name |
| Parent | Actual parent and sibling order |
| Layout | auto-layout axis, wrap, alignment, distribution, absolute child status |
| Width | fill/hug/fixed, value, min/max, left/right or scale constraint |
| Height | fill/hug/fixed, value, min/max, top/bottom or scale constraint |
| Spacing | four paddings, row/column gap, item spacing |
| Clip/scroll | clipping ancestor, overflow axis, scroll track padding, scrollbar behavior |
| Surface | every fill layer, gradient stops/angle, opacity, stroke, radius, shadow/blur |
| Type | exact family/file plus file hash, system-font status, style, weight, variable axes, size, line height, letter spacing, alignment, line limit |
| Asset | source node, original file, intrinsic size, box, object-fit, object-position/crop |
| Asset visibility | alpha/nontransparent bounds, mask/composite role, visible-pixel expectation in the rendered crop |
| Ratio chain | intrinsic bitmap ratio, exported-node ratio, rendered box ratio, clip/crop transform, tolerance |
| Reuse | Figma component/variant, invariant shell, allowed variant deltas, and corresponding code component/props |
| State | default/pressed/selected/scrolled/disabled and prototype connection |

For any non-static screen, the separate interaction ledger in `interactions.md` is mandatory; the single `State` cell above is not sufficient.

## Content contract

For every repeated component, test authored content limits rather than the single sample visible in the frame:

| Case | Required decision |
| --- | --- |
| Short / long text | wrap or clamp count, minimum copy height, action alignment |
| Empty optional slot | whether the slot collapses or preserves spacing |
| Numbers | numeral form, grouping, currency/points asset, no synthetic glyph |
| Existing states | default, selected, disabled, loading, error, locked |
| Mixed row | tallest content owns the rendered row height when Figma uses stretch |

Use props for independent content values. Use a variant only for a stable combination that changes anatomy, semantics, or behavior. A different title/image/value alone is data, not a new variant.

## Dependency checks

Record these relationships rather than only pixel dimensions:

- which child grows when the viewport widens;
- which siblings have min/max widths and which one absorbs remaining space;
- whether row height comes from the tallest item;
- which ancestor owns border-radius clipping;
- whether a horizontal scroll track includes the edge padding or sits inside it;
- whether a fixed action participates in flex flow or overlays content;
- whether a sticky header replaces, covers, or follows the original header;
- which chrome stays outside screen transitions;
- whether text hugs content, wraps, clamps, or truncates;
- whether multiple fills/effects are composited and in which order.
- whether an outer section fills its parent while only the repeated items inside keep an authored fixed/min/max width;
- which first-level vertical zone contains the node and the zone's root-relative bounds;
- the complete ancestor path that determines each visible leaf's width and height;
- which dimensions come from aspect ratio and how they change when the parent widens;
- whether an exported bitmap includes transparent padding or transformed bounds that differ from the visible artwork;
- whether a fixed-size artwork sits inside a fluid stage without inheriting its width.

## High-risk patterns

### Long or dense frame

First create a zone map from root children: root-relative Y range, role, repeated component source, and nested node requiring its own design context. Capture readable crops per zone instead of relying on one downscaled full-frame screenshot. Audit shared components once, then record instance-specific overrides. A full-frame screenshot proves global order and rhythm; it is not readable evidence for typography, assets, radii, or nested constraints.

### Horizontal carousel in a rounded card

The rounded card should usually own `overflow: hidden`. The horizontal scroller should span the card's clipping box, while an inner track supplies left/right content padding. Padding the outer scroller often clips against a rectangular inner viewport and exposes the wrong card edges.

### Equal-height repeated cards

When Figma uses stretch, implement the row/grid so every card in a row gets the maximum row height. Inside each card, use a vertical flex column and let the content region grow before the action. Do not fix a title area's height unless Figma does.

For a wrapping container, the equality scope is one rendered flex/grid line, not the entire collection. Record wrap, gap, align-items/align-content, card flex basis and min/max, then group instances by rendered top coordinate at every required width. Buttons align through internal flexible space; truncating content or assigning unrelated fixed heights is not an equal-height solution.

Define the shared card shell once: surface radius, copy padding, title line limit, artwork slot, action slot, and internal growth. Treat text, image, badge, price, and state as data or variant props. If two instances of the same Figma component have different shell geometry in code, either prove an authored variant or fix the shared component; do not patch the instances separately.

Do not introduce single-line ellipsis as a space-saving default. Preserve the authored wrap/clamp behavior and maximum line count, then let the row stretch to its tallest item when Figma uses stretch.

### Fill section with fixed-width scroll items

Separate the section, scroll viewport, track, and item constraints. A section marked fill must follow the content column at every width; only the track items retain their authored basis/min/max. Verify that narrow overflow is reachable through the inner scroller and that wider viewports do not leave the whole section stuck at the source-frame pixel width.

### Fluid three-item hero or medal rail

Capture each item's grow, shrink, basis, min, and max. A visually centered fixed-width image at one viewport does not reproduce the dependency. The clipping stage and offscreen neighbors are separate constraints.

### Layered progress or reward fill

Capture every track segment and background layer separately. A flat color is incorrect when Figma uses overlapping linear gradients, masks, or translucent overlays.

### Translucent overlay or sheet surface

Read the surface's fills and effects as an ordered compositing stack, not as one apparent color from the screenshot. Record the opaque substrate separately from translucent decorative fills, image fills, node opacity, blend mode and backdrop blur. A translucent gradient over an omitted base fill exposes the page behind it and is structurally wrong even when its colors look similar on a quiet background.

Render the surface over both the real page and a temporary high-contrast diagnostic background. Inspect visually empty regions of the sheet, not only areas covered by artwork and text. The page may show through only when Figma explicitly specifies a translucent final composite; blur alone is not evidence of intended transparency.

### Typography that looks “too heavy”

Confirm the loaded font bytes and computed family before changing weight. For a variable font, verify `wght`, `wdth`, optical size, and font synthesis. Compare glyph shapes at the same size and line height; do not tune Medium down by eye to compensate for a fallback font.

A named static face such as `Medium.ttf` is not proof that it is equivalent to the design's variable-font instance. If the exact family is available as a variable font, record its file hash and declared axes, reproduce the specific `wght`/`wdth` values, and assert the computed `font-variation-settings`. For large numeric displays, compare a crop containing repeated zeroes; their advance width and contour expose a wrong width axis even when the overall text block nearly matches.

### Fluid card with proportional artwork

Do not freeze the card height at the source viewport. Record the text/top region, the artwork's aspect ratio and min/max dimensions, the action gap, and any surface max-height. When the card fills a wider row, let the proportional artwork derive the new height until the recorded cap applies. Assert the dependency at every requested width.

### Fixed artwork inside a fluid stage

The stage may absorb remaining width while the artwork stays fixed. Preserve the artwork's own box and internal transform; do not set its image to `width:100%; height:100%` unless the Figma artwork itself is fill on both axes. Transparent bitmap bounds are not proof that the visible art should be stretched.

Record the nontransparent pixel bounds as well as the file bounds. A bitmap can decode and report the expected dimensions while containing no visible pixels, or while its visible artwork sits outside the rendered crop. Masks and base layers must be verified as a composed subtree, not accepted independently because their files load.
