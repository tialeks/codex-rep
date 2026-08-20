# Figma Automation Skill

## Purpose

Rules for safe Figma automation through MCP and Figma Plugin API.

## Component property modification

When modifying Figma component instances:

- Do not change child layer visibility directly if the element is controlled by a component property.
- Always inspect `instance.componentProperties` first.
- Boolean component properties must be changed through `instance.setProperties()`.

Example:

```javascript
instance.setProperties({
  "Center Picture#3143:11": true
});
```

## Verified workflow

1. Receive Figma URL.
2. Extract `fileKey` and `nodeId`.
3. Inspect instance properties.
4. Find the exact component property key.
5. Apply `setProperties()`.
6. Validate the new value after mutation.

## Example

Node:
`11635:134641`

Property:
`Center Picture#3143:11`

Result:
`false → true`

## Important

A component property is not the same as a layer visibility state.
Changing `.visible` may break component logic.
Prefer changing the property exposed by the component API.
