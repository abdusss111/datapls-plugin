#!/usr/bin/env python3
"""Build the datapls Claude Code plugin from an MCP settings dump.

Input: the JSON from the admin MCP tab («Дамп») — {"settings": {...},
"skills": [{"name", "description", "parent", "enabled", "hidden", ...}]}.

Output (next to this script's parent dir by default):
  .claude-plugin/plugin.json   manifest
  .mcp.json                    the datapls MCP server (OAuth login on first use)
  skills/datapls-analyst/      how to work with datapls at all
  skills/<name>/               one pointer per server skill: Claude picks it by
                               description, the body is loaded live from the
                               server with loadSkill, so edits in the admin
                               reach users without rebuilding the plugin
  commands/analyze.md          /datapls:analyze <question>

Also writes dist/datapls-<version>.zip — the file to upload on claude.ai
(Customize → Plugins → Add → Upload plugin).

Usage: python3 tools/build.py dump.json [--out DIR] [--version X.Y.Z]
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import zipfile
from pathlib import Path

PLUGIN_NAME = "datapls"
MARKETPLACE = "datapls"
REPO = "abdusss111/datapls-plugin"
MCP_URL = "https://api.datapls.io/mcp"
DESCRIPTION_MAX = 1024
NAME_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")

# Server skills that make no sense outside our own chat UI.
SKIP = {
    # Its body drives renderChart, which MCP does not serve; Claude draws charts itself.
    "generate-vega-chart",
}

ANALYST_SKILL = """\
---
name: datapls-analyst
description: {description}
---

# Аналитика datapls

Данные сети (продажи, промо, ассортимент, остатки, товародвижение, упущенные
продажи, OOS, доли полки, прогноз) доступны только через MCP-сервер datapls.
Набор его тулз зависит от настроек аккаунта: semantic layer (cubeMeta,
cubeSqlApi, queryResults, searchCertifiedQueries) или прямой ClickHouse
(clickhouse-sql). Пользуйся тем, что сервер отдал.

## Порядок работы
1. Найди методологию: вызови `listSkills`, выбери 1–3 скилла по `description`
   и загрузи их тела через `loadSkill`. Тело скилла обязательно к исполнению:
   его параметры, блоки анализа и порядок агрегации.
2. Если в скилле есть обязательный параметр (период, бренд, ТМ, партнёр), а
   пользователь его не назвал, спроси и остановись. Не подставляй всю сеть.
3. Если доступен `searchCertifiedQueries`, сначала поищи проверенный запрос по
   дословному вопросу пользователя и адаптируй его.
4. Имена view, мер и колонок бери только из ответов сервера (`cubeMeta`, схема
   в описании `clickhouse-sql`, DESCRIBE). Не выдумывай.
5. Независимые запросы отправляй параллельно. Агрегируй на стороне базы.

## Правила ответа
- Любая цифра — только из результата тулзы datapls. Нет данных — так и скажи.
- Кратко: вывод, затем ключевые цифры жирным, разбивки — таблицей.
- Валюта — тенге (₸). Укажи период и фильтры, по которым считал.
- Если datapls не подключён, попроси пользователя выполнить `/mcp` → datapls →
  Authenticate и войти логином datapls.
"""

ANALYST_DESCRIPTION = (
    "Розничная аналитика datapls: продажи, промо, ассортимент, остатки, "
    "товародвижение, упущенные продажи, OOS, доля полки, доля в категории, "
    "распричинка изменений, сравнение периодов (YoY, MoM, YTD) по сети, "
    "магазинам, городам, брендам и ТМ. Использовать для любого вопроса о "
    "цифрах и динамике розничных данных — до ответа загрузить данные через "
    "MCP-сервер datapls."
)

POINTER_SKILL = """\
---
name: {name}
description: {description}
---

# {name}

Методология «{name}» хранится на сервере datapls и может меняться — не
отвечай по памяти.

1. Вызови тулзу `loadSkill` MCP-сервера datapls с `name="{name}"` и выполни
   загруженное тело полностью: обязательные параметры, блоки, порядок расчёта.
2. Данные бери тулзами datapls (см. скилл datapls-analyst). Любая цифра —
   только из их результатов.
3. Если `loadSkill` недоступен — datapls не подключён: попроси пользователя
   выполнить `/mcp` → datapls → Authenticate.
"""

ANALYZE_COMMAND = """\
---
description: Ответить на вопрос по розничным данным datapls
argument-hint: <вопрос, например «почему упали продажи M&Ms в сентябре»>
---

Ответь на вопрос по данным datapls: $ARGUMENTS

Работай по скиллу datapls-analyst: подбери методологию через `listSkills` и
`loadSkill`, данные — только тулзами MCP-сервера datapls, недостающие
обязательные параметры уточни у пользователя.
"""

README = """\
# datapls — плагин для Claude

Подключает Claude к розничной аналитике datapls: MCP-сервер, методологии
(скиллы) и команду `/datapls:analyze`. Данные открываются только после входа
под аккаунтом datapls — доступ, права и источник данных задаются на сервере.

## Установка

**claude.ai и Claude Desktop:** Customize → Plugins → Add → Add marketplace →
`{repo}` → установить плагин **datapls**. Затем в карточке плагина вкладка
**Connectors** → datapls → Connect и войти логином datapls. Плагин сохраняется
в аккаунте Claude и появляется также в Desktop, Cowork и Claude Code.

**Claude Code:**

```bash
claude plugin marketplace add {repo}
claude plugin install {plugin}@{marketplace}
```

Затем `/mcp` → datapls → Authenticate.

## Что внутри

- `.mcp.json` — MCP-сервер `{mcp_url}`
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
описание. Версия {version}: {skill_count} скиллов.
"""


def yaml_str(text: str) -> str:
    """A YAML scalar that is safe for any text (JSON strings are valid YAML)."""
    return json.dumps(" ".join(text.split()), ensure_ascii=False)


def description(text: str) -> str:
    text = " ".join((text or "").split())
    if len(text) > DESCRIPTION_MAX:
        text = text[: DESCRIPTION_MAX - 1].rstrip() + "…"
    return yaml_str(text)


def pointer_skills(dump: dict) -> list[dict]:
    out = []
    for s in dump.get("skills") or []:
        name = str(s.get("name") or "")
        if not name or name in SKIP or not s.get("enabled", True) or s.get("hidden"):
            continue
        if not NAME_RE.match(name):
            raise SystemExit(f"Skill name not valid for Claude Code: {name!r}")
        if not (s.get("description") or "").strip():
            raise SystemExit(f"Skill {name!r} has no description to match on")
        out.append(s)
    return sorted(out, key=lambda s: s["name"])


def build(dump: dict, out: Path, version: str) -> int:
    for sub in ("skills", "commands", ".claude-plugin"):
        shutil.rmtree(out / sub, ignore_errors=True)
    skills = pointer_skills(dump)

    (out / ".claude-plugin").mkdir(parents=True)
    (out / ".claude-plugin" / "plugin.json").write_text(
        json.dumps(
            {
                "$schema": "https://anthropic.com/claude-code/plugin.schema.json",
                "name": PLUGIN_NAME,
                "version": version,
                "description": "Розничная аналитика datapls: MCP-сервер, методологии и команды",
                "author": {"name": "datapls"},
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n"
    )
    (out / ".claude-plugin" / "marketplace.json").write_text(
        json.dumps(
            {
                "name": MARKETPLACE,
                "description": "Плагины datapls для Claude",
                "owner": {"name": "datapls"},
                "plugins": [
                    {
                        "name": PLUGIN_NAME,
                        "source": "./",
                        "description": "Розничная аналитика datapls",
                        "version": version,
                    }
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n"
    )
    (out / ".mcp.json").write_text(
        json.dumps({"mcpServers": {"datapls": {"type": "http", "url": MCP_URL}}}, indent=2) + "\n"
    )

    analyst = out / "skills" / "datapls-analyst"
    analyst.mkdir(parents=True)
    (analyst / "SKILL.md").write_text(
        ANALYST_SKILL.format(description=description(ANALYST_DESCRIPTION))
    )
    for s in skills:
        d = out / "skills" / s["name"]
        d.mkdir(parents=True)
        (d / "SKILL.md").write_text(
            POINTER_SKILL.format(name=s["name"], description=description(s["description"]))
        )

    (out / "commands").mkdir()
    (out / "commands" / "analyze.md").write_text(ANALYZE_COMMAND)
    (out / "README.md").write_text(
        README.format(
            repo=REPO,
            plugin=PLUGIN_NAME,
            marketplace=MARKETPLACE,
            mcp_url=MCP_URL,
            skill_count=len(skills),
            version=version,
        )
    )
    return len(skills)


def make_zip(out: Path, version: str) -> Path:
    """The upload for claude.ai: one .claude-plugin/plugin.json at the archive root."""
    dist = out / "dist"
    dist.mkdir(exist_ok=True)
    target = dist / f"{PLUGIN_NAME}-{version}.zip"
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(out.rglob("*")):
            rel = path.relative_to(out)
            if path.is_dir() or rel.parts[0] in ("dist", "tools") or path.name == ".DS_Store":
                continue
            zf.write(path, rel.as_posix())
    return target


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("dump", type=Path, help="MCP settings dump (admin → MCP → «Дамп»)")
    ap.add_argument("--out", type=Path, default=Path(__file__).resolve().parent.parent)
    ap.add_argument("--version", default="0.1.0")
    args = ap.parse_args()
    n = build(json.loads(args.dump.read_text()), args.out, args.version)
    print(f"Built {PLUGIN_NAME} {args.version} at {args.out}: {n} skills + datapls-analyst")
    print(f"Upload for claude.ai: {make_zip(args.out, args.version)}")


if __name__ == "__main__":
    main()
