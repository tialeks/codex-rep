# Подготовка генерации

Команды запускаются из корня плагина — три уровня выше этого файла.

## Запрос

Сохрани JSON рядом с результатами задания в рабочем каталоге вне пакета плагина. Это относится ко всем PNG, запросам, исполнениям и отчётам; `assets/` содержит только зарегистрированные источники. `userBrief` — исходная просьба, `settings` — точный снимок, `prompt` — только содержание сцен или адресная коррекция:

```json
{
  "schemaVersion": 1,
  "userBrief": "Груша-светильник",
  "settings": {
    "topic": "Груша-светильник", "subjects": "", "avoid": "",
    "settingsVersion": 3, "graphicType": "object", "count": 1,
    "detailLevel": "balanced", "arrangement": "auto",
    "camera": "three-quarter", "creativity": 3,
    "palette": "natural", "whiteBase": false,
    "materials": {"mode": "auto", "base": null, "accents": []},
    "background": "white", "effects": [], "recognizable": true
  },
  "prompt": "Груша служит основанием лампы; тонкая стойка держит складчатый абажур.",
  "referenceMode": "prompt",
  "userReferences": []
}
```

Снимок формы требует `schemaVersion: 1` и объект `settings`. Повреждённый снимок не заменяй брифом без настроек. Компилятор проверяет типы, допустимые сочетания и активные значения. Не меняй отвергнутый параметр молча. `transparent_background` берётся из `settings.background`; отдельное противоречивое указание отклоняется.

## Изображения на входе

- `referenceMode=prompt`: без автоматических стилевых изображений.
- `referenceMode=selected`: только `styleReferenceIds` из [sources.json](sources.json) и конкретная `referenceReason`.
- `userReferences`: массив `{path, role}`. CONTENT REFERENCE задаёт предмет, COMPOSITION REFERENCE — расположение, STYLE REFERENCE — стиль, MATERIAL REFERENCE — поверхность. Пути абсолютные. Не передавай карту поверхности как общий стиль.
- `editSource`: путь к PNG для правки; он становится первым EDIT SOURCE.
- `settings.reference.facets`: ровно один GUIDANCE REFERENCE по [контракту свойств](reference-guidance.md). Привязка `settings.reference.image` проверяется по SHA и добавляется автоматически.

При `materials.mode=selected` подготовка собирает выбранные карты в один MATERIAL REFERENCE: основа, затем акценты. Не дублируй карты вручную. Когда материалы берутся из GUIDANCE REFERENCE, лист неактивного ручного набора не добавляется. Копии, порядок, SHA и схема листа сохраняются в исполнении. Всего допускается пять входных изображений — бюджет процесса; лишнее не отбрасывается скрыто.

## Подготовка и отправка

```sh
python3 scripts/prepare_generation.py prepare --request /absolute/request.json --output /absolute/new-execution --quiet
python3 scripts/prepare_generation.py verify --execution /absolute/new-execution --expected-manifest-sha256 <PIN_FROM_PREPARE>
```

Сохрани `manifestSha256` из ответа prepare отдельно от изменяемых файлов исполнения. Это pin исходного состояния; не вычисляй новый SHA текущего manifest взамен. Он связывает снимок, промпт, версию профиля и копии входов. Verify не перекомпилирует задание новым кодом.

Просмотри входные изображения и передай встроенному imagegen точный объект аргументов verify. Не добавляй историю изображений. Полный промпт и manifest уже сохранены; повторный вывод в чат не нужен. Новая попытка требует новой директории. После переноса исполнения снова вызови verify для актуальных путей входов.

После реального вызова сохрани точные переданные аргументы в `actual-arguments.json`, затем свяжи фактический PNG:

```sh
python3 scripts/prepare_generation.py record-submission --execution /absolute/new-execution --expected-manifest-sha256 <PIN_FROM_PREPARE> --arguments /absolute/actual-arguments.json --generated-file /actual/returned.png
```

Для финальной [проверки результата](review-verification.md) нужен receipt с `--generated-file`: один ID вызова не связывает PNG с исполнением. Сохранение receipt не подтверждает визуальное качество.

Pin проверяет сохранённые файлы; согласованная подмена файлов и самого внешнего pin находится за пределами проверки.
