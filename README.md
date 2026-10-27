# datapls — плагин для Claude

Подключает Claude к розничной аналитике datapls: MCP-сервер, методологии
(скиллы) и команду `/datapls:analyze`. Данные открываются только после входа
под аккаунтом datapls — доступ, права и источник данных задаются на сервере.

## Установка

**claude.ai и Claude Desktop:** Customize → Plugins → Add → Add marketplace →
`abdusss111/datapls-plugin` → установить плагин **datapls**. Затем в карточке плагина вкладка
**Connectors** → datapls → Connect и войти логином datapls. Плагин сохраняется
в аккаунте Claude и появляется также в Desktop, Cowork и Claude Code.

**Claude Code:**

```bash
claude plugin marketplace add abdusss111/datapls-plugin
claude plugin install datapls@datapls
```

Затем `/mcp` → datapls → Authenticate.

## Что внутри

- `.mcp.json` — MCP-сервер `https://api.datapls.io/mcp`
- `skills/datapls-analyst` — как работать с данными datapls
- `skills/<имя>` — методологии: Claude выбирает их по описанию, тело грузится
  с сервера через `loadSkill`, поэтому правки методологии доходят без обновления
- `commands/analyze.md` — `/datapls:analyze <вопрос>`

## Сборка (для разработчиков datapls)

```bash
# админка → Agent v3 → MCP-сервер → «Дамп» → mcp-settings-*.json
python3 tools/build.py ~/Downloads/mcp-settings-*.json --version X.Y.Z
git commit -am "datapls X.Y.Z" && git push
```

Пересборка нужна, только если скилл добавили, переименовали или поменяли
описание. Версия 0.1.0: 16 скиллов.
