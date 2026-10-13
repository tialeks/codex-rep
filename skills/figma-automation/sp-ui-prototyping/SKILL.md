---
name: sp-ui-prototyping
short_description: React-прототипы на последних стабильных пакетах SP UI с точными ассетами и браузерной проверкой.
description: Use when a product manager wants an interactive SP UI prototype in a standalone React project using npm or pnpm and published @yandex-adtech-int/sp-ui-core, sp-ui-theme, sp-ui-tokens, sp-ui-assets, and sp-ui-fonts packages. Includes component setup, responsive layouts, user flows, and browser verification. Not for changing or publishing the component library.
metadata:
  compatibility: Standalone React matching the selected packages, TypeScript, CSS-capable bundler, Node.js, npm or pnpm; internal registry access and browser verification
---

# SP UI Prototyping

Build runnable product flows with published SP UI packages in a standalone React
project.
No Arcadia checkout, AISuite or Tracker is required. For library authoring, use
SP UI's repository workflow; PlusUI is a different design system.

## Sources of Truth

This skill describes the workflow, not a release's component catalog or API.
Read contracts from the target project's installed, locked packages: `exports`,
public declarations, CSS, assets manifest/catalog and version-matched docs.
Inspect only the components needed by the task. Examples here are discovery aids:
verify them before copying and adapt to the selected release. Never treat a
missing example in this skill as evidence that a component is absent.

Use the latest stable published versions of Core, Theme, Tokens, Assets and
Fonts. Check Fonts publication availability as described in Installation; a
checkout or draft PR does not establish a stable registry release. Query the
internal registry at the start of every prototype task, including work on an
existing prototype; upgrade older SP UI versions rather than preserving them. Follow [Installation](references/installation.md)
to validate dependencies, install exact versions and update the lockfile. Do not
silently fall back to older releases if the latest set has a compatibility problem;
report the conflicting versions and continue independent work. Record the resolved
versions in delivery notes, not as a manually maintained catalog inside this skill.

| Reference | Read when |
| --- | --- |
| [Installation](references/installation.md) | Selecting packages, wiring CSS/theme and fonts |
| [Components](references/components.md) | Discovering public APIs and mapping visible blocks |
| [Design Basics](references/design-basics.md) | Choosing semantic tokens and typography |
| [Assets](references/assets.md) | Resolving exact icons, graphics, logos and Figma assets |
| [Layouts](references/layouts.md) | Choosing page layout and verifying responsiveness |

## Workflow

1. Inspect the target project's instructions, manifest, lockfile, entry point,
   router, global CSS, fonts and available tests. Reuse its framework and package
   manager. Do not read credentials or `.env` files to diagnose installation.
2. Establish the route, product identity, primary action and reproduction scope:
   exact copy, brand adaptation or a new prototype. Derive layout from the task,
   supplied design and existing app. There is no universal page maximum in SP UI;
   a compact 600 px shell is an optional explicitly chosen mode, not the default.
   Ask only about decisions that block the requested flow.
3. Inventory copy, destinations, assets and states. Distinguish supplied content,
   approved demo data and missing information. A request for fictional demo data
   authorizes it within that scope. Do not invent legal text or real destinations.
4. Follow Installation and discover contracts from the selected packages. Use
   public imports, not Arcadia source paths, workspace links or Storybook fixtures.
   Load the needed families from the published Fonts package; preserve approved
   project fonts when appropriate and follow Installation for publication gaps.
   The historical font helper is an explicitly chosen legacy adapter.
5. Map each visible block to a public component, local prototype implementation,
   exact local reproduction, or a blocker. Verify the actual API before declaring
   a gap. Keep component-owned typography, interaction and CSS intact; use public
   customization and app-owned wrappers rather than overriding private selectors.
6. Implement the complete requested flow. Actions navigate, update state or show
   an honest outcome; no dead controls or `href="#"`. Label simulated behavior.
   Do not perform real purchases or external writes just to demonstrate a flow.
7. Use structural responsive CSS and the chosen layout. Keep shared wrapper edits
   scoped and verify an unaffected route when they are necessary. Check important
   content, interaction states and applicable breakpoint boundaries.
8. Run available type/build/lint and relevant behavior checks, then inspect the
   actual route in a browser as described in Layouts. A build is not appearance
   verification. Report unavailable evidence and checks rather than claiming pass.

## Figma and Other Design Evidence

Use the selected node, relevant documentation, supplied screenshots and assets.
With Figma tools, load their required official skill if available. Installing this
skill does not provide Figma access, tools or Code Connect mappings. Inaccessible
sources are verification limitations, not defects in the design documentation.

Code Connect offers usage examples; verify their imports and props against the
selected package. Resolve nested assets using the Assets reference. Auto Layout
is not an implicit breakpoint. Unknown behavior at other widths, interaction
states or animation timings remains unknown; do not invent a DS rule from one
frame. Continue independent work without claiming unsupported fidelity.

Distinguish observed design facts, package behavior and local recommendations.
Preserve target identity and content in brand adaptations. For exact local
reproduction, retain measured geometry instead of substituting convenient tokens.
Do not add synthetic brand graphics or silently reduce the requested fidelity.

## Completion

Report the route, resolved package versions, implemented flow, public components,
local implementations and reasons, approved demo data, layout decisions and
remaining blockers. Include actual checks and inspected fresh screenshots with
viewport/state. Keep build results separate from browser evidence; do not claim
visual completion or exact fidelity without verification.
