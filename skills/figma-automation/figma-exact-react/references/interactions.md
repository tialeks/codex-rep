# Interaction ledger

Complete one row for every prototype connection and every visible interactive state. Query the exact destination/state node instead of inferring it from a label or a familiar mobile pattern.

| Source node/state | Trigger | Action/destination | Transition | Duration/easing | Shared chrome | Scroll/focus result | Test assertion |
| --- | --- | --- | --- | --- | --- | --- | --- |
| exact node id + default/selected/etc. | tap, drag, after delay, scroll threshold | node id, overlay, swap, back, close | move/dissolve/smart animate, direction, overlay position | exact values from Figma | what stays static/outside animated panel | reset, preserve, lock, restore, focus target | initial, intermediate, final DOM/geometry |

## Procedure

1. Enumerate prototype connections from the target root, nested components, and variants.
2. Call design context for every destination frame and every visually distinct component state.
3. Record whether navigation is forward, back, modal, overlay, tab/state swap, or scroll-driven.
   Treat a same-page tab, filter, segmented control, or carousel selection as local state unless the prototype explicitly connects to a destination frame. Local state must not inherit route transition, remount the page, reset scroll, or create a second copy of shared chrome.
4. Record what is shared across the transition. Persistent status bars, headers, tab bars, and backgrounds must not accidentally inherit panel animation.
5. Record the exact direction, duration, easing, overlay placement, background treatment, and scroll/focus result exposed by Figma. Keep the source and destination colors, crops, opacity endpoints, and geometry identical to Figma; never exaggerate them to advertise the transition.
6. Implement source, intermediate animated, and settled states. Test all three. A correct CSS declaration is insufficient when an interaction helper waits until the transition is almost complete; sample the intermediate state through input that returns immediately.
7. Add Playwright assertions for panel transforms/animation names or computed geometry during motion, then final route/state, shared chrome position, and restored/preserved scroll.
8. Assign one state owner and one DOM owner to every shared control. Assert that only one visible header/tab bar/navigation instance exists before and after transitions.
9. Exercise drag, swipe, and horizontal scroll with real browser input. A positive `scrollWidth - clientWidth` or an `overflow-x: auto` declaration is only precondition evidence; assert the selected carousel state or `scrollLeft` actually changes.

If Figma exposes a control but no destination or motion property, implement only its evidenced semantic state and report the missing connection as a blocker. Do not invent conventional mobile behavior unless the user explicitly supplies it.
