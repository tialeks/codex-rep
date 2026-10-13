# Package, Theme and Font Setup

## Always Use the Latest Stable SP UI Releases

The distribution entry points are separate packages:

- `@yandex-adtech-int/sp-ui-core`: components and public styling APIs.
- `@yandex-adtech-int/sp-ui-theme`: theme helpers and styles.
- `@yandex-adtech-int/sp-ui-tokens`: design tokens and exported contracts.
- `@yandex-adtech-int/sp-ui-assets`: icons, graphics, logos and catalog.
- `@yandex-adtech-int/sp-ui-fonts`: font binaries and public CSS face declarations.

Use `https://npm.yandex-team.ru` with the project's approved access configuration.
Do not print credentials, copy another user's token or change global npm settings.
If access fails, report the prerequisite; do not fall back to old AdTech archives.

For BOTH new and existing prototypes, ALWAYS fetch the latest stable published
versions of Core, Theme, Tokens, Assets and Fonts at the start of each task. Existing
manifest/lockfile versions are the starting state, not a reason to keep an older
SP UI release. Do not upgrade unrelated dependencies automatically.

1. Query the listed packages in the internal registry:

   ```sh
   npm view @yandex-adtech-int/sp-ui-core dist-tags --json --registry=https://npm.yandex-team.ru
   npm view @yandex-adtech-int/sp-ui-theme dist-tags --json --registry=https://npm.yandex-team.ru
   npm view @yandex-adtech-int/sp-ui-tokens dist-tags --json --registry=https://npm.yandex-team.ru
   npm view @yandex-adtech-int/sp-ui-assets dist-tags --json --registry=https://npm.yandex-team.ru
   npm view @yandex-adtech-int/sp-ui-fonts dist-tags --json --registry=https://npm.yandex-team.ru
   ```

   Use each package's current stable `latest` release. Do not use a remembered
   version, a README example, cached metadata or an installed old version as the
   answer. Prerelease/alpha/beta releases are excluded unless explicitly requested.
   If `latest` is a prerelease or registry metadata is inconsistent, report the
   missing stable release or conflicting metadata instead of guessing. In particular,
   a new Fonts package may initially have only a PR alpha tagged `latest`: this
   does not authorize installing it as stable. Use a prerelease only when explicitly
   requested, and pin its exact version. Before the first stable Fonts publication,
   preserve working approved project fonts where available; otherwise font setup
   remains blocked until an approved source or prerelease is selected. Continue
   independent work and disclose the missing Fonts release. Do not automatically
   switch to the historical font helper. Registry access failure does not authorize
   silently using an older release.
2. Read `version`, `dependencies`, `peerDependencies` and `engines` for the exact
   selected releases using `npm view package@version ...`. Check that they work
   together and with the project's React/React DOM and tooling. The packages do
   not need to share a version number. If the latest set conflicts, report the
   exact constraint and required decision; do not silently pick older SP UI versions.
3. Include directly imported packages as direct dependencies, even if transitive.
   Build the concrete install/update command with the resolved exact SP UI
   versions, including Fonts when a stable release is available or a prerelease
   is explicitly selected. Use the existing manager: `npm install --save-exact`
   or `pnpm add --save-exact`. Do not execute placeholder commands or leave `latest`
   as a floating dependency. Follow workspace-specific filtered rules when applicable.
4. Update manifest and lockfile together; retain unrelated dependencies and project
   scripts. For an existing prototype, adapt affected usage to the actual updated
   API and rerun the requested flow instead of relying on old component examples.
5. Read the resulting installed export maps/declarations and compile the actual
   usage. Record exact resolved versions and keep the lockfile with the prototype.

The historical `plus-ultra-storybook/components/manifest.json` distributes
AdTech UI archives, not a current SP UI release source. No archive-vendoring
installer or special transitive override is required for normal registry usage.
For migration, change imports and dependencies together, inspect changed APIs,
and remove only obsolete package refs/overrides; keep unrelated vendor/font files.

## Theme and CSS

Inspect the selected Theme export map, helper declarations and styles. Confirm
which styles include Tokens, which root class/attribute enables them and how
portals inherit the theme. Do not invent a ThemeProvider, universal stylesheet or
component stylesheet path from a filename that is not publicly exported.

This small browser-entry example is a starting point, not a version-independent
API promise. Confirm the imports, function signature and theme name in the
installed release before using it:

```tsx
import { themeToClassnames } from '@yandex-adtech-int/sp-ui-theme';
import '@yandex-adtech-int/sp-ui-theme/styles/light.css';

document.documentElement.classList.add(themeToClassnames('light'));
```

Preserve unrelated root classes. For SSR, use the framework's document/root API
and keep initial server/client themes consistent; do not execute that DOM statement
on the server. When switching themes, load their required styles and replace only
the library's theme classes, deriving those classes from its API.

Check existing CSS imports before adding Tokens separately: Theme may already
include them. Inspect Core's exported entry and shipped CSS to determine whether
it injects styles or needs an explicit stylesheet. Use a CSS-capable bundler;
plain Node execution of a CSS-importing UI module is not a compatibility test.

Render a needed component and typography sample. Verify computed styles, actual
token values beneath the theme ancestor and production CSS delivery. Missing CSS
is an integration issue; do not compensate with copied component internals.

## Fonts

### Fonts Package

Determine required families, weights and styles from the selected Core CSS and
design. The standard SP UI source is `@yandex-adtech-int/sp-ui-fonts`; Theme,
Tokens and typography classes do not load font binaries. Inspect the installed
Fonts `exports`, CSS face declarations and README before choosing imports.
Keep unrelated brand fonts and working approved project font setup; migrate
matching declarations deliberately, without registering the same faces twice.

For releases exporting these subpaths, import the needed families once at the
application entry point (Next.js root layout or `_app.tsx`):

```tsx
import '@yandex-adtech-int/sp-ui-fonts/ys-text.css';
import '@yandex-adtech-int/sp-ui-fonts/ys-compressed.css';
```

These imports declare `YS Text` and `YS Compressed Var`; they do not assign a
family to elements. Use the verified Core typography API for that. Other public
family CSS entries and `fonts.css` must be selected from the installed export map.
Load only the families the prototype needs. Check the actual weight/style coverage:
a normal variable compressed face does not establish a genuine italic face.

Font URLs are relative to package CSS. Let the consumer's bundler emit the font
assets; do not copy Storybook font files, invent a CDN URL or add a static `<link>`
for these package imports. Verify the production build beneath its deployment
base path. If Vite dev reports an asset outside its serving allow list, allow the
resolved installed Fonts package directory while preserving existing workspace
allow entries; do not allow the entire filesystem.

Record the exact Fonts version, imported families and actual loaded faces in
prototype delivery notes. If no stable package or approved existing source is
available, follow the publication-gap branch above. Disclose the missing release
and any observed browser fallback; a fallback is not an approved replacement source.

### Historical Adapter (Explicit Legacy Use)

Use `scripts/install-fonts.mjs` only when the user explicitly selects the historical
supply or the task is to maintain a prototype already using this adapter. It is
**not automatic discovery of the fonts required by every SP UI release** and is
not a default fallback for an unavailable Fonts package.
Before using it, compare its `fonts.css` face declarations with the current needs.
If incompatible or unavailable, use a suitable approved source and report the gap;
do not change typography tokens to fit the old bundle.

```sh
node scripts/install-fonts.mjs --project ../prototype/package.json
```

This helper requires Node.js 22+ and an existing package.json. Its default source is
https://s3.mds.yandex.net/plus-ultra-storybook/components/fonts/manifest.json.
It deliberately accepts only the known schema and six filenames, checks every
SHA-256 before writes, and refuses traversal, symlinks and conflicting files.
An explicit trusted HTTPS or local manifest can be passed with `--manifest`, but
it must follow that same supply contract. A changed schema/file set requires
updating this adapter and its tests, not weakening validation during a prototype.
Hashes detect corruption, not an untrusted publisher. Do not run it concurrently.

It changes no package metadata and writes into `public/fonts/adtechui`; the old
folder name preserves compatibility and does not select old component packages.
Keep the files with the prototype and serve them under its deployment base path.
For Vite, a corresponding index.html entry is:

```html
<link rel="stylesheet" href="%BASE_URL%fonts/adtechui/fonts.css" />
```

For other frameworks use their static-file/base-path mechanism. Repeated identical
installation is safe; differing files are refused. Do not delete an existing font
setup automatically to make the helper succeed.

Wait for fonts to load and inspect actual rendered faces as described in
[Design Basics](design-basics.md). Family names or `document.fonts.check` alone
can report success while the target text renders with a fallback.
