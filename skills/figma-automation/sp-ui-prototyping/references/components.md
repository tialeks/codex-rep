# Discovering Component Contracts

## Inspect the Selected Package

1. Locate the target project's installed `@yandex-adtech-int/sp-ui-core` package
   through its package-manager layout or resolver. Read its resolved version and
   `package.json` export map; do not assume a hoisted `node_modules` layout or that
   `package.json` itself is an exported import. If installation is blocked, a
   verified archive of that exact release can support provisional API inspection.
2. For each needed component, follow the export entry to its public `.d.ts` files
   and referenced types. Check required props, slots, allowed values, native
   attributes, refs and controlled/uncontrolled state. CSS API and React API may
   have different entry points: do not infer exports from source filenames.
3. Use documentation/examples for that release to understand semantics, defaults,
   motion and responsive behavior. Types prove shape, not runtime behavior. If
   docs are missing, inspect the shipped implementation/CSS as evidence of the
   current behavior and verify relevant behavior in the browser. A latest online
   page or Figma mapping does not override an older installed contract.
4. Compile the concrete usage in the consumer. Do not rebuild a control locally
   until you have checked whether this version supports the required behavior.

Do not maintain an exhaustive component list or prop/default table in this skill.
An export proves availability, not design-review maturity. Respect any release's
legacy/deprecation documentation. Keep package behavior, design intent and local
prototype decisions distinct if they conflict.

## Minimal Usage Example

This illustrates state wiring only. Before copying, confirm that the installed
release exports this component and supports `children` and `onClick`. Obtain any
other props from that release; do not copy a historical list of variants.

```tsx
import { useState } from 'react';
import { Button } from '@yandex-adtech-int/sp-ui-core/button/react';

export function PrototypeAction() {
  const [saved, setSaved] = useState(false);
  return <>
    <Button onClick={() => setSaved(true)}>Save selection</Button>
    <p role="status">{saved ? 'Saved in this demo only.' : ''}</p>
  </>;
}
```

Theme and CSS setup is separate: follow [Installation](installation.md).
The example text is demo content, not approved product copy.

## Composition and Interaction

Inspect actual slot types rather than assuming universal `title`, `items`,
`variant`, `as` or `href` props. Caller-owned text and links remain caller-owned;
do not add fabricated library defaults. Copyable compositions can require local
CSS; include it in the consumer instead of importing Storybook fixtures.

For form controls, check labeling, state updates, native form semantics, loading,
disabled behavior and keyboard interaction. Do not assume identical props or
semantics across controls. Preserve links for navigation and buttons for actions;
avoid nested interactive elements. Derive component breakpoints and the source
of width from its own contract, independently of the page shell.

## Mapping and Gaps

Keep a compact mapping in working notes or the requested delivery artifact:
visible block, content source, public import or local implementation, evidence
and deviation. No separate permanent report is required for every run.

- Public component: exported path and API fit the required structure.
- Local prototype: app-owned composition or a documented package gap.
- Local exact reproduction: measured design reproduced outside the library.
- Blocked: required content, asset or design evidence is unavailable.

Use public customization and wrappers. Do not copy library internals, override
private selectors or change the library API during a consumer prototype task.
Check nested graphics through [Assets](assets.md). Report gaps honestly;
creating external issues is a separate action requiring user authorization.
