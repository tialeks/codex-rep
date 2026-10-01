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
| Прототип в вёрстке / Figma → React + TypeScript | `skills/figma-automation/figma-exact-react/SKILL.md` |
| Лого-шайба / объёмная иконка сервиса | `skills/figma-automation/service-shaiba/SKILL.md` |
| Instance component-property edits | `skills/figma-automation/SKILL.md` |
| Alphabetical variant sorting / Letter grouping | `skills/ux-analysis/icn-var-sort/SKILL.md` |

- User instructions take precedence over project skill guidelines, within platform permissions. When a rule blocks requested work, identify its file and exact requirement, distinguish it from your interpretation, and complete unaffected work.
- Answer in Russian unless requested otherwise. Lead with the result, explain changes and verification briefly, and state concrete limitations. Do not claim a GitHub push, Figma change, or model-setting change without confirmation from the relevant tool.
- Keep verification proportional: inspect the actual changed properties or files; broaden checks only for an unresolved risk or required gate.
- Use independent concurrent reads when useful. Delegate to subagents only when requested or authorized by applicable instructions; avoid parallel writes to shared Figma state.
- `lib/framebase-design-system/` is a separate imported library. Its visual rules and tokens apply to that library and projects explicitly using it, not automatically to AdTech or other Figma files.
- Do not copy API model parameters into instruction files as if they changed the chat's selected model. Use the host's actual model settings when available.

- Когда пользователь просит «собрать прототип в вёрстке», «сверстать прототип» или реализовать макет Figma в коде, сначала читать `skills/figma-automation/figma-exact-react/SKILL.md`. Если Figma node/selection или целевой стек не определены, уточнить недостающие данные; не менять существующий стек автоматически.

- Facet: по командам «открой плагин с генерацией», «открой плагин Саши», «давай сгенерируем иллюстрацию в плагине Саши» и смысловым производным читать `skills/figma-automation/Facet/plugins/reference-style-3d/skills/reference-style-3d/SKILL.md`. В браузерном чате открывать встроенную форму Facet; подтверждённые задания выполнять без повторной формы.

- Лёшин генератор: команды «Лешин генератор» и «Лёшин генератор», независимо от регистра, запускают `skills/figma-automation/sp-illustrations/skills/sp-illustrations/SKILL.md`. Если сюжет не задан, запросить бриф; если задан, выполнять штатный флоу. Использовать соседний навык `sp-illustrations-critic` для независимой проверки. Эти команды имеют приоритет над общими триггерами Facet и service-shaiba.
