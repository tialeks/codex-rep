# 📦 sp-ui-prototyping · v3.0.0

👤 **Автор:** danilamesh

> React-прототипы на SP UI: API из установленных пакетов, совместимые версии из registry, точные ассеты и проверка поведения без дублирования контрактов.

---

## ✨ Что нового в v3.0.0

```
Добавлен sp-ui-fonts: выбор стабильной версии, публичные CSS-импорты нужных семейств и проверка фактически загруженных начертаний. Если стабильный Fonts-релиз отсутствует, агент сообщает ограничение; alpha используется только по явному запросу. Исторический S3-helper больше не является стандартным способом подключения. Уточнены обработка относительных font URL сборщиком, deployment base path и Vite serving allow list.
```

---

## 📖 Описание

Use when a product manager wants an interactive SP UI prototype in a standalone React project using npm or pnpm and published @yandex-adtech-int/sp-ui-core, sp-ui-theme, sp-ui-tokens, sp-ui-assets, and sp-ui-fonts packages. Includes component setup, responsive layouts, user flows, and browser verification. Not for changing or publishing the component library.
