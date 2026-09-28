# Visual QA protocol

## 1. Capture comparable evidence

- Export the exact Figma node at its natural scale unless the user requested another scale.
- Render the app at the same CSS viewport width and full frame height.
- Wait for `document.fonts.ready`, decoded images, and stable animation state.
- Disable animations for static pixel comparison, but test navigation motion separately.
- Ensure browser scaling and device scale factor are known and consistent.
- Prove the QA URL serves the current source. For preview/static servers, rebuild before capture and verify a current asset/hash or visible change; reload alone may keep testing stale `dist` output.
- Add any real review viewport visible in browser feedback to the QA matrix, even when it is outside the original source width. Treat it as a new boundary unless the user explicitly accepts a hard minimum or maximum.
- Do not compare a rounded Figma presentation frame with a rectangular app viewport without explicitly masking only the presentation corners.

## 2. Compare by zones

Divide the frame into rectangular regions at real Figma block boundaries: status/header, hero, each critical card or repeated pattern, sections, and bottom navigation. Store global and per-region changed-pixel ratios. A large quiet background must not hide a badly mismatched card.

For each failing zone, keep a short mismatch ledger:

| Evidence | Likely cause | Fix | Recheck |
| --- | --- | --- | --- |
| text baseline/width differs | wrong font file, axis, line height, or fallback | inspect computed font and network load | crop diff |
| image silhouette differs | wrong asset or crop | download original and match object-position | asset zone |
| edges drift with width | fixed width substituted for fill/min/max | restore constraints | 360/480/600 |
| rounded scroller edges differ | clip owner or track padding is wrong | move overflow/padding to correct layer | scroll at both ends |
| one card is shorter | row does not stretch | restore stretch plus internal flex growth | every row |
| progress colors differ | missing gradient layer or wrong opacity | reproduce all fill layers | progress crop |
| page content shows through a sheet/card | opaque base fill omitted below translucent decoration | restore the ordered fill stack and recheck on contrast content | empty surface crop |

## 3. Structural browser tests

Do not assert every pixel as a hard-coded CSS value. Assert the dependencies that define the design:

- root width equals its Figma constraint at each viewport;
- sibling min/max widths and flex grow/shrink/basis;
- gaps and padding derived from the parent;
- equal heights per repeated row;
- equal heights are measured by grouping cards with the same rendered top coordinate at each width; do not compare only the first row or the whole collection as one group;
- repeated instances of one component preserve the same invariant shell geometry—radius, padding, copy/artwork/action slots, and button baseline—while only documented variant props differ;
- no overlap between text/content and fixed actions;
- overlay, sheet and glass surfaces preserve the ordered Figma fill/effect stack; a high-contrast element behind an intended opaque region is not visible in the rendered composite;
- correct clip owner and intentional inner scrollability;
- no document horizontal overflow;
- original image assets load and have nonzero natural dimensions;
- visible alpha-bearing assets contain nonzero visible pixels in the expected crop; fully transparent exports and artwork clipped outside the rendered box fail even when natural dimensions are nonzero;
- intentional horizontal scrollers respond to real wheel/touch/drag input and change `scrollLeft` at the narrowest viewport;
- local tab/state changes preserve route, scroll position, shared DOM ownership, and absence of route animation;
- visibility checks use rendered geometry such as `getClientRects()` or ancestor visibility, not only the element's own computed `display`;
- each raster/composite preserves the documented intrinsic/export/render ratio chain and does not use unexplained anisotropic scaling;
- widening the viewport changes only the axes marked fluid in the constraint matrix; fixed artwork dimensions remain fixed and ratio-derived heights follow their equations;
- every Figma font family is loaded and appears in the computed style of its representative text selector; `document.fonts.check` alone is only a preflight;
- every variable-font representative exposes the expected computed axes; include a large numeric sample when the screen uses prominent balances or prices, so a wrong `wdth` axis cannot hide in the global diff;
- typography-wide OpenType features resolve identically on representative body, button, price, and display text; inspect repeated zeroes and the adjacent points/currency asset together;
- sticky header and shared status/navigation remain at the expected screen coordinate;
- fixed bottom navigation reaches both viewport edges, remains pinned without an unintended gap, includes the authored bottom/safe-area padding, and the final scroll item can clear it with the required breathing room;
- no sticky ancestor creates an unintended scroll root through overflow, transform, or containment, and the underlay changes only after the designed threshold;
- forward/back panels animate in the correct directions.

## 4. Acceptance

A numeric threshold is a regression guard, not proof by itself. Default starting alarms for a faithful mobile screen are 4% global changed pixels and 5% per critical rectangular region with `pixelmatch` threshold 0.1 and antialiasing ignored. Tighten them after the first correct baseline. Never loosen them merely to make a known mismatch pass.

The test passes only when:

1. automated ratios are under the agreed limits;
2. the diff image was visually inspected;
3. no conspicuous mismatch is hidden by a large matching area;
4. anatomy and interaction assertions pass at every required width;
5. build/typecheck/tests pass.
6. every requested responsive width passes the distortion guard and constraint-dependency assertions, not only overflow checks.

## 5. Technical accessibility gate

Do not silently redesign a Figma mismatch in the name of accessibility. Preserve the agreed visual source, implement semantic HTML, keyboard behavior, focus and accessible names, then report any unresolved design-level contrast or target-size issue as debt.

When claiming accessibility was checked, validate the rendered DOM externally:

1. `html-validate` for HTML/ARIA structure;
2. `axe-core` for the real accessibility tree and WCAG violations;
3. Lighthouse accessibility for landmarks, document metadata and heading order.

Avoid blanket `aria-hidden`: it must never hide a focusable element or its focusable descendants. A passing visual diff is not accessibility evidence, and in-head WCAG reasoning is not a validator.
