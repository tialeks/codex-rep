# Service logos

50 standalone SVG service marks in one visual system.

## Files

- `01-nova.svg` … `50-knot.svg` — individual assets.
- `manifest.json` — names, paths, ids, and palette values.
- `sprite.svg` — all marks as reusable SVG symbols.
- `/service-logos-preview.html` — visual catalog when the local app is running.

Every logo uses a `64 × 64` viewBox, has an accessible `<title>`, and has no
font or image dependencies.

## Standalone usage

```html
<img src="/service-logos/01-nova.svg" width="48" height="48" alt="Nova" />
```

```jsx
<img src="/service-logos/01-nova.svg" width={48} height={48} alt="Nova" />
```

## Sprite usage

```html
<svg width="48" height="48" role="img" aria-label="Nova">
  <use href="/service-logos/sprite.svg#logo-nova"></use>
</svg>
```

The available symbol ids follow the pattern `logo-{slug}`. Use
`manifest.json` as the source of truth when rendering logos dynamically.

## Regeneration

Run `scripts/generate-service-logos.mjs` with Node.js after changing the
palette, geometry, or symbol definitions.
