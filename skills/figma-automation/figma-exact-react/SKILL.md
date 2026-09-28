---
name: figma-exact-react
description: "Собрать или исправить конкретный Figma node как точный React + TypeScript интерфейс: прочитать anatomy, auto-layout и constraints, переиспользовать компоненты проекта, выгрузить оригинальные assets, реализовать состояния и проверить visual/responsive/interactions/build. Обращаться к скиллу по запросам «собрать прототип в вёрстке» и «сверстать прототип». Применять workflow, когда есть Figma node URL или доступная Figma selection и целевой стек React/TS; не использовать для screenshot-only, клонирования живого URL, не-Figma интерфейсов или общего frontend QA."
---

# Figma Exact React

Собирать реальный интерфейс из структуры Figma, а не визуальную оболочку по скриншоту. Figma — источник истины; код готов только после структурной, визуальной, responsive и runtime-проверки.

## Обязательные companion workflows

- До `get_design_context` загрузить официальный `figma-design-to-code` и передать его в `skillNames`, если этот параметр есть в текущей схеме инструмента.
- Для rendered QA загрузить `frontend-testing-debugging`, если он доступен; иначе выполнить описанные ниже проверки доступными средствами. Соблюдать текущие инструкции инструментов Browser и Playwright.
- При существенных React-изменениях следовать проектным правилам и активному React best-practices skill.

## Жёсткие правила

1. Сначала вызвать `get_design_context` для точного node. Screenshot и metadata не заменяют design context.
2. Сохранить стек, tokens, компоненты, шрифты и архитектуру проекта. Figma-generated code — только reference.
3. Не угадывать asset, crop, constraint, variant, interaction или effect: читать вложенный node. Неразрешимая неизвестность — blocker.
4. Скачивать точные Figma assets локально. Не рисовать SVG/path вручную, не заменять glyph Unicode и не оставлять временные MCP URL.
5. Переводить anatomy, fill/hug/fixed, min/max, clip и ancestor dependencies, а не подгонять один viewport.
6. Не использовать screenshot всего экрана как UI и не скрывать ошибки clipping-ом.
7. Не объявлять готовность по одному build.
8. Повторяемый Figma-компонент имеет один invariant shell; контент и состояния передавать props/data. Карточки одной rendered-строки при stretch равны высоте максимальной карточки.
9. Сложную декоративную композицию без собственной семантики, интерактивности и независимых constraints экспортировать одним asset. Не растрировать текст, controls, целые карточки или экран.
10. Сохранять aspect ratio и Figma image transform. Не растягивать bitmap по двум осям без явного доказательства из Figma.
11. Gesture-driven visuals вычислять непрерывно из pointer/scroll progress; commit state происходит после release, но background, scale и position меняются во время drag.
12. При отклонённой fidelity или просьбе пересобрать войти в clean-room: старые UI dimensions/assets считать недостоверными, перечитать Figma и заменить целевую часть связно.
13. Для sheet, modal, overlay, card и glass-surface воспроизводить полный стек fills/effects снизу вверх. Полупрозрачный декоративный градиент не заменяет непрозрачный базовый fill; backdrop blur не делает поверхность непрозрачной. До приёмки проверить поверх контрастного контента, что подложка просвечивает только там и настолько, как задано в Figma.

## Workflow

### 1. Зафиксировать контракт

- Распарсить `fileKey` и `nodeId`; изучить ближайший `AGENTS.md`, scripts, routes, components, tokens, fonts, assets и tests.
- Записать: node и source viewport, проверяемые ширины, fixed/sticky поведение, anatomy/constraints, typography features, asset policy, states/interactions и publication scope.
- До аудита спросить только о выборе, который меняет платформу, состав экранов, внешний эффект или архитектуру. Не спрашивать то, что видно в Figma/репозитории.

### 2. Провести аудит до кода

- Прочитать [references/anatomy.md](references/anatomy.md) полностью и составить zone map, anatomy ledger, constraint matrix, content contract и invariant/variant contract.
- Для длинного frame читать first-level zones и сложные nested nodes отдельно; один уменьшенный screenshot не является доказательством деталей.
- Прочитать [references/assets.md](references/assets.md) полностью и классифицировать каждый visual node: `DOM`, `SVG`, `ORIGINAL_IMAGE` или `COMPOSITE_PNG`.
- Для states, overlays, tabs, carousel, drag/swipe и connected screens прочитать [references/interactions.md](references/interactions.md) полностью и составить interaction ledger.
- После полного аудита задать только вопросы о противоречиях, которые Figma и проект не разрешают. До их ответа не реализовывать спорную часть.

### 3. Собирать dependency-ordered slices

Собирать shared primitives/chrome → один representative slice → остальные sections/states. После каждого high-risk slice запускать узкую проверку и показывать preview; это ловит ошибку общего компонента до размножения.

- Auto-layout переводить в flex/grid с теми же axis, order, gap, padding, align, wrap и growth.
- Для каждой поверхности записывать порядок compositing: base fill → дополнительные fills/gradients/images → stroke → opacity/blend → backdrop/filter → shadow. Не схлопывать несколько Figma fills в один приблизительный CSS-gradient, если меняется итоговая прозрачность.
- Сохранять parent/child/sibling relationships и clip owner.
- Shared header, tab bar, bottom nav, carousel и stateful control имеют одного DOM/state owner.
- Реальные controls делать semantic controls. Tabs/filters/segmented controls менять local state без route animation, remount и scroll reset, если Figma не доказывает обратное.
- Horizontal scroller: rounded parent владеет clipping, inner track — content padding; проверять реальным input.
- Sticky header: проверить scroll root и всех ancestors на `overflow`, transform и containment.
- Использовать exact font files, variation axes, OpenType и `font-variant-numeric`; отдельно сверять повторяющиеся нули и соседний currency/points asset.
- Responsive выводить из constraints и dependency equations. Не вводить произвольные breakpoints или hard min-width.

### 4. Проверить содержимое и границы

- Для repeated component прогнать short/long/empty content, разрешённое число строк, числовые значения и существующие disabled/loading/error/selected states.
- Props использовать для независимых значений; variants — только для устойчивых комбинаций, меняющих anatomy/behavior. Не плодить variant для каждого текста.
- В каждом viewport проверить page overflow, intentional inner scroll, текстовые переносы, crop, equal-height rows, fixed/sticky chrome и последний scroll item с требуемым нижним воздухом.

### 5. Запустить deterministic QA

Прочитать [references/visual-qa.md](references/visual-qa.md) полностью.

Запустить применимые проверки:

```bash
node <skill-dir>/scripts/verify-source.mjs --root "$PWD"
node <skill-dir>/scripts/verify-render.mjs --root "$PWD" --url <url> --widths <widths> --height <height> --out /tmp/figma-render --page-selector <selector> --ready-selector <selector> --font-contract "<family>=<font-file>"
node <skill-dir>/scripts/pixel-diff.mjs --root "$PWD" --reference <figma.png> --actual <render.png> --diff <diff.png> --result <result.json> --max-ratio 0.04 --regions "<name>:<x>:<y>:<width>:<height>"
```

Дополнить project-specific browser tests для anatomy, content edges, responsive dependencies и interactions. Если заявляется a11y, подтвердить реальный DOM через html-validate, axe-core и Lighthouse; собственное рассуждение не считается проверкой.

## Completion gates

Не писать «готово», пока применимое не выполнено:

- root и нужные nested nodes прочитаны; ledger/matrix/contracts не содержат неизвестных visible properties;
- все assets/fonts локальные, точные, декодируются и видимы; composite экспортирован целиком и не искажён;
- repeated shells едины, equal-height измерен по каждой rendered-строке, content edge cases не ломают anatomy;
- source viewport и все заданные ширины прошли visual/zone inspection без overflow, clipping, overlap и distortion;
- tabs/navigation/scroll/sticky/drag проверены реальными browser interactions, включая intermediate drag state;
- source audit, build, typecheck, tests и релевантный lint прошли; diff не содержит посторонних файлов.

Если gate недоступен, назвать его непроверенным и объяснить причину. Threshold — сигнал, а не разрешение оставить видимый mismatch.

## Итоговый отчёт

Сначала сообщить, прошла ли реализация проверки. Указать nodes/flow, изменённые файлы, viewports, visual diff по критическим зонам, команды и оставшиеся deviations/blockers. QA screenshots/diffs хранить вне репозитория, если пользователь не попросил иное.
