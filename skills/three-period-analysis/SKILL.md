---
name: three-period-analysis
description: "Включать при любом запросе метрики с периодом. Скилл делает 3 сравнения, YoY, MoM, YTD. Все они обязательны."
---

# three-period-analysis

Методология «three-period-analysis» хранится на сервере datapls и может меняться — не
отвечай по памяти.

1. Вызови тулзу `loadSkill` MCP-сервера datapls с `name="three-period-analysis"` и выполни
   загруженное тело полностью: обязательные параметры, блоки, порядок расчёта.
2. Данные бери тулзами datapls (см. скилл datapls-analyst). Любая цифра —
   только из их результатов.
3. Если `loadSkill` недоступен — datapls не подключён: попроси пользователя
   выполнить `/mcp` → datapls → Authenticate.
