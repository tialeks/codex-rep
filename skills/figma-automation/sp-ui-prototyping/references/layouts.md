# Layout and Browser Verification

## Choose the Layout from the Task

Follow the user's requirements, supplied responsive designs and existing app
layout. If those leave room for judgment, choose a content-appropriate fluid
layout and state the choice as a prototype recommendation. Ask only when an
unresolved design choice materially blocks the task. Do not impose an unrelated
page width or require approval merely to follow a supplied wider design.

A centered, fluid shell with a 600 px maximum is an optional compact-prototype
mode **only when the user or project explicitly chooses it**. It is not the
SP UI default or a component breakpoint. Do not require an exception request
for other layouts. Keep fixed navigation and headers aligned with whichever
shell the application actually uses.

Use flex/grid, wrapping and media/container queries. Reuse documented project
breakpoints; otherwise choose content-driven ones and identify them as local.
Know whether a component responds to viewport or container width. Auto Layout
alone does not specify the responsive contract. Test the relevant width source.

Preserve collection order and semantics. Do not invent a desktop grid or carousel
when reproducing a design; for a new prototype, select the structure for the task.
Let content determine height, give text regions room to shrink/wrap, and avoid
page-level overflow. Never hide overflow globally to mask a broken layout.

## Shared Wrappers

Trace the route through document, providers, navigation and width constraints.
Prefer route-local changes. Before editing a shared wrapper, explain why that is
needed and which routes are affected; verify an unaffected route afterward.

## Choose Verification Widths

Cover the requested device range and supplied design widths. For a responsive
page, inspect at least a narrow and a wide relevant viewport, plus immediately
below and at meaningful layout/component breakpoints. For container queries,
vary the container as well as the viewport. Verify the explicitly chosen compact
shell around its maximum when that mode applies. There is no fixed universal
set of four widths in this skill.

Include long or missing content and important interaction states where applicable.
Use the component's documented motion/reduced-motion behavior; do not invent
animation durations or infer behavior from a still image.

## Inspect the Actual Route

1. Run the final serving mode and open the actual route, preferably through the
   project's browser test tooling. Wait for the page root and fonts; do not use
   persistent-request `networkidle` as the only readiness signal.
2. Trigger relevant lazy loading and verify visible images/backgrounds, dimensions
   and actual fonts. Associate failed resources with the rendered state. For SVG
   or CSS backgrounds, use appropriate evidence instead of fabricating image
   element properties or HTTP status.
3. Measure shell and navigation bounds, wrapping and horizontal overflow at the
   chosen widths. Compare observed DOM geometry to the intended layout rather
   than treating CSS declarations as proof.
4. Exercise the requested flow, keyboard access and relevant control states.
   Capture fresh route/state screenshots and inspect them for content, fonts,
   assets, clipping, overlap and interaction feedback. Include local composites
   separately when a full-page screenshot hides important detail.
5. Fix mismatches and recapture affected states after the final rendering change.
   Screenshots with error overlays, failed resources or from earlier code are not
   successful verification. Report blocked capture/navigation/resource checks.

Keep a compact viewport/state result with screenshot paths and relevant resource
failures. Separate type/build/test results from browser evidence. A build or a
saved screenshot alone does not prove appearance was inspected.
