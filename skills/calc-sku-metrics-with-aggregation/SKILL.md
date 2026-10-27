---
name: calc-sku-metrics-with-aggregation
description: "Включать при расчёте Количество SKU в промо / в ассортименте."
---

# calc-sku-metrics-with-aggregation

Методология «calc-sku-metrics-with-aggregation» хранится на сервере datapls и может меняться — не
отвечай по памяти.

1. Вызови тулзу `loadSkill` MCP-сервера datapls с `name="calc-sku-metrics-with-aggregation"` и выполни
   загруженное тело полностью: обязательные параметры, блоки, порядок расчёта.
2. Данные бери тулзами datapls (см. скилл datapls-analyst). Любая цифра —
   только из их результатов.
3. Если `loadSkill` недоступен — datapls не подключён: попроси пользователя
   выполнить `/mcp` → datapls → Authenticate.
