# Published Assets and Figma Mapping

Use the selected release of `@yandex-adtech-int/sp-ui-assets`. Inspect its export
map, manifest/catalog and declarations instead of keeping an asset catalog here.
Core's legacy artwork is not the default source for new prototypes.

## Selection Order

1. For a supplied Figma instance, inspect its Code Connect mapping, if available.
   Confirm the example's package export and supported props in the installed
   version. A mapping is evidence of identity, not proof that every version has it.
2. If mapping is missing or errors on a nested asset, look for an exact identity
   in the installed `@yandex-adtech-int/sp-ui-assets/manifest.json` or `/catalog`:
   Figma file/node/component identity, chosen variant and public export. Check
   whether the identity refers to a master or its selected variant; do not equate
   unrelated frames or different file keys. Follow declared variant mappings.
3. If identity/variant cannot be resolved, report the missing node/variant and
   request the required asset or an explicit alternative. Continue independent
   layout work if possible. Do not silently pick similar artwork by name or look,
   redraw a logo, substitute emoji, or treat a failed mapping as permission to guess.

For a prototype without a supplied design, choose an appropriate catalog resource
for the task and identify that as a prototype choice, not an exact Figma match.
The manifest may cover only part of the Figma library; absence is not permission
to modify or republish Assets during prototype work.

## Public Imports

Derive the exact import and allowed variant combination from the matched catalog
record and its public declaration. Do not synthesize a path from a Figma layer's
name or assume that all sizes, languages and color schemes can be combined.
Confirm the public export exists and distinguishes source variant from rendered
wrapper size. Use explicit leaf imports for ordinary pages; runtime pickers can
use catalog loaders when the selected version exports them.

Read the exported adapter contract before choosing React, URL or raw-file imports.
Do not assume raw images are always URL strings or always static-image objects:
use the target framework's contract. Check whether SVG needs a loader; do not
add SVGR merely because an asset is SVG. Verify production image emission and
deployment base paths, not just development-server loading.

Use accessible names for informative assets and hide decorative icons beside a
visible label. Match the wrapper's actual accessibility API; do not assume an
SVG wrapper and an image share every prop.

## Verification

Check every nested icon/graphic, not just the parent component: correct public
import, actual selected variant, loaded resource, visual appearance and accessible
name/decorative status. Build success or successful Code Connect lookup alone
is not visual verification. Apply the resource and screenshot checks in
[Layouts](layouts.md).
