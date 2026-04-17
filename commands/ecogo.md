---
description: "ecogo-workflow — one-word invocation. Run an op by name (init/compile/query/…), or just say what you want in plain English."
argument-hint: "<free text in plain English> | init <name> | migrate [--dry-run] | ingest <path|url> | compile [<path>] | query <question> | correct <page-slug> [<claim>] | rationale [<subcmd>] | eval [<question>] | gap [<question>] | fetch [<gap-id|question>] | learn [<subcmd>] | lint | run [<profile>] | remove <name>"
---

Load and follow the `ecogo-workflow:ecogo` skill.

Dispatch logic (the skill handles this internally — the command file just routes):
- **No arguments** → run the default-action decision ladder.
- **First argument matches a known op name** (`init`, `migrate`, `ingest`, `compile`, `query`, `correct`, `rationale`, `eval`, `gap`, `fetch`, `learn`, `lint`, `run`, `remove`) → invoke that op with the remaining arguments.
- **First argument does not match any op name** → treat the entire argument string as natural-language intent and route via the skill's Natural-Language Routing block.

Pass through all user arguments verbatim to the skill.
