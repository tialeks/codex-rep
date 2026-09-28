# Asset strategy

Прочитать до реализации любого экрана с изображениями, иконками или сложной декоративной графикой.

## Классификация

Каждый visible visual node отнести ровно к одному типу:

| Тип | Когда использовать | Что зафиксировать |
| --- | --- | --- |
| `DOM` | текст, control, container, layout surface, независимо responsive элемент | node, semantics, constraints |
| `SVG` | единичная точная vector/icon/logo нода | node, intrinsic/rendered size |
| `ORIGINAL_IMAGE` | uploaded bitmap без реконструкции | image asset, crop, object-fit/position |
| `COMPOSITE_PNG` | сложное декоративное subtree без собственной семантики/интерактивности | root node, scale, intrinsic/rendered bounds, anchor |

Не flatten-ить subtree с live text, controls, independently constrained children или анимацией внутренних частей.

## Export routing

1. Обычный реальный node экспортировать стандартным Figma asset API.
2. Uploaded bitmap брать из original image asset.
3. Если точная overridden-композиция доступна только как instance descendant path вида `I…;…`, найти фактическую Plugin API ноду в read-only режиме и вызвать `exportAsync` на полном safe-to-flatten subtree.
4. Ошибка обычного API на instance path означает сменить export route, а не собрать композицию из DOM-слоёв.

## Проверка

- Сохранить asset локально; временный MCP URL не допускается.
- Для requested scale (например, PNG @3x) проверить decoded pixel dimensions.
- Разделять intrinsic bitmap bounds, exported-node bounds и rendered/clipping bounds.
- Проверить aspect ratio, transparent padding, nontransparent bounds, object-fit и object-position.
- На всех widths картинка должна сохранять доказанный размер/пропорцию и anchoring; fixed artwork внутри fluid stage не становится fluid автоматически.
- Composite должен рендериться одним `<img>`/image element. Его DOM-реконструкция считается отклонением без отдельного Figma-доказательства.
