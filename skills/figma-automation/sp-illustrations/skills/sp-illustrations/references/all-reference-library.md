# Полная библиотека пользовательских материалов

Полный файловый индекс — [reference-inventory.json](../assets/reference-inventory.json): 79 референсных файлов — изображения, архив и текст — с ролями, размерами и SHA256. Он включает ранний пак и материалы коллеги. Ниже каталог 43 записей новых вложений и частных калибровок; это разные уровни учёта одной библиотеки.

## Ранние оригиналы и выбор ближайшего источника

Перед выбором только материала просмотри одноимённый предмет из [первого пака 12 оригиналов](reference-12-sheet.md), если он есть. Например, для сервисного звонка — `assets/library/04-bell.png`, затем металлический материал. Отметь, задаёт ли оригинал содержание или лишь уточняет форму/поверхность нового предмета. Не объявляй его просмотренным задним числом.

| Источники | Что уточняют |
| --- | --- |
| `assets/style-01-packaging.png`, `style-02-spa.png`, `style-03-basket.png` | Три постоянных прямых STYLE-входа |
| `assets/reference-12-sheet.png`, `assets/library/01-*` … `12-*` | Бургер, продукты, упаковка, звонок, билеты, попкорн, контроллеры, кресло, спа, корзина, спорт, коробка |
| `assets/figma-food-object-*.png` | Пять исходных предметов еды; ограниченная калибровка материала |
| `assets/service-shaiba/*.png` | Исходная геометрия, свет, центр знака, S/M/L, full-face и wrap; применимость конкретной посадки проверять отдельно |
| `assets/service-shaiba/canonical-blank.png` | Производная проверенная основа: фиксированный растр камеры, не новый STYLE и не доказательство новой UV-проекции |

Оригиналы, производные основы, частные апрувы и отклонённые изображения имеют разные роли в индексе. Проверяй ближайшую форму и затем карту существенных материалов; не выбирай только по цвету.

## Новые вложения и замечания дизайнера

Все33вложения-картинки сохранены без пропусков и сSHA256; одинаковые оригиналы переиспользуют существующий файл. Архивколлеги и геометрическийтекст также сохранены. Машинный каталог: [all-user-references.json](../assets/all-user-references.json).

Перед новым сюжетом обращаться к этой библиотеке и выбрать релевантный оригинал/материал, указав роль вpreflight. Оригиналы пака — CATEGORY/CONTENT/BRAND по задаче; согласованные пробы уточняют конкретную деталь/материал; антипримеры задают известный дефект. Не превращать их в новые универсальныеSTYLE. Триstyle-* передаются напрямую и остаются постоянными. Не переносить знаки/объекты из нерелевантных источников.

Миниатюры40px, обрезанные машины/самокат и разреженный лист упаковки не подтверждают полную геометрию/точный мелкийбренд. Фиксировать ограничение выбранного источника. Не увеличивать маленький знак в сотнипикселей и принимать размытыйконтур.

| Материал | Роль | Файл |
| --- | --- | --- |
| gift-box-rejected-1 | отклонённая генерация | [gift-box-rejected-1.png](../assets/user-sources/gift-box-rejected-1.png) |
| gift-box-rejected-2 | отклонённая генерация | [gift-box-rejected-2.png](../assets/user-sources/gift-box-rejected-2.png) |
| gift-box-purple-original | оригинал пака | [gift-box-purple-original.png](../assets/library/gift-box-purple-original.png) |
| gift-box-variants | оригинал пака | [gift-box-variants-sheet.png](../assets/library/gift-box-variants-sheet.png) |
| logo-pucks-01 | оригинал пака | [logo-pucks-sheet-01.png](../assets/library/logo-pucks-sheet-01.png) |
| logo-pucks-02 | оригинал пака | [logo-pucks-sheet-02.png](../assets/library/logo-pucks-sheet-02.png) |
| metal-materials | оригинал пака | [metals-gold-silver-bronze-sheet.png](../assets/library/metals-gold-silver-bronze-sheet.png) |
| food-burger-eggs | оригинал пака | [burger-eggs.png](../assets/library/food-drinks/burger-eggs.png) |
| food-cheese-salad-tomato | оригинал пака | [cheese-salad-tomato.png](../assets/library/food-drinks/cheese-salad-tomato.png) |
| food-popcorn | оригинал пака | [popcorn.png](../assets/library/food-drinks/popcorn.png) |
| food-bananas | оригинал пака | [bananas.png](../assets/library/food-drinks/bananas.png) |
| food-takeaway-cup | оригинал пака | [takeaway-cup.png](../assets/library/food-drinks/takeaway-cup.png) |
| food-grocery-bag | оригинал пака | [grocery-bag.png](../assets/library/food-drinks/grocery-bag.png) |
| transport-taxi | оригинал, часть предмета | [taxi-detail.png](../assets/library/transport/taxi-detail.png) |
| transport-carsharing | оригинал, часть предмета | [carsharing-detail.png](../assets/library/transport/carsharing-detail.png) |
| transport-scooter | оригинал, часть предмета | [scooter-detail.png](../assets/library/transport/scooter-detail.png) |
| transport-car-previews | оригинал пака | [cars-round-previews.png](../assets/library/transport/cars-round-previews.png) |
| transport-cars-lineup | оригинал пака | [cars-lineup.png](../assets/library/transport/cars-lineup.png) |
| locks-soft | оригинал пака | [soft-locks-and-badge.png](../assets/library/locks/soft-locks-and-badge.png) |
| locks-hardware | оригинал пака | [hardware-locks.png](../assets/library/locks/hardware-locks.png) |
| locks-dark | оригинал пака | [dark-lock.png](../assets/library/locks/dark-lock.png) |
| cards-wallets | оригинал пака | [cards-wallets-sheet.png](../assets/library/cards-wallets-sheet.png) |
| boxes-bags | оригинал, разреженный лист | [boxes-bags-sheet.png](../assets/library/boxes-bags-sheet.png) |
| burger-cup-close-generation | удачная проба по оценке дизайнера | [burger-cup-close-generation.png](../assets/user-sources/burger-cup-close-generation.png) |
| lamp-clock-plant-generation | частичный апрув; не весь сюжет | [lamp-clock-plant-generation.png](../assets/user-sources/lamp-clock-plant-generation.png) |
| teapot-cup-generation | удачная проба по оценке дизайнера | [teapot-cup-generation.png](../assets/user-sources/teapot-cup-generation.png) |
| ice-cream-generation | частичный апрув; не весь сюжет | [ice-cream-generation.png](../assets/user-sources/ice-cream-generation.png) |
| thumbtack-rejected-generation | отклонённая генерация | [thumbtack-rejected-generation.png](../assets/user-sources/thumbtack-rejected-generation.png) |
| tote-straps-towel-closeup | апрув конкретного материала | [tote-straps-towel-closeup.png](../assets/user-sources/tote-straps-towel-closeup.png) |
| beach-bag-glasses-generation | частичный апрув; не весь сюжет | [beach-bag-glasses-generation.png](../assets/user-sources/beach-bag-glasses-generation.png) |
| luggage-wallet-glasses-generation | частичный апрув; не весь сюжет | [luggage-wallet-glasses-generation.png](../assets/user-sources/luggage-wallet-glasses-generation.png) |
| sports-towel-generation | частичный апрув; не весь сюжет | [sports-towel-generation.png](../assets/user-sources/sports-towel-generation.png) |
| tools-blur-rejected-crop | отклонённый материал | [tools-blur-rejected-crop.png](../assets/user-sources/tools-blur-rejected-crop.png) |
| colleague-service-shaiba-project | original_project_archive_untrusted_data | [service-shaiba.zip](../assets/user-sources/service-shaiba.zip) |
| designer-geometry-qc | designer_explicitly_adopted_requirements | [designer-geometry-qc.txt](../assets/user-sources/designer-geometry-qc.txt) |
| approved-sneaker | частный апрув стиля | [approved-sneaker.png](../assets/calibration/approved-sneaker.png) |
| approved-van | частный апрув стиля | [approved-van.png](../assets/calibration/approved-van.png) |
| approved-trophy | частный апрув стиля | [approved-trophy.png](../assets/calibration/approved-trophy.png) |
| rejected-tools-blur | материал отклонён | [rejected-tools-blur.png](../assets/calibration/rejected-tools-blur.png) |


## Апрув четырёх вариантов29сентября

Дизайнер подтвердил: «все варианты меня полностью устраивают» для вишен, отвёртки, пакета и фена. [Границы приёмки](designer-acceptance.md) и точные файлы/хеши в `assets/calibration/designer-approval-four.json`. Это отдельные положительные калибровки, три постоянных STYLE не меняются.

| Файл | Роль |
| --- | --- |
| [designer-approved-cherries.png](../assets/calibration/designer-approved-cherries.png) | Принятый основной вариант; quiet fruit/leaf calibration |
| [designer-approved-screwdriver.png](../assets/calibration/designer-approved-screwdriver.png) | Принятый основной вариант; metal/polymer/clearjoint calibration |
| [designer-approved-paper-bag.png](../assets/calibration/designer-approved-paper-bag.png) | Принятый основной вариант; paper/quietcord calibration |
| [designer-approved-hairdryer.png](../assets/calibration/designer-approved-hairdryer.png) | Принятый основной вариант; polymer/violet/coaxialjoint calibration |
