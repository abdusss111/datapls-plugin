---
name: lost-sales-distribution
description: "Упущенные продажи из-за неполной дистрибуции SKU: ассортиментные дыры и их потенциал."
---

# lost-sales-distribution

Методология «lost-sales-distribution» хранится на сервере datapls и может меняться — не
отвечай по памяти.

1. Вызови тулзу `loadSkill` MCP-сервера datapls с `name="lost-sales-distribution"` и выполни
   загруженное тело полностью: обязательные параметры, блоки, порядок расчёта.
2. Данные бери тулзами datapls (см. скилл datapls-analyst). Любая цифра —
   только из их результатов.
3. Если `loadSkill` недоступен — datapls не подключён: попроси пользователя
   выполнить `/mcp` → datapls → Authenticate.
