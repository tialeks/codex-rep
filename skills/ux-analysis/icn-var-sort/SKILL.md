---
name: icn-var-sort
description: Sort large Figma icon or service component-set variant values alphabetically and group variants by an initial-letter property such as Letter, with a final 0-9 group. Use when a Figma component set has many named variants whose Values picker is difficult to search or whose letter grouping must be created, repaired, or verified.
---

# ICN Variant Sort

Organize a Figma component set without changing its visible variant labels, component identities, default content, or canvas geometry.

## Required setup

- Load `figma-use` immediately before every `use_figma` call and pass `resource:figma-use` in `skillNames` when the skill was loaded as a resource.
- Inspect first and mutate only the component set identified by the user.
- Preserve component IDs, exact property values, defaults, grid anchors, positions, and dimensions unless the user explicitly requests otherwise.

## Inspect the component set

1. Resolve the supplied node. Promote a variant component to its parent `COMPONENT_SET` when necessary.
2. Read `componentPropertyDefinitions` only from the component set.
3. Record every child component's ID, name, `variantProperties`, `x`, `y`, width, height, `gridColumnAnchorIndex`, and `gridRowAnchorIndex`.
4. Record the exact raw options of the property being sorted. Do not discard invisible Unicode ordering characters.
5. Derive display labels by removing only leading Unicode format/control characters. Include the common format ranges `U+200B–U+200F`, `U+202A–U+202E`, and `U+2060–U+206F`, plus `U+00AD`, `U+061C`, `U+FEFF`, and C0 controls.
6. Confirm that display labels are unique and that every child has the target property.

## Sort the main Values picker

- Compare display labels case-insensitively using stable lexical order.
- Preserve the exact raw values on the variants; invisible prefixes may carry Figma's internal option ordering.
- Reordering component children alone does not reliably reorder an already-existing `variantOptions` array.
- `componentPropertyDefinitions.*.variantOptions` and legacy `variantGroupProperties.*.values` are effectively read-only in the Plugin API.
- When an existing Values list is unordered, rebuild only that variant-property metadata inside the same component set: temporarily rename the property, restore every child name with the original raw value in the intended order, and validate the final schema. Because this touches a shared property across all variants, obtain explicit user approval immediately before the mutation.
- Never recreate the component set or clone/replace its components merely to sort values; that can break library identity and instance relationships.

## Create or update Letter grouping

1. Derive a group from the first visible character of the main value:
   - ASCII letter → uppercase `A` through `Z`.
   - Digit → `0-9`.
   - Any other initial → stop and ask how it should be grouped.
2. Use only letter groups that actually have variants. Do not create empty letters.
3. Order the groups alphabetically and append `0-9` last.
4. Within each group, keep the main values alphabetically ordered.
5. Reorder component children by group before introducing a new `Letter` variant property. Figma derives a new property's option order from the first occurrence of each value in the child order.
6. Set each component name with both properties while preserving the exact raw main value, for example `Letter=B, Service=<raw-value>`.
7. If `Letter` already exists, preserve its capitalization and update its values only as requested.

The `Letter` default normally follows the first letter of the component set's default variant. Report this rather than forcing another default by moving canvas geometry.

## Atomic validation

Perform the mutation and its checks in one `use_figma` call so a thrown validation error aborts the transaction. Return every mutated node ID.

Before returning success, require all of the following:

- The component count and component IDs are unchanged.
- Every main variant value exactly matches its recorded raw value.
- The main Values picker retains or gains the intended alphabetical order.
- `Letter` options equal the available uppercase groups followed by `0-9`.
- Every variant's `Letter` matches its first visible character.
- `x`, `y`, dimensions, grid row, and grid column are unchanged.
- No temporary property remains.

After the write succeeds, run a fresh read-only verification call. Report the value count, group order, assignment errors, numeric-group count, preserved geometry, and resulting defaults.

## Stop conditions

- On any `use_figma` error, stop and diagnose it before another write.
- Do not retry a schema-rebuild workaround without explicit approval when the previous attempt was rejected for risk.
- If exact option ordering is unavailable through the Plugin API, explain the limitation and ask before using visible sorting labels or another workaround.
