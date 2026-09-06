# SP Figma — project instructions

- Follow [operating rules](docs/operating-rules.md) for task scope, authorization, and sources of truth.
- Complete requested work and routine verification without repeated approval questions. Ask only when missing information materially changes the result or an action exceeds the authorized scope.
- Use the relevant skill below; do not load every skill for every task. These repository skills supplement the installed Figma plugin instructions.

| Task | Skill |
| --- | --- |
| Design-system structure, variables, styles | `skills/design-system/SKILL.md` |
| Components, variants, properties | `skills/component-audit/SKILL.md` |
| User flows and interaction states | `skills/ux-analysis/SKILL.md` |
| Accessibility review or requested fixes | `skills/accessibility/SKILL.md` |
| Instance component-property edits | `skills/figma-automation/SKILL.md` |
| Alphabetical variant sorting / Letter grouping | `skills/ux-analysis/icn-var-sort/SKILL.md` |

- User instructions take precedence over project skill guidelines, within platform permissions. When a rule blocks requested work, identify its file and exact requirement, distinguish it from your interpretation, and complete unaffected work.
- Answer in Russian unless requested otherwise. Lead with the result, explain changes and verification briefly, and state concrete limitations. Do not claim a GitHub push, Figma change, or model-setting change without confirmation from the relevant tool.
- Keep verification proportional: inspect the actual changed properties or files; broaden checks only for an unresolved risk or required gate.
- Use independent concurrent reads when useful. Delegate to subagents only when requested or authorized by applicable instructions; avoid parallel writes to shared Figma state.
- `lib/framebase-design-system/` is a separate imported library. Its visual rules and tokens apply to that library and projects explicitly using it, not automatically to AdTech or other Figma files.
- Do not copy API model parameters into instruction files as if they changed the chat's selected model. Use the host's actual model settings when available.
