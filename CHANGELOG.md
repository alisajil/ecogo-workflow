# Changelog

All notable changes to `ecogo-workflow` are documented here. Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Versioning follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html). The project is pre-1.0, so MINOR version bumps may include breaking changes — read the notes before upgrading.

## [0.3.0] — 2026-04-17

### Breaking

- **Removed `/eco go` (two-word) invocation.** The single-word `/ecogo` is now the only entry point.
- **Deleted `commands/eco.md`.** If you referenced the old command in scheduled tasks or saved prompts, replace `/eco go ...` with `/ecogo ...`. Behavior is otherwise identical.

### Changed

- **`commands/ecogo.md` rewritten as unified entry point.** A single `/ecogo` command accepts three argument shapes:
  - `/ecogo` (no args) → runs the default-action decision ladder
  - `/ecogo <op-name> ...` → invokes one of the 13 operations (init, migrate, ingest, compile, query, correct, rationale, eval, gap, fetch, learn, lint, run, remove)
  - `/ecogo <free text>` → routes via Natural-Language Routing to the right op or bundled skill
- Fully-qualified form `/ecogo-workflow:ecogo <anything>` still works and is identical.

### Updated

- 43+ references renamed across `README.md` + `SKILL.md` + bundled-skill provenance headers.
- Version strings bumped from `0.2.0` to `0.3.0` in provenance comments of the two bundled skills.

---

## [0.2.0] — 2026-04-17

### Added

- **Bundled `brainstorming` skill** (MIT © Jesse Vincent, redistributed with attribution). Use `/ecogo-workflow:brainstorming` to walk a new-feature idea through clarifying dialogue, approach tradeoffs, design spec, and self-review. Enforces a hard gate: no code until the design is approved.
- **Bundled `subagent-driven-development` skill** (MIT © Jesse Vincent, redistributed with attribution). Use `/ecogo-workflow:subagent-driven-development` after a written plan exists to dispatch a fresh subagent per task with two-stage review (spec compliance then code quality) and a fix-review loop.
- **Intelligent skill orchestration** in the Natural-Language Router. Four new routing rows cover:
  - Memory recall intents (checks filed queries → episodic-memory → the base's query op)
  - Design intents (routes to bundled `brainstorming`)
  - Execution intents (routes to bundled `subagent-driven-development`)
  - Full chained flows (e.g. "build me X from scratch" chains design → plan → execute with user gates at each link)
- **Skill Orchestration subsection** documenting the three routing axes — retrieval, design, execution — and how skills layer.
- **Self-Improvement Loop subsection** documenting how observations → learn distill → user accept → runtime overlay → schema promotion actually works end to end.
- **Autonomous Flows subsection** stating exactly what the plugin will do without asking (safe idempotent work) vs what requires user confirmation (side-effectful work, memory mutations).
- **Decision-ladder step 7**: surface pending proposed learnings for user review.
- **Model Selection and Token Budget section** (SKILL.md):
  - Per-task-class model routing: Haiku 4.5 for mechanical work, Sonnet 4.6 for standard, Opus 4.7 for deep reasoning
  - Token-budget discipline rules: no re-reading skill files mid-op, batched observation emissions, capped report sizes, lean LLM prompts
  - Response brevity defaults: announce-and-do, not announce-explain-do
  - Claude Code effort-mode awareness: fast mode degrades gracefully, extended-thinking mode enforces full discipline, Opus allowed longer chains
- **Per-profile model policy for `ecogo run`**:
  - `cheap` — Haiku only (compile + lint + frontmatter)
  - `default` — mixed per task class
  - `expensive` — Sonnet baseline with Opus escalation on conflicts
  - `canary` — Haiku smoke test
- **Beginner-friendly README** rewritten with Mac + Windows step-by-step setup guides, first-15-minutes walkthrough, and common developer workflow recipes.

### Changed

- Help Summary in SKILL.md extended with the new capabilities (design intents, execution intents, chained flows, learn-from-self).
- README now leads with use cases (ADRs, onboarding, runbooks, post-mortems, API doc drift, technical debt ledger) rather than a generic knowledge-base framing.
- Plugin description in both `plugin.json` and `marketplace.json` updated to *"Self-correcting engineering knowledge base for software teams"*.

---

## [0.1.0] — 2026-04-17

Initial public release on GitHub.

### Added

- **Thirteen operations** covering the knowledge-base lifecycle:
  - `init` — scaffold a new knowledge base
  - `migrate` — upgrade a base to the current schema (idempotent, additive; v1 and v2 markers layered)
  - `ingest` — save a source (URL or file) to `raw/`
  - `compile` — synthesise cross-linked pages with a bounded 3-iteration self-critique loop
  - `query` — answer a question with `[[wikilink]]` citations
  - `correct` — re-ground a page against cited sources and declared source-roots; three-way grounding outcome (grounded / miscited / ungrounded / contradicted)
  - `rationale` — extract the *why* (tradeoffs, alternatives, historical, gotcha) as inline Obsidian callouts with promote-to-entity clustering
  - `eval` — score the base against a defined question set with per-run judging and regression detection
  - `gap` — stage open knowledge gaps from lint reports, compile-unresolved flags, eval misses, and follow-up prose
  - `fetch` — pull external sources to close open backlog items
  - `learn` — roll up recurring observations into proposed rules with five-section lifecycle (Observing / Proposed / Accepted / Rejected / Promoted)
  - `lint` — audit for dead links, orphan pages, missing sections
  - `run` — composer that chains ops into profiled pipelines (default / cheap / expensive / canary) with 30-min time budget and idempotency gate
  - `remove` — delete a base cleanly
- **Natural-Language Router** — `/eco go <text>` (superseded by `/ecogo` in v0.3.0) maps plain English onto operations.
- **Learning Subsystem** — observation emission catalogue with 10 rationale-specific classes plus generic observation classes; accepted-rules overlay read at op start by every op.
- **Rationale Extraction pipeline** — regex pre-pass (strong + weak + negative markers) + LLM judge + cluster-to-entity promotion at similarity ≥ 0.85. Four kinds: tradeoff, alternative, historical, gotcha. Confidence rubric: high, medium, low.
- **Self-critique loop inside `compile`** — bounded 3-iteration, break conditions (converged / no-progress / budget exhausted), strict fix table that never fabricates replacements.
- **Source-roots fallback** in `correct` — accurate-but-miscited claims get their citation fixed instead of deleted.
- **Golden test harness** in `tests/rationales/` — tolerant YAML comparator (`compare.py`) with text-substring + kind + min-confidence matching; shell harness (`run-golden.sh`) with pre-flight checks; 5 expected YAMLs (4 positive + 1 control).
- **Deterministic lint script** — `scripts/lint-kb.py` for structural checks (dead links, orphans, missing sections).
- **SessionStart hook** — auto-installs `qmd` (hybrid BM25 + vector search) and `marp-cli` (slide export) via `scripts/install-deps.sh`.

### Licensing

- MIT License, Copyright © 2026 Ali Sajil.

---

[0.3.0]: https://github.com/alisajil/ecogo-workflow/releases/tag/v0.3.0
[0.2.0]: https://github.com/alisajil/ecogo-workflow/releases/tag/v0.2.0
[0.1.0]: https://github.com/alisajil/ecogo-workflow/commit/5b7a500
