# Design Foundations from the Selected Release

## Tokens and Typography

Read the installed Tokens export map, then the exported contract or CSS for the
chosen theme. Derive token names, values and units from those files; this skill
intentionally has no copied color, spacing, radius or typography tables.

Choose by semantic role: surface, content, border, feedback or control state.
Do not select the nearest-looking hex or invent a public token name. Keep static,
theme-dependent and brand colors distinct according to the selected contract.
Inspect emitted CSS units before calculations; a numeric metadata value alone
is not a usable CSS length. Test each supported theme.

Read public typography exports and their declarations/styles from Core. Reuse
those classes when available instead of reconstructing a style from remembered
font sizes. Component-owned typography should remain owned by the component.
For exact reproduction, do not force unmatched design values into convenient
public tokens: identify a local measured fallback and its reason.

## Fonts

CSS font-family declarations do not supply binaries. Determine required families,
weights and styles from the selected package's CSS and the supplied design, then
match them to the installed `@yandex-adtech-int/sp-ui-fonts` face declarations
or working approved project fonts. A font package CSS import supplies faces;
Core typography selects them. Do not assume a historical font bundle covers a
future release or synthetic italic is genuine.
See [Installation](installation.md#fonts) for package imports, publication gaps
and explicitly selected legacy adapter use.

Wait for `document.fonts.ready`, check required faces and inspect actual rendering;
readiness can also mean a failed request completed. Where browser tooling permits,
inspect rendered font faces, not only computed family names. If unavailable,
report fallback and its effect on measurements rather than claiming exact fidelity.

## Local Styling

Use a consistent vocabulary from the available tokens, natural text height and
content-led grouping. Style app-owned wrappers without resetting component-owned
appearance, focus rings or motion. Local semantic variables are allowed for a
prototype where the public API has a confirmed gap; identify them as local.

Keep semantic HTML, labels, visible keyboard focus and meaningful loading,
empty, error and success states. Verify contrast and do not rely on color alone.
These are consumer requirements, not evidence of a specific Figma measurement.

## Images

Follow [Assets](assets.md) for exact package resources. Bundler-emitted package
images are regular consumer dependencies. For other resources, use approved
assets; do not silently upload/rehost or turn temporary export URLs into durable
runtime dependencies. Never approximate brand graphics or substitute emoji.

Distinguish the image slot from the leaf resource: preserve aspect ratio, crop,
position and clipping. Provide appropriate alternative text. Verify image loading
and appearance independently of the page's HTTP status.
