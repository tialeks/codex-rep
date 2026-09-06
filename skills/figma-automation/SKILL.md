---
name: figma-automation
description: Inspect and modify exposed component properties on Figma instances, including boolean properties such as Center Picture; use for instance-property edits.
---

# Figma Automation Skill

## Purpose

Rules for safe Figma automation through MCP and Figma Plugin API.

Follow [project operating rules](../../docs/operating-rules.md). Load the installed `figma-use` skill before using its tool; use the currently exposed API and tool schema.

## Component property modification

When modifying Figma component instances:

- Do not change child layer visibility directly if the element is controlled by a component property.
- Always inspect `instance.componentProperties` first.
- Boolean component properties must be changed through `instance.setProperties()`.

Resolve the exact property key from the current instance. Property suffixes are instance/component-specific; do not reuse IDs from a past example.

## Verified workflow

1. Receive Figma URL.
2. Extract `fileKey` and `nodeId`.
3. Inspect instance properties.
4. Find the exact component property key.
5. Apply `setProperties()`.
6. Validate the new value after mutation.

## Important

A component property is not the same as a layer visibility state.
Changing `.visible` may break component logic.
Prefer changing the property exposed by the component API.
