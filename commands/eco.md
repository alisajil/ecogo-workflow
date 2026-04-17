---
description: "eco go — friendly entry point for ecogo-workflow. Say what you want in plain English."
argument-hint: "go | go <what you want in plain English>"
---

Load and follow the `ecogo-workflow:ecogo` skill. The user invoked via the friendly `eco` alias — they may not know the op names.

Route via the **Natural-Language Routing** block in SKILL.md:
- If the argument is just `go` with nothing else → run the default-action decision ladder.
- If the argument is `go <free text>` → classify the free text against the intent table and route to the best-matching op.
- If classification is ambiguous → ask a short menu-style clarifying question, do NOT guess on destructive actions (ingest, correct, fetch, run, remove).

Preserve the rest of the user's text verbatim when passing it through to the routed op.
