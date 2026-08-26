# Loopframe Design System

Единый автономный UI-kit для Framebase, Mockupservice, Loopframe Studio и следующих сервисов. В архиве лежат компоненты, токены, шрифты, анимации, 50 сервисных логотипов и исходники Morphicons/Thinking Logos.

## Быстрый старт

```bash
npm install
npm run build
npm run select-logo -- --target /путь/к/вашему-проекту
```

Мастер спросит, какой логотип использовать, и создаст в проекте:

- `public/brand-logo.svg` — основной знак;
- `public/favicon.svg` — тот же знак для вкладки;
- `public/brand-loader-mark.svg` — прозрачный центральный символ для Thinking Logo;
- `src/loopframe-brand.ts` — готовая конфигурация бренда.

Без интерактивного вопроса: `npm run select-logo -- --logo nova --target ../my-service`.

## Подключение

```tsx
import { BrandProvider, BrandLogo, BrandThinkingLogo, Button } from "@loopframe/design-system";
import "@loopframe/design-system/styles.css";
import { loopframeBrand } from "./loopframe-brand";

export function App() {
  return <BrandProvider brand={loopframeBrand}>
    <main className="lf-root"><BrandLogo/><Button>Продолжить</Button><BrandThinkingLogo state="working"/></main>
  </BrandProvider>;
}
```

В `index.html` оставьте `<link rel="icon" type="image/svg+xml" href="/favicon.svg">`.

## Что внутри

- Компоненты: Surface, Button, IconButton, LoadingButton, SegmentedControl, SliderDetents, Toggle, Accordion.
- Motion kit: BlurReveal, FadeUp, TiltCard, MagneticButton, ColorSelector, FluidDotOrbit.
- Локальный MorphingIcon с готовыми парами menu/close, play/pause, plus/check и стрелками. Режим уменьшения движения включён всегда.
- BrandThinkingLogo использует выбранный знак и состояния `thinking`, `searching`, `working`, `solving`, `listening`, `waiting`, `generating`.
- Токены: точные тёмные поверхности, типографика YS Text, сетка 4 px, радиусы, размеры контролов, тени, focus и motion presets.
- `references/` — контрольные реализации трёх исходных проектов для проверки будущих изменений.

## Правила

1. Все экраны живут внутри `.lf-root`; не переопределяйте токены точечно в компонентах.
2. Отступы берутся из `--lf-space-*`, высоты — из `--lf-control-*`, радиусы — из `--lf-r-*`.
3. Интерактивная анимация обязана учитывать `prefers-reduced-motion`; готовые компоненты уже учитывают.
4. Для загрузки используйте BrandThinkingLogo/LoadingButton: в анимацию попадёт не цветной квадрат, а отдельная форма выбранного знака.
5. Новый сервис сначала прогоняет `select-logo`, после чего использует один `loopframeBrand` во всём приложении.

Сторонние исходники и лицензии описаны в `THIRD_PARTY_NOTICES.md`.
