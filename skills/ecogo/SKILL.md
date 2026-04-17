---
name: ecogo
description: >-
  ecogo-workflow — self-improving, compounding knowledge base inside Obsidian.
  Use when the user says "/ecogo-workflow:ecogo", "/eco", "eco go", "ecogo init",
  "ecogo migrate", "ecogo ingest", "ecogo query", "ecogo correct", "ecogo eval",
  "ecogo gap", "ecogo fetch", "ecogo learn", "ecogo lint", "ecogo run", "ecogo rationale",
  or asks about managing a knowledge base. ALSO use when the user asks plain
  questions that imply workflow operations: "is this page wrong?", "fix the
  base", "what's out of date?", "save this article", "tell me about X",
  "what should I work on next?".
argument-hint: init <name> | migrate [--dry-run] | ingest <path|url> | compile [<path>] | query <question> | correct <page-slug> [<claim>] | rationale [<subcmd>] | eval [<question>] | gap [<question>] | fetch [<gap-id|question>] | learn [<subcmd>] | lint | run [<profile>] | remove <name> | (plain English via "eco go ...")
---

# ecogo-workflow

Self-improving, compounding knowledge base inside an Obsidian vault.

## Operations

```
/ecogo-workflow:ecogo init my-topic
/ecogo-workflow:ecogo migrate           # existing wiki → current schema (idempotent)
/ecogo-workflow:ecogo correct auth-flow-design "session TTL"
/ecogo-workflow:ecogo ingest ~/ObsidianVault/03-Resources/my-topic/raw/article.md
/ecogo-workflow:ecogo ingest https://example.com/article
/ecogo-workflow:ecogo query "how does our auth flow work"
/ecogo-workflow:ecogo eval
/ecogo-workflow:ecogo gap "what's our retry strategy for the payment API?"
/ecogo-workflow:ecogo fetch
/ecogo-workflow:ecogo learn
/ecogo-workflow:ecogo rationale                      # backfill rationale for concept pages
/ecogo-workflow:ecogo rationale provider-integration-pattern   # re-extract one page
/ecogo-workflow:ecogo lint
/ecogo-workflow:ecogo run

# Friendly entry — no op names required
/eco go                                     # do the smart thing for current state
/eco go tell me about the auth flow           # → query
/eco go the deployment runbook looks out of date     # → correct (after slug resolution)
/eco go save this RFC <url>             # → ingest
/eco go audit the engineering docs                      # → lint
/eco go what should I work on               # → print open backlog items

```

---

## Active Wiki Detection

Walk up from `cwd` looking for a directory containing **both** `CLAUDE.md` and a `wiki/` subfolder.

1. Start at `cwd`. Check if `CLAUDE.md` and `wiki/` exist in the current directory.
2. If found → that directory is the **active wiki root**. Read `CLAUDE.md` for schema.
3. If not found → move to parent directory and repeat until filesystem root.
4. If no wiki found anywhere in the path, prompt the user:
   > "Which wiki should I use?"
   List available wikis by running: `ls -d ~/ObsidianVault/03-Resources/*/wiki 2>/dev/null`
   and presenting the parent directory names.

---

## qmd Availability

Reference paths used throughout this skill:

```
QMD="env -u BUN_INSTALL ${CLAUDE_PLUGIN_DATA}/node_modules/.bin/qmd"
MARP="${CLAUDE_PLUGIN_DATA}/node_modules/.bin/marp"
```

**Check:** Test if `"${CLAUDE_PLUGIN_DATA}/node_modules/.bin/qmd"` exists and is executable via Bash: `test -x "${CLAUDE_PLUGIN_DATA}/node_modules/.bin/qmd"`.

**Important:** Always invoke qmd via `env -u BUN_INSTALL` to force Node.js runtime. If `BUN_INSTALL` is set in the environment, qmd runs under Bun, which uses a SQLite build without extension loading support and cannot load sqlite-vec.

- **If present:** use it for `query` and `embed` operations. ALWAYS use the full path — never bare `qmd`.
- **If absent:** fall back to reading `wiki/index.md` manually and grepping wiki files.

---

## Learning Subsystem

The wiki records recurring issues it encounters and uses them to evolve its own behavior over time. Two files back this:

- **`outputs/learnings-raw.jsonl`** — append-only log of individual observations emitted by `compile`, `lint`, `eval`, `fetch`, and `gap`. Never read during normal operation.
- **`outputs/learnings.md`** — human-readable synthesis: patterns (grouped observations), their status, proposed rules, and promotion history. Read at the start of every op as a runtime overlay.

### Observation emission

Whenever `compile`, `lint`, `eval`, `fetch`, or `gap` encounters an issue from the catalog below, append one JSON object (one line) to `outputs/learnings-raw.jsonl`:

```json
{"ts":"<ISO8601>","op":"<operation>","class":"<class-name>","evidence":{<op-specific context: page slug, question, url, etc.>}}
```

**Starter class catalog** (keep class names kebab-case, specific, and stable — `ecogo learn` groups by exact string match):

| Class | Emitted by | When |
|-------|-----------|------|
| `ungrounded-claim` | compile | Critique pass found a factual claim with no wikilink to a source-summary. |
| `fabricated-claim` | compile | Critique pass found a claim not present in any raw source. |
| `omitted-entity` | compile | Critique pass found a source-mentioned entity with no page and no wikilink. |
| `critique-noconverge` | compile | Self-critique loop exhausted its 3-iteration budget without reaching 0 issues. |
| `dead-link` | lint, compile | A `[[wikilink]]` points to a file that does not exist in `wiki/`. |
| `orphan-page` | lint | Page has no inbound links (excluding index.md / log.md). |
| `stale-page` | lint | Page with `status: stale` frontmatter older than 90 days. |
| `eval-regression` | eval | Run's `mean_score` dropped vs the previous run. |
| `eval-complete-zero` | eval | A question scored `complete=0` in the current run. |
| `fetch-zero-sources` | fetch | A gap was fetched but every candidate failed the filter. |
| `fetch-spam-rejected` | fetch | A candidate URL was dropped for spam / off-topic / login-walled content. |
| `backlog-skip` | gap | User moved an item to `## Skipped`. |
| `manual-correction` | correct | `ecogo correct` removed or replaced claims on a page. |
| `raw-source-missing` | correct, compile | A cited raw source file could not be found on disk. |
| `correction-declined` | correct | `correct` found no claim to fix — all claims were grounded. Recurrences on the same page suggest stale sources. |
| `claim-miscited` | correct | Claim is accurate per `source-roots` grep but the cited sources don't contain it. Fix = add the discovered source to the page's `## Sources`, optionally ingest it as a source-summary. Recurring miscites flag a compile gap (sources weren't fully captured). |
| `route-ambiguous` | natural-language routing | A free-text input didn't map confidently to any op; the router asked the user to clarify. |
| `rationale-extracted` | compile, rationale | A rationale object was produced and rendered. Evidence: `{page_slug, kind, confidence}`. |
| `rationale-missing-per-marker` | compile, rationale | Regex fired but LLM judge returned empty. Evidence: `{source_slug, marker_hits}`. Over time signals marker noise. |
| `rationale-deleted-by-user` | lint, correct, rationale delete | Inline rationale callout was present at last snapshot and is absent now. Evidence: `{page_slug, text_hash, kind, confidence, age_days, reason?}`. |
| `rationale-promoted-to-entity` | compile, rationale promote | Inline callout replaced with wikilink to a new `rationale-<slug>.md` entity page. Evidence: `{page_slug, new_entity_slug, explicit?}`. |
| `rationale-llm-malformed` | compile, rationale | LLM judge returned unparseable JSON after one retry. Evidence: `{source_slug, raw_response_first_200_chars}`. |
| `rationale-fabrication-attempt` | compile, rationale | LLM returned a rationale whose `source_excerpt` is not a verbatim substring of the input window. Evidence: `{source_slug, claimed_excerpt}`. Rejected; never rendered. |
| `rationale-no-anchor` | compile, rationale | Rationale produced but its `fact_anchor` did not match any concept page. Dropped. Evidence: `{attempted_anchor, source_slug}`. |
| `rationale-cross-page-contradiction` | compile, rationale, lint | Two pages have contradictory rationales for the same fact anchor. Evidence: `{page_slugs, fact_anchor, kind}`. Directly feeds S3 gotcha detection. |
| `rationale-rate-limited` | compile, rationale | A source produced more than 40 candidate windows; only top 40 were judged. Evidence: `{source_slug, candidate_count}`. |
| `rationale-budget-exceeded` | compile, rationale | Op hit the 100-LLM-call-per-invocation budget before finishing. Evidence: `{pages_remaining, total_llm_calls}`. |
| `other` | any | Novel pattern not in catalog — include a free-text `description` inside `evidence`. |

Emission is **best-effort**: if the file can't be opened, skip silently. Observations are auxiliary — they never block or error the primary operation.

### Accepted-rules overlay

At the start of every op (right after reading `CLAUDE.md`), open `outputs/learnings.md` if it exists and read the `## Accepted` section. Treat each accepted learning's `Proposed rule:` text as an **additional constraint** for this operation, applied alongside SKILL.md and CLAUDE.md rules.

This is how the wiki evolves behaviorally without editing this skill file. A rule observed ≥ 5 times → proposed by `ecogo learn` → accepted by the user → automatically applied on every subsequent run. A rule may later be *promoted* into the wiki's `CLAUDE.md` to become permanent schema.

If `outputs/learnings.md` does not exist, skip the overlay — the op still runs normally.

---

## Rationale Extraction

A compile-time pass (step 3.5) plus a dedicated retroactive op (`ecogo rationale`) that captures the *why* behind factual claims on concept pages. Implements sub-project S1 of the plugin's intelligence-upgrade roadmap.

See **`skills/ecogo/references/rationale-extraction.md`** for the full regex catalog, LLM judge prompt shape, confidence rubric, callout render format, insertion rules, promote-to-entity criteria, entity-page template, frontmatter schema, and delete-signal detection logic. The reference is the normative source — this section is the in-skill summary.

### Pipeline summary

1. **Regex pre-pass** on source prose finds candidate windows (3-sentence spans around rationale markers: `because`, `tradeoff`, `we chose X over Y`, `instead of`, etc.). Skips code blocks, tables, frontmatter, HTML comments.
2. **LLM judge pass** receives each window and returns a JSON array of rationale objects (possibly empty — most hits are incidental). Each object: `{text, kind, confidence, fact_anchor, source_excerpt}`. `kind` ∈ `{tradeoff | alternative | historical | gotcha | other}`.
3. **Validation** — reject any rationale whose `source_excerpt` is not a verbatim substring of its window; emit `rationale-fabrication-attempt`. Retry malformed JSON once; then emit `rationale-llm-malformed` and skip.
4. **Insertion** — on the target concept page, the rationale renders as an Obsidian callout (`[!NOTE]` for tradeoff/alternative/historical/other; `[!WARNING]` for gotcha) placed after the first paragraph matching `fact_anchor` via exact substring, token overlap ≥ 0.6, or qmd semantic fallback.
5. **Promote-to-entity** — after all extractions for a run, cluster rationales by text similarity (overlap ≥ 0.85) + same `kind`. Clusters of ≥ 3 distinct concept pages become a `wiki/rationale-<slug>.md` entity page; inline callouts are replaced with a `[[rationale-<slug>]]` wikilink. Sets `has-rationale-entity: true` on each concept page.
6. **Observations** — emit from the catalog in the Learning Subsystem section. See the reference doc for the full list of rationale-* classes.

### Rate limits and budgets

- Max 40 candidate windows per source (top 40 by marker strength if exceeded; emit `rationale-rate-limited`)
- Max 100 LLM judge calls per op invocation (emit `rationale-budget-exceeded` and commit partial if hit)
- Default behaviour can be tuned per-wiki via accepted-learnings rules (filter by kind, raise/lower thresholds, etc.)

### Frontmatter schema v2 (additive)

Concept pages gain three fields (all optional; v1 tooling ignores them):

```yaml
rationale-count: <int>
rationale-tags: [tradeoff, alternative, ...]
has-rationale-entity: true|false
```

The `ecogo migrate` op includes `<!-- ecogo-migrate: v2 applied YYYY-MM-DD -->` as the v2 marker. Idempotent; layers on top of v1.

### Dependencies

- Learning Subsystem (observations, accepted-rules overlay) — existing.
- `correct` op — gains rationale rubric (strict on `source_excerpt`, loose on `text`).
- qmd — used for `fact_anchor` semantic fallback.
- `outputs/rationales/snapshot.json` + `outputs/rationales/deleted.json` — per-wiki state, created on first rationale extraction.

---

## Natural-Language Routing

When the skill is invoked via `/eco go`, via `eco go ...` in a user message, or with no subcommand at all (bare `/ecogo-workflow:ecogo`), do **not** assume a specific op. Route based on intent using the logic below.

### Default action (invoked without free text: `eco go` alone)

Run the first applicable branch of this decision ladder. Announce which branch fired before doing the work: `"Base state: <reason>. Running <op>."`

1. **Uncompiled raw sources exist** (`raw/articles/*.md` whose slug has no matching `wiki/<slug>.md`) → `ecogo compile`.
2. **Pages flagged `[!WARNING] unverified`** (from scheduled re-verification or prior correction) → print the list and suggest `ecogo correct <page-slug>` for each. Do not auto-correct without confirmation.
3. **Most recent lint report older than 7 days** → `ecogo lint`.
4. **Eval baseline exists AND last eval older than 7 days** (`outputs/evals/questions.md` has no `[REPLACE]` placeholders AND last line of `outputs/evals/history.jsonl` is > 7 days old) → `ecogo eval`.
5. **Backlog has ≥ 1 open item with priority `high`** → `ecogo fetch` (top high-priority item).
6. **New observations since last distill** (`outputs/learnings-raw.jsonl` modified after last `## [YYYY-MM-DD] learn` in `log.md`) → `ecogo learn`.
7. **Proposed learnings pending user review** (entries in `outputs/learnings.md` under `## Proposed`) → surface the top 3 with one-line summaries and ask user to accept/reject. Do not auto-accept.
8. **None of the above** → print `"Base is idle. Nothing urgent."` plus a friendly list of what the user could do: seed eval questions if placeholders remain, ingest a source, run `ecogo eval` for a fresh baseline, start a design with `eco go design <topic>`, etc. Do NOT run any op.

### Free-text routing (`eco go <free text>`)

Classify the free text against the intent table. If a row matches confidently, invoke the routed op with the extracted arguments. If no row matches confidently or the action is destructive, ask a short clarifying question first.

| Intent clues (any of, case-insensitive) | Route | Extraction |
|-----------------------------------------|-------|-----------|
| "what is", "how does", "tell me about", "explain", "why is", "who is", "when did" | `ecogo query "<free text>"` | Pass the full free text minus the leading command word. |
| "save", "remember this", "add this", "ingest", "import", "save this article" + a URL or path | `ecogo ingest <url\|path>` | Extract the first URL or file path. If none, ask: "Where is the content? Paste a URL or file path." |
| "is X wrong", "X looks wrong", "fix X", "correct X", "update X", "X is out of date" where X names a wiki page | `ecogo correct <page-slug> [<specific-claim>]` | Resolve X to a page slug via qmd search. If ambiguous, list top 3 matches and ask which one. Extract any quoted phrase or trailing clause as `<specific-claim>`. |
| "check everything", "audit the wiki", "clean up", "what's broken", "any issues" | `ecogo lint` | No args. |
| "score", "grade the wiki", "quality check", "how good is the wiki" | `ecogo eval` | No args (full question set). |
| "what's pending", "what should I work on", "backlog", "todo list", "open items" | **Do not invoke an op.** Read `outputs/backlog.md`, print the `## Open` section filtered to top 10 items with a one-line summary at the top. |
| "find sources on X", "pull info about X", "research X", "get articles on X" | `ecogo gap "<topic>"` then `ecogo fetch <new-gap-id>` | Two-step. Announce both.  |
| "delete X", "remove X", "throw away X" | **Confirm first.** If X is a wiki name: `ecogo remove <name>`. If X is a page: prompt the user to confirm deletion, then delete the page file (no op wraps this — it's a direct file delete). Never auto-delete. |
| "run the daily thing", "run everything", "do the updates", "tick" | `ecogo run` (default profile) | No args. |
| "what can you do", "help", "commands", "how does this work" | Print a plain-English help block (see Help Summary below). No op invocation. |
| "remember: <fact>" / "note: <fact>" | `ecogo ingest` (inline mode — save the fact as a short raw/articles/ note with user attribution) | Use today's date and a slug derived from the first 5 words. |
| "how did we decide X", "what did we discuss about X", "remind me about X", "do you remember X" | **Memory-first recall.** Step 1: check `wiki/queries/` for a prior filed answer to a similar question (match by slug overlap). Step 2: if the `episodic-memory:search-conversations` skill is available, invoke it. Step 3: fall back to `ecogo query` against the wiki. Announce which step hit. |
| "design X", "new feature Y", "let's build Z", "how should we approach X", "spec out X", "brainstorm X" | **Invoke the `brainstorming` skill.** Run `/ecogo-workflow:brainstorming <free text>`. The skill has its own hard-gate (no code until design approved) — respect that gate even under autonomous flow. Pass the free text verbatim. |
| "implement the plan", "execute the tasks", "run the implementation plan at <path>", "build it" (when a plan already exists) | **Invoke the `subagent-driven-development` skill.** Run `/ecogo-workflow:subagent-driven-development` with the most recent plan path from `docs/superpowers/plans/` (or the path named in the free text). This skill dispatches fresh subagents per task with two-stage review. |
| "build me X from scratch", "design and ship X", "take me from idea to code on X" | **Chained flow: brainstorming → plan → subagent-driven-development.** Announce the chain. Invoke `brainstorming` first. After its design spec is approved, the brainstorming skill itself will hand off to the writing-plans convention. After a plan exists, invoke `subagent-driven-development`. User approves each gate. |

### Skill orchestration (how the plugin picks among its own ops and bundled skills)

The plugin's thirteen ops handle the knowledge-base lifecycle (ingest, compile, query, correct, etc.). The **bundled third-party skills** handle the work that a knowledge base can't do on its own — designing new features, recalling prior conversations, executing plans task-by-task. The router chooses among them along three axes:

1. **Retrieval axis** — when the user is looking for information:
   - Look it up in the base → `ecogo query`
   - Recall from prior Claude Code conversations → `episodic-memory:search-conversations` (if available)
   - Recall from a filed query → read `wiki/queries/<slug>.md` directly (no op)
   - Do all three in that order and compose the result. Prefer the fastest source that has an answer.

2. **Design axis** — when the user is going to build something new:
   - Single-question clarification → answer directly
   - Multi-step new feature → `/ecogo-workflow:brainstorming` (bundled). Respects its own HARD-GATE: no code until the design is approved.
   - After a design is approved, the brainstorming skill itself terminates by handing off to the writing-plans workflow; the plan file lands in `docs/superpowers/plans/`.

3. **Execution axis** — when a plan already exists and the user wants it built:
   - Small single-file edit → apply directly
   - Multi-task plan → `/ecogo-workflow:subagent-driven-development` (bundled). Dispatches a fresh subagent per task with two-stage review (spec compliance then code quality) and a fix-review loop.
   - Single-session parallel independent tasks → use `superpowers:dispatching-parallel-agents` if installed; otherwise serial subagent-driven-development.

Skills layer cleanly. A single "take this from idea to shipped code" ask becomes:

```
brainstorming  →  writing-plans  →  subagent-driven-development  →  (optional) compile into the base as an ADR
                                                                     (runs ecogo compile with the plan + spec as sources)
```

Announce the chain before starting each link. Respect each skill's own gates. The plugin is an orchestrator, not a gate-skipper.

### Self-improvement loop

Already built in — this subsection makes the mechanics visible so autonomous flows can use them:

1. **Every op emits observations** (`ecogo compile`, `ecogo lint`, `ecogo eval`, `ecogo correct`, `ecogo fetch`, `ecogo gap`) into `outputs/learnings-raw.jsonl` per the **Learning Subsystem** section above.
2. **`ecogo learn` distills** raw observations by class. When a class crosses the threshold (default: ≥5 in 30 days), the distill drafts a proposed rule and moves the entry to `## Proposed`.
3. **User accepts or rejects** via `ecogo learn accept <L-id>` / `reject <L-id>`. Accepted rules become a runtime overlay read by every op.
4. **Promote to schema** via `ecogo learn promote <L-id>` once a rule has proven stable. The rule is appended to the base's `CLAUDE.md` and becomes permanent behavior.

This loop is what makes the plugin behave better over time per wiki without editing this shipped SKILL.md. The **default-action decision ladder** includes `ecogo learn` (step 6) so recurring observations get distilled on idle ticks, and step 7 surfaces pending proposals for user review. Routing decisions themselves can be tuned: if the user consistently rejects a route, emit an observation with class `route-ambiguous` and `learn` will eventually propose a new routing rule.

### Autonomous flows

What the plugin will do without asking (safe, observational, idempotent):

- **Read operations**: `query`, `rationale list`, `learn list`, `lint` (findings only), backlog listings, default-action ladder traversal, `eval` when a baseline exists and is stale.
- **Idempotent compile**: `compile` of already-staged `raw/articles/*.md` with `compiled: false`. Content is grounded; self-critique catches fabrication.
- **Observation emission**: all ops emit observations without asking.
- **`learn` distill**: rolling raw observations into `## Observing` / `## Proposed` is safe. Accepting/rejecting is not.
- **Scheduled runs** (`ecogo run` composer) within their idempotency gate.

What **requires user confirmation** (has side effects, external I/O, or writes to memory):

- `ingest <url>` — fetches external content into `raw/`.
- `fetch <gap>` — same, goes to the web.
- `correct` of a page — modifies a wiki page's content.
- `remove <name>` — destroys a whole base.
- `learn accept` / `learn reject` / `learn promote` — changes what the plugin will do on future runs.
- `brainstorming` approval gates — the skill's HARD-GATE is never skipped autonomously.
- `subagent-driven-development` task dispatch — first task always confirmed; subsequent tasks within a single plan can proceed without re-confirming if accepted-learnings have granted it.

The guiding principle: **the plugin automates the parts that are safe because they are observable (everything it does writes to `log.md` and emits observations), and asks for approval on the parts where a wrong call would cost the user real time or money.**

### Disambiguation

If the free text doesn't cleanly match, ask a short menu question:

> "Did you want to (1) look something up, (2) fix something that looks wrong, (3) save new information, (4) audit the engineering docs's health, or (5) something else?"

For routes where a wrong guess is cheap (query, lint, eval, backlog listing): try your best guess and announce the assumption: `"Assuming you want to look this up — running ecogo query. If that's wrong, say 'no, I meant <X>'."`

For routes where a wrong guess is costly (ingest, correct, fetch, run, remove): **always confirm before acting.** A wrong ingest pollutes `raw/`. A wrong correct rewrites a page. A wrong remove deletes a wiki.

### Help Summary (plain-English)

When asked "help" or "what can you do", print something like:

> **This plugin can:**
> - **Look things up** — ask a question in plain English. Checks prior filed answers + past conversations (if episodic-memory available) + the base, in that order.
> - **Remember new things** — paste a URL or file path, say "save this".
> - **Fix itself** — say "is X wrong" or "fix X" and it re-grounds the page against its cited sources and declared code repositories.
> - **Check itself** — say "audit" or "check everything" to find broken links, outdated pages, missing sections.
> - **Grade itself** — say "score the base" once evaluation questions are defined.
> - **Find gaps** — say "what should I work on" to see the open backlog.
> - **Pull new sources** — say "find info about X" to search the web and stage sources for next compile.
> - **Design new features** — say "design X" or "new feature Y" and it runs the brainstorming skill (hard-gate: no code until design is approved).
> - **Execute a plan** — say "implement the plan" or "build it" when a written plan already exists; dispatches subagents per task with two-stage review.
> - **Take an idea from zero to shipped code** — say "build me X from scratch" and it chains design → plan → execute with a gate at each step.
> - **Learn from itself** — every op emits observations. Recurring patterns become proposed rules you accept or reject. Accepted rules apply to every future run.
>
> **Most-used triggers:**
> - `eco go` — do the smart thing for current state
> - `eco go <question>` — look something up (memory-first)
> - `eco go fix <page name>` — correct a page
> - `eco go save <url>` — ingest a source
> - `eco go design <feature>` — start a brainstorm
> - `eco go build me <feature> from scratch` — full chained workflow
> - `eco go audit the engineering docs` — lint
> - `eco go what should I work on` — show backlog
> - `eco go` (alone, on a cron) — autonomous upkeep tick

---

## `init <name>`

Create a new wiki scaffold under the Obsidian vault.

### Steps

1. **Check if wiki already exists:**
   If `~/ObsidianVault/03-Resources/<name>/` exists, abort with:
   "Wiki '<name>' already exists at ~/ObsidianVault/03-Resources/<name>/. Use `ecogo remove <name>` first, or choose a different name."

2. Create directory structure:
    ```bash
    mkdir -p ~/ObsidianVault/03-Resources/<name>/raw/articles
    mkdir -p ~/ObsidianVault/03-Resources/<name>/raw/attachments
    mkdir -p ~/ObsidianVault/03-Resources/<name>/wiki/queries
    mkdir -p ~/ObsidianVault/03-Resources/<name>/outputs/reports
    mkdir -p ~/ObsidianVault/03-Resources/<name>/outputs/evals
    mkdir -p ~/ObsidianVault/03-Resources/<name>/outputs/runs
    ```

3. Write `~/ObsidianVault/03-Resources/<name>/CLAUDE.md` using the **CLAUDE.md template** below (fill in `<name>`).

4. Write `~/ObsidianVault/03-Resources/<name>/wiki/index.md` using the **index.md template** below.

5. Write `~/ObsidianVault/03-Resources/<name>/log.md` using the **log.md template** below.

6. Write `~/ObsidianVault/03-Resources/<name>/.gitignore` using the **.gitignore template** below.

7. Write `~/ObsidianVault/03-Resources/<name>/qmd.yml` using the **qmd.yml template** below.

8. **Seed evaluation questions.** Prompt the user:
   > "Optionally, what are 3-10 questions this wiki should eventually answer well? These become the eval set for `ecogo eval` to measure progress. (Press enter to skip — you can edit `outputs/evals/questions.md` anytime.)"

   Write `~/ObsidianVault/03-Resources/<name>/outputs/evals/questions.md` using the **questions.md template** below. If the user provided questions, substitute them for the `[REPLACE]` placeholder bullets. If the user skipped, keep the placeholders (eval will refuse to run until they are replaced — that's deliberate).

9. **Create empty backlog.** Write `~/ObsidianVault/03-Resources/<name>/outputs/backlog.md` using the **backlog.md template** below. The backlog is where `ecogo gap` stages detected knowledge gaps and `ecogo fetch` records which gaps have been worked on.

10. **Seed the learning subsystem.** Write `~/ObsidianVault/03-Resources/<name>/outputs/learnings.md` using the **learnings.md template** below. Do NOT create `outputs/learnings-raw.jsonl` — ops create it on first emission. The subsystem activates automatically as observations accumulate.

11. Commit to vault git:
    ```bash
    git -C ~/ObsidianVault add "03-Resources/<name>/" && git -C ~/ObsidianVault commit -m "init: <name> wiki"
    ```

12. If qmd available:
    ```bash
    "${QMD}" collection add ~/ObsidianVault/03-Resources/<name>/wiki --name <name> && "${QMD}" embed --collection <name>
    ```

13. Print Web Clipper setup instruction:
     ```
     Obsidian Web Clipper setup:
     1. Install: https://obsidian.md/clipper
     2. In clipper settings, set Destination folder to:
        03-Resources/<name>/raw/articles
     3. Set filename template to: {{date:YYYY-MM-DD}}-{{title}}
     4. After clipping, run: /ecogo-workflow:ecogo ingest ~/ObsidianVault/03-Resources/<name>/raw/articles/<clipped-file>.md
     ```

---

## `migrate [--dry-run]`

Bring an existing wiki up to the current schema. Creates missing data files and directories, appends missing rule sections to the wiki's `CLAUDE.md`, and records a version marker so subsequent migrations layer cleanly.

**Idempotent:** running twice is a no-op the second time (the version marker makes migrate exit early). Safe to run on a wiki created by a newer plugin version — it reports "already at v1" and does nothing.

**Scope:** migrate is **purely additive**. It never rewrites existing `CLAUDE.md` content or deletes files. Customizations are preserved.

### Steps

1. **Detect active wiki.** Read `CLAUDE.md`.

2. **Check migration markers.** Search `CLAUDE.md` for the latest marker in this precedence order:
   - `<!-- ecogo-migrate: v2 applied -->` → wiki is at v2. Print "Wiki already at schema v2. Nothing to do." and exit.
   - `<!-- ecogo-migrate: v1 applied -->` → wiki is at v1. Proceed with v1→v2 delta only (skip v1 creation steps).
   - Neither marker → wiki is pre-v1. Proceed with full v1→v2 migration in order.

3. **Plan changes.** Build three lists:

   a. **Data files/dirs** — for each of the following, record "create" if missing, "skip (exists)" otherwise:
      - `outputs/evals/` directory
      - `outputs/evals/questions.md` file
      - `outputs/backlog.md` file
      - `outputs/learnings.md` file
      - `outputs/runs/` directory

   b. **CLAUDE.md Directory Layout additions** — for each path literal (`outputs/evals/`, `outputs/backlog.md`, `outputs/learnings-raw.jsonl`, `outputs/learnings.md`, `outputs/runs/`): record "add line" if the literal does not appear anywhere in the existing `## Directory Layout` section, "skip (already listed)" otherwise.

   c. **CLAUDE.md rule sections** — for each of `## Eval Rules`, `## Gap Rules`, `## Fetch Rules`, `## Learning Rules`, `## Run Rules`, `## Correction Rules`, `## Source Roots`, `## Rationale Rules` (v2 addition): record "append" if the heading does not appear in `CLAUDE.md`, "skip (already present)" otherwise.

   d. **v2 additions** (when upgrading v1 → v2 or applying a pre-v1 migration):
      - **Data dir** `outputs/rationales/` — record "create" if missing.
      - **Frontmatter hint** — nothing in CLAUDE.md changes for frontmatter; v2 frontmatter fields (`rationale-count`, `rationale-tags`, `has-rationale-entity`) are additive and documented only in SKILL.md and the rationale reference. Record nothing for frontmatter in the plan table.

4. **If `--dry-run`:** print the three plans as tables. Write nothing. Exit.

5. **Execute the plan, in order:**

   a. **Create missing directories** with `mkdir -p`.

   b. **Create missing data files** from the templates in this skill (see **Templates** section):
      - `outputs/evals/questions.md` ← **questions.md template** (placeholder `[REPLACE]` bullets; user edits later).
      - `outputs/backlog.md` ← **backlog.md template**.
      - `outputs/learnings.md` ← **learnings.md template**.
      - Do **not** create `outputs/learnings-raw.jsonl` — ops create it on first observation emission.

   c. **Update `CLAUDE.md` Directory Layout in place.** For each "add line" entry: insert a new bullet inside the `## Directory Layout` block, positioned immediately before the `- log.md` line (conventionally the last entry). Use the exact descriptions from the **CLAUDE.md template in `init` step 3**. Preserve every existing line byte-for-byte.

   d. **Append missing rule sections to `CLAUDE.md`.** For each flagged section: append the corresponding block from the **CLAUDE.md template in `init` step 3** verbatim. Order: Eval Rules → Gap Rules → Fetch Rules → Learning Rules → Run Rules → Correction Rules → Source Roots. Skip any section already present.

   e. **Append the version marker** as the last line of `CLAUDE.md`. If the wiki was pre-v1, write both markers sequentially (v1 first, then v2 on the following line). If the wiki was at v1, append only the v2 marker.
      ```
      <!-- ecogo-migrate: v1 applied YYYY-MM-DD -->
      <!-- ecogo-migrate: v2 applied YYYY-MM-DD -->
      ```

   f. **Create v2 data dir** if planned in step 3d:
      ```bash
      mkdir -p outputs/rationales
      ```

6. **Append to `log.md`:**
   ```
   ## [YYYY-MM-DD] migrate | v1 schema | <N> files/dirs created, <L> layout lines added, <M> sections appended
   Files: <comma-list>. Sections: <Eval Rules | Gap Rules | ...>.
   ```

7. **Commit:**
   ```bash
   git -C ~/ObsidianVault add "03-Resources/<wiki-name>/" && git -C ~/ObsidianVault commit -m "migrate: <wiki-name> to v1 schema"
   ```

8. **Print** the executed plan (annotated with "done"), then the recommended next steps for an existing wiki:
   - "Open `outputs/evals/questions.md` and replace the `[REPLACE]` placeholders with 3-10 real evaluation questions for this wiki."
   - "Run `ecogo eval` to establish a baseline score."
   - "Run `ecogo gap` (scan mode) to stage backlog items from the latest lint/compile reports and any 'Suggested follow-ups' or 'TODO' prose in log.md and wiki pages."
   - "Run `ecogo lint` to catch any drift that accumulated since the last lint — the critique loop wasn't active on older compiles, so expect some missing sections and orphan pages."

### Notes

- **The marker is the schema version authority.** If you hand-edit CLAUDE.md to add the new rule blocks yourself, add the marker manually too — otherwise migrate will re-append and produce duplicates.
- **Directory Layout update is by substring match**, not by line-structure. If you wrote `See outputs/evals/ for evaluation data` in prose, migrate considers the `outputs/evals/` path "listed" and skips adding a bullet. That's intentional — it respects custom documentation.
- **Forward-compat.** Future schema versions use different markers (`v2 applied`, etc.) and layer on top of v1. Running a v2 migrate on a v1 wiki applies only the v2 delta.
- **No downgrade path.** To revert, manually remove the marker, the appended sections, and the data files. Nothing in this skill will remove them for you.

---

## `ingest <path|url>`

Acquire a source and save it to the raw library. Does NOT create wiki pages — use `compile` for that.

### Steps

1. **Detect active wiki** (see Active Wiki Detection). Read `CLAUDE.md` for schema.

2. **Acquire source:**
   - If input is a **URL**: use the WebFetch tool to retrieve content.
   - If input is a **file path**: read the file directly.
   - If the source file is in `raw/` directly (not in a subdirectory), read it from there. Sources saved before the `raw/articles/` convention are still valid.

3. **Classify** the source as one of: `article` | `paper` | `transcript` | `conversation` | `image-set`.

4. **Save to raw library:** Write to `raw/articles/YYYY-MM-DD-<slug>.md` with frontmatter:
   ```yaml
   ---
   date: YYYY-MM-DD
   source-type: <classification>
   source-url: <original URL or file path>
   title: <extracted or inferred title>
   compiled: false
   ---
   ```
   If input was a file path already in `raw/`, skip this step (source is already saved).

5. **Append to `log.md`:**
   ```
   ## [YYYY-MM-DD] ingest | <title>
   Saved <source-type> from <source> to raw/articles/.
   ```

6. **Commit:**
   ```bash
   git -C ~/ObsidianVault add "03-Resources/<wiki-name>/" && git -C ~/ObsidianVault commit -m "ingest: <title>"
   ```

7. **Print:** "Source saved to raw/articles/<filename>. Run `ecogo compile` to integrate into the wiki."

---

## `compile [<path>]`

Read raw sources and create/update wiki pages with entity extraction and cross-references.

- If `<path>` is given: compile that specific raw source.
- If no argument: scan `raw/articles/` for sources without a corresponding source-summary page in `wiki/`, and compile those.

### Steps

1. **Detect active wiki.** Read `CLAUDE.md` for schema and templates.

2. **Identify sources to compile:**
   - If path argument given: use that file.
   - Otherwise: list files in `raw/articles/`. For each, check if a corresponding source-summary page exists in `wiki/` (match by slug or title). Compile any source without a matching summary.
   - If nothing to compile: "All sources are already compiled. Nothing to do." Stop.

3. **For each source to compile** (synthesizer pass — record every page you create or modify into `touched_pages` for the critique pass in step 4):

   a. Read the raw source content.

   b. **Write or update source-summary page** in `wiki/` using the `source-summary` template from `CLAUDE.md`. Filename: `<slug>.md`. Add to `touched_pages`.

   c. **Entity extraction:** For each mentioned entity (person, concept, event):
      - Check if a page already exists in `wiki/`.
      - If yes → update with new information, preserving existing content. Add to `touched_pages`.
      - If no → create using the appropriate template (`concept.md` or `person.md`). Add to `touched_pages`.
      - Add `[[wikilinks]]` to related pages in both directions.

   d. **Backlink audit** (CRITICAL — do not skip):
      ```bash
      grep -rln "<new page title>" wiki/
      ```
      For each file that mentions the new page title but does NOT contain `[[new-page-name]]`: add a `[[wikilink]]` at the first mention. Any file you modify here is also added to `touched_pages`.

3.5. **Rationale extraction pass** (added in S1; skip entirely if the wiki's `CLAUDE.md` lacks the `v2 applied` marker — rationale extraction requires v2 schema):

   This pass captures the *why* behind facts written on concept pages. Runs after entity extraction, before self-critique, so the critique loop validates the new rationale callouts alongside other claims. See **`skills/ecogo/references/rationale-extraction.md`** for the full pipeline spec.

   a. **Budget check.** Initialize `llm_call_count = 0`. Budget: `100` calls per compile invocation (tunable via accepted-learnings rules).

   b. **For each source compiled in step 3:**
      - Run regex pre-pass on source prose. Collect candidate windows. Cap at 40 per source (top 40 by marker strength if exceeded; emit `rationale-rate-limited`).
      - For each candidate window, invoke the LLM judge (see reference doc for prompt shape). Increment `llm_call_count`.
      - If `llm_call_count >= 100`: stop rationale pass; emit `rationale-budget-exceeded`. Commit progress in the next step.
      - Validate each returned rationale: `source_excerpt` MUST be a verbatim substring of the window. Reject and emit `rationale-fabrication-attempt` if not. Malformed JSON: retry once; then emit `rationale-llm-malformed` and skip this window.

   c. **For each validated rationale:**
      - Determine target concept page via `fact_anchor` matching (exact substring, token overlap ≥ 0.6, then qmd semantic fallback). If no match, emit `rationale-no-anchor` and drop.
      - Render inline callout per the reference doc, inserting after the first paragraph matching the anchor (or at page bottom before `## See Also` if anchor matched weakly).
      - Update target page's frontmatter: `rationale-count` ++, `rationale-tags` ← union with `kind`, `has-rationale-entity: false` (set later if promoted).
      - Add target page to `touched_pages`.
      - Emit `rationale-extracted`.

   d. **Promote-to-entity pass:**
      - Cluster all rationales produced in this run by text similarity (token overlap ≥ 0.85) AND same `kind`.
      - For each cluster spanning ≥ 3 distinct concept pages: create `wiki/rationale-<slug>.md` per the entity template in the reference doc. Slug from first 5-8 content words of the rationale text, lowercased, kebab-case. If slug collides, append `-2`, `-3`, etc.
      - Replace inline callouts on each clustered page with a shortened wikilink callout:
        ```
        > [!NOTE] Rationale
        > See [[rationale-<slug>]] for the tradeoff analysis behind this choice.
        ```
      - Set `has-rationale-entity: true` on affected concept pages.
      - Add new entity pages to `touched_pages`.
      - Emit `rationale-promoted-to-entity` per promotion.

   e. **Update snapshot.** Recompute `outputs/rationales/snapshot.json` with hashes of all inline rationale callouts now present across `touched_pages`. Create the `outputs/rationales/` directory if it doesn't exist.

4. **Self-critique loop** (bounded, max 3 iterations):

   The pages from step 3 are a first draft. This loop re-reads them as a **separate pass**, finds drift the synthesizer missed, and patches in place. Separation matters — a single-pass model scores its own output too generously; the critic must read fresh.

   Initialize `RUN_ID = $(date -u +%Y-%m-%dT%H%M%SZ)`. Initialize `iteration_log = []`.

   For `iteration = 1..3`:

   a. **Deterministic checks** on each page in `touched_pages` (run `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/lint-kb.py" <wiki-root>/wiki/` and filter results to `touched_pages`, or apply these inline):
      - **Dead links**: every `[[wikilink]]` on the page must resolve to an existing file in `wiki/`.
      - **Wikilink density**: concept and source-summary pages must have ≥ 3 outbound wikilinks.
      - **Missing sections**: concept pages must contain `## Counter-Arguments and Gaps`.
      - **Length ceilings**: source-summary ≤ 600 words; concept ≤ 2000 words. No lower bound — short is acceptable, the wiki grows via sources not padding.
      - **Bidirectional backlinks**: for each page `P` in `touched_pages`, `grep -rln "<P title>" wiki/`. Any file mentioning the title without containing `[[<P-slug>]]` is a missing backlink.

   b. **LLM-judged checks** — re-open each page in `touched_pages` fresh, separate from the synthesizer context:
      - **Grounded**: every non-trivial factual claim traces to at least one `[[wikilink]]` to a source-summary page.
      - **Not fabricated**: every claim is present in the raw source(s) being compiled. Any claim that is not must be removed, not rephrased.
      - **No omitted entities**: the raw source does not mention a person, concept, or event that has no wiki page and no wikilink here.

   c. **Collect** all flags into `issues[iteration]`. Record `len(issues[iteration])` in `iteration_log`. **Emit one observation** per flag to `outputs/learnings-raw.jsonl` using the classes `ungrounded-claim`, `fabricated-claim`, `omitted-entity`, or `dead-link` — see **Learning Subsystem → Observation emission** above for the JSON line format.

   d. **Break conditions** (evaluate in order — break the outer loop on any match):
      1. `len(issues[iteration]) == 0` → converged.
      2. `iteration > 1 AND len(issues[iteration]) >= len(issues[iteration-1])` → no progress, stop and record the remainder as unresolved.
      3. `iteration == 3` → iteration budget exhausted, record remainder as unresolved and **emit a `critique-noconverge` observation** with the source slug and remainder count in `evidence`.

   e. **Apply fixes** for `issues[iteration]`. Fix table:

      | Flag | Fix |
      |------|-----|
      | Dead link | If target is clearly a stubbable concept/person, create a stub using the appropriate template and keep the wikilink. Otherwise remove the wikilink. |
      | Too few wikilinks | Re-scan `wiki/index.md` for related entities mentioned on the page; add wikilinks at first natural mention. Do NOT invent link targets. |
      | Missing "Counter-Arguments and Gaps" section | Append the empty section to the concept page. |
      | Source-summary too long | Move extended discussion to a new concept page, wikilink it. Add the new page to `touched_pages`. |
      | Concept too long | Same — split into sub-topics linked by wikilinks. |
      | Ungrounded claim | Add a wikilink to a supporting source-summary if one exists. If no source supports it, **remove the claim.** Never invent a citation. |
      | Fabricated claim | Remove the sentence or paragraph. Do not rephrase. |
      | Omitted entity | Create the page only if the raw source has enough detail to fill it. Otherwise add a `[[wikilink]]` and let the page come later from another source. Empty stubs become orphans. |
      | Missing backlink | Insert `[[wikilink]]` at the first natural mention in each flagged file. |

5. **Write critique report** to `outputs/reports/<RUN_ID>-compile.md`:
   ```markdown
   # Compile Critique — <RUN_ID>

   **Sources compiled:** N | **Pages touched:** M | **Iterations:** K | **Converged:** yes/no

   ## Iteration summary

   | Iter | Issues found | Issues fixed | Remaining |
   |------|--------------|--------------|-----------|
   | 1    | ...          | ...          | ...       |
   | ...  |              |              |           |

   ## Unresolved issues

   <list each unresolved flag with page slug, category, and short reason — these need human attention or a subsequent `ecogo lint` / additional sources>
   ```

6. **Update `wiki/index.md`** with new/updated entries under the appropriate domain heading.

7. **Close resolved backlog items.** For each raw source compiled in step 3, read its frontmatter. If it contains `fetched-for: <gap-id>`, find that id in `outputs/backlog.md`:
   - If found under `## In Progress` or `## Open`: move the entry to `## Done` and append `| resolved: YYYY-MM-DD via compile (source: <slug>)` to the line.
   - If the id is not present in the backlog (e.g., user hand-tagged a source): skip silently — the source still compiles normally.
   - If multiple raw sources share the same `fetched-for` id and any of them compiled, the backlog item is closed once. Subsequent matches just annotate `| also via <slug>`.

   This step is what makes the declarative loop self-closing: gap → fetch → compile → backlog done, with no extra user action.

8. **Append to `log.md`:**
   ```
   ## [YYYY-MM-DD] compile | <N> sources → <M> pages, <K> critique iterations, <L> unresolved, <G> gaps closed
   Compiled <source-titles>. Critique report: outputs/reports/<RUN_ID>-compile.md.
   ```

9. **Commit:**
   ```bash
   git -C ~/ObsidianVault add "03-Resources/<wiki-name>/" && git -C ~/ObsidianVault commit -m "compile: <summary> (<K> crit iter, <L> unresolved, <G> gaps closed)"
   ```

10. **If qmd available:**
    ```bash
    "${QMD}" embed --collection <name>
    ```

11. **Suggest** running `ecogo eval` next to measure whether the compile raised or lowered the score. Do not run it automatically — that's an explicit user decision.

---

## `query <question>`

Answer a question using wiki knowledge, with citations.

### Steps

1. **Detect active wiki.** Read `CLAUDE.md`.

2. **Find relevant pages:**
   - If qmd available:
     ```bash
     "${QMD}" query "<question>" --collection <name>
     ```
     Parse output for candidate page paths.
   - Otherwise: read `wiki/index.md` and identify relevant pages by title/description matching.

3. **Read all relevant pages.** Follow one level of `[[wikilinks]]` if targets look relevant to the question.

4. **Synthesize answer** with `[[wikilinks]]` as citations. Format rules:
   - **Default:** prose with inline wikilink citations.
   - **If question contains "table":** markdown table with wikilink citations in cells.
   - **If question contains "slides":** Marp markdown with `marp: true` frontmatter. Render with: `"${MARP}" <file> -o output.html`

5. **File the answer** to `wiki/queries/<slug>.md` using the `query-output` frontmatter schema. Always file — no prompt.

6. **Ask:** "Promote this answer to `wiki/<slug>.md` as a concept page? (y/n)"
   - If yes: move the file from `wiki/queries/` to `wiki/`, update frontmatter `status` from `filed` to `promoted`, and append to `log.md`:
     ```
     ## [YYYY-MM-DD] promote | <slug>
     Promoted query answer to concept page.
     ```

7. **Append to `log.md`:**
   ```
   ## [YYYY-MM-DD] query | <question-slug>
   Answered question. Referenced N pages. Filed to queries/<slug>.md.
   ```

8. **Commit:**
   ```bash
   git -C ~/ObsidianVault add "03-Resources/<wiki-name>/" && git -C ~/ObsidianVault commit -m "query: <slug>"
   ```

---

## `correct <page-slug> [<specific-claim>]`

Re-ground a wiki page (or a specific claim on it) against the raw sources the page was built from. Replace drift, fabrications, and misreads that slipped past the compile-time self-critique.

This is how "wrong data in the wiki gets replaced with correct data automatically" works in practice: when a user or the scheduled re-verification pass notices a page is wrong, `correct` re-reads the cited sources and patches the page in place. It **never invents replacements** — if a claim is wrong and no source supports a better version, the claim is removed. A shorter, honest page beats a padded wrong one.

Not a substitute for `compile` (which brings in new material) or `fetch` (which pulls new sources). If the cited sources themselves are stale, `correct` will report that and point at `fetch`.

### Steps

1. **Detect active wiki.** Read `CLAUDE.md`. Read `outputs/learnings.md` accepted rules per the **Learning Subsystem → Accepted-rules overlay**.

2. **Resolve target:**
   - `<page-slug>` is required. Open `wiki/<page-slug>.md` (check `wiki/queries/<page-slug>.md` too if the main path misses). If still missing, abort: `"Page not found at wiki/<slug>.md or wiki/queries/<slug>.md. Use 'eco go tell me about X' or 'ecogo query' to locate the right slug first."`
   - `<specific-claim>` (optional): free-text naming the claim in question. When provided, scope correction to sentences and nearby context that address this claim. When absent, audit the whole page.

3. **Identify cited sources.** Read the page's `## Sources` or `## Entities Mentioned` section. Collect:
   - `[[wikilinks]]` pointing at `source-summary` pages → follow each, note the `source-url` frontmatter, and map to the corresponding file in `raw/articles/` (by slug match).
   - Direct file path references (e.g., `src/integrations/provider-a/mapper.go`) — these are code-level citations, not fetchable raw sources. Note them but don't re-read (correction cannot verify against live code without explicit user opt-in and repo path).
   - Any inline URL citations.

4. **If no cited sources** and `<specific-claim>` is not provided, abort with:
   > "Page has no cited sources — grounding is impossible without a reference. Either (a) re-ingest the original source and re-compile this page, or (b) delete the page if it's no longer useful."

   If a specific claim is provided but the page has no sources, ask the user to paste the authoritative source for that claim, or cancel.

5. **Re-read the raw sources** that back this page. If the raw file is missing (user deleted it, or the page predates the `raw/articles/` convention): emit `raw-source-missing` observation, continue with whatever sources are available, and note the gap in the correction report.

6. **Grounding pass** — a **separate read** from step 3. For each non-trivial factual claim on the page (or claims within the scoped `<specific-claim>` if given):

   **a. Check cited sources first.**
   - Does the claim trace to text in at least one of the raw sources? (exact phrase match, paraphrase, or logical consequence) → mark `grounded`, record the supporting source slug.
   - Does a raw source contain text that directly contradicts the claim? → mark `contradicted`, record both the claim text and the contradicting source text.

   **b. Fallback: source-roots search.** If the claim does not trace to cited sources, **do not yet call it ungrounded**. Read the wiki's `CLAUDE.md` for a `source-roots:` list (declared in the schema as an optional field — see **Correction Rules** in the CLAUDE.md template). For each path in `source-roots`:
   - Grep the tree for the claim's distinctive tokens (verbatim strings, API codes, numeric values, endpoint paths).
   - If found in a file not currently cited → mark `miscited`, record both the file path and the line range. Do NOT delete — this claim is accurate; the citation is incomplete.
   - If nothing is found across all source-roots → mark `ungrounded` (true unsupported).

   If the wiki has no `source-roots:` declared, skip (b) entirely — every uncited claim goes straight to `ungrounded`. This is the safe-strict behavior for non-technical wikis where the raw library is the complete authority.

   **c. Trivial statements are not claims.** Wikilinks themselves (`[[supplier-service]]`), section headings, and structural scaffolding are references, not factual assertions — skip them.

   **d. Rationale callouts (added in S1) use a distinct rubric.** For each `> [!NOTE] Rationale` or `> [!WARNING] Rationale` callout on the page:
   - Check `source_excerpt` (derivable from the callout body, or from the page's stored rationale metadata if present): must be a verbatim substring of at least one cited source → `rationale-grounded`. If not in cited sources but found verbatim in source-roots → `rationale-miscited` (handle same as the main-claim miscited case: add the source, don't delete). If not anywhere → `rationale-ungrounded`.
   - Check `text` (the prose rationale itself): must be a plausible paraphrase of the grounded `source_excerpt`. If the `text` makes claims that the excerpt does not support → `rationale-contradicted`. The standard for "plausible paraphrase" is looser than for main claims — rationales are interpretive by nature.
   - This yields four rationale-specific outcomes: `rationale-grounded | rationale-miscited | rationale-ungrounded | rationale-contradicted`. Fix-table for rationales below in step 7.

   Rules for the grounding pass:
   - **Treat direct API field names, version numbers, endpoint paths, config keys, and numeric thresholds strictly** — they must appear verbatim in a source, not as paraphrases. These are the claims most likely to be wrong.
   - **Paraphrases of interpretive statements are acceptable** if the source supports the interpretation — e.g., "the aggregator uses gRPC for supplier communication" is grounded by a source that shows gRPC call sites even if it doesn't literally say those words.
   - **Source-roots grep is verbatim-first.** Paraphrase matching in code-level source-roots invites false positives. When the claim is a prose paraphrase (not a verbatim token), prefer to leave it as `ungrounded` rather than guess at a match.

7. **Classify the outcome and act:**

   | Outcome | Action |
   |---------|--------|
   | All non-trivial claims grounded | **Report:** `"No correction needed — page claims all trace to cited sources. If you believe the page is wrong, the cited sources themselves may be stale. Run 'eco go find info about <topic>' to pull fresh sources, then 'ecogo compile' to integrate."` |
   | Some claims `miscited` (accurate per source-roots but not per cited sources) | **Add the discovered source file to the page's `## Sources` section** with a short label (`<path> (<topic>, lines X-Y)`). Do NOT delete the claim — it's accurate, the citation was just incomplete. Offer the user: `"Shall I also ingest <path> as a proper source-summary so future compiles use it?"` |
   | Some claims ungrounded (nothing in cited sources OR in source-roots), none contradicted | Remove each ungrounded claim sentence-by-sentence. Preserve surrounding grounded prose. Do NOT rephrase or invent replacements. |
   | Some claims contradicted | Replace the contradicted claim with the source-supported version. Preserve the surrounding prose. Quote the contradicting source excerpt in a `> [!NOTE] Corrected 2026-04-17 from [[source-slug]]` callout adjacent to the correction so provenance is visible. |
   | `<specific-claim>` was given but no matching claim found on the page | Report the full page state and ask the user: `"I couldn't find a claim on this page matching '<specific-claim>'. Did you mean one of these? (list up to 3 nearest-match sentences)"`. Do not modify anything. |
   | Rationale callout is `rationale-grounded` | Preserve. |
   | Rationale callout is `rationale-miscited` | Add the discovered source to `## Sources`. Preserve the callout. Offer to ingest the source (same as main claim miscited case). |
   | Rationale callout is `rationale-ungrounded` | Remove the entire callout. Decrement `rationale-count` in the page's frontmatter. If this was the only callout of its kind on the page, remove the kind from `rationale-tags`. Compute the callout's hash and append to `outputs/rationales/deleted.json` with `{reason: "correct-found-ungrounded"}`. Emit `rationale-deleted-by-user` with `reason: correct`. |
   | Rationale callout is `rationale-contradicted` | Replace the callout body (`text`) with a source-supported rewrite. Preserve the kind, confidence, and source footer. Add a meta-callout immediately below: `> [!NOTE] Corrected <date>` noting the original text was unsupported. Emit `manual-correction` with `subject: rationale`. |

8. **Preserve** during rewriting: frontmatter, the `## See Also` block (unless it wikilinks a removed claim's only target), the `## Counter-Arguments and Gaps` section, and any section the user explicitly authored that doesn't intersect the corrected claim.

9. **Emit observations** per **Learning Subsystem → Observation emission**:
   - `manual-correction` per class of correction (one observation, evidence = `{page_slug, user_claim, N_ungrounded_removed, N_contradicted_replaced, sources_rechecked}`).
   - `raw-source-missing` if any raw source could not be found during step 5.
   - `correction-declined` if step 7 ended with "no correction needed" — this pattern, when it recurs for the same page across multiple `correct` calls, signals that the user thinks the page is wrong but the sources agree. Over time, `learn` proposes: "If a user corrects a page more than once and claims all ground, re-fetch the cited sources."

10. **Append to `log.md`:**
    ```
    ## [YYYY-MM-DD] correct | <page-slug>
    <short description: claims checked N, grounded N, ungrounded removed N, contradicted replaced N. Sources re-read: <slugs>. Reason: <user_claim or "full-page audit">.>
    ```

11. **Commit:**
    ```bash
    git -C ~/ObsidianVault add "03-Resources/<wiki-name>/" && git -C ~/ObsidianVault commit -m "correct: <page-slug> (<N> removed, <M> replaced)"
    ```

12. **Print a diff-style summary:**
    ```
    Page: <page-slug>
    Sources re-read: <slug-1>, <slug-2>
    Claims audited: N

    REMOVED (ungrounded):
      - "<claim text>"
      - ...

    REPLACED (contradicted):
      - was: "<old claim>"
        now: "<new claim>"
        source: [[<slug>]]
        excerpt: "<relevant source quote>"

    PRESERVED: N sentences grounded, unchanged.
    ```

### Notes

- **Never invent replacements.** This is the most important rule. If a source doesn't support a better version of a wrong claim, the claim is removed, full stop. The wiki having a gap is better than the wiki having fiction.
- **Correction ≠ rewriting.** Don't rewrite sentences that are grounded just because they're near sentences that aren't. Minimum-edit is the goal.
- **Stale-source case.** If the user says "this is wrong" but every claim traces cleanly to the sources, the sources themselves are probably stale. Tell the user and point at `fetch` — `correct` can't refresh sources.
- **Code citations are not verifiable here.** If a page cites a local file path (e.g., `supplier/.../search_response_mapper.go`), `correct` records the citation but does not grep the live code. That's a different class of verification and requires explicit user opt-in.
- **Multi-page corrections.** `correct` operates on one page at a time by design. If a claim is wrong across many pages, correct them individually — batch rewrites risk cross-page consistency drift.

---

## `lint`

Audit wiki integrity and fix issues.

### Steps

1. **Read all files** in `wiki/`.

2. **Build a link graph:** for each `[[wikilink]]` on each page, record the edge (source → target).

3. **Run deterministic lint script** if available:
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/lint-kb.py" <wiki-root>/wiki/
   ```

4. **Report and fix:** For every flag in this table, **emit an observation** per **Learning Subsystem → Observation emission** — classes `dead-link`, `orphan-page`, `stale-page` are predefined; other flags emit under `other` with a `description` field in evidence.

   | Check | Action |
   |-------|--------|
   | **Orphan pages** (no inbound links) | List them. Suggest adding links from related pages. Emit `orphan-page`. |
   | **Dead links** (`[[wikilinks]]` to nonexistent files) | Create stub pages with appropriate template. Emit `dead-link`. |
   | **Unlinked concept mentions** | Scan pages for proper nouns and technical terms appearing in prose without `[[wikilinks]]`. If a corresponding page exists, add the wikilink at first mention. If no page exists, flag as a candidate for a new page. |
   | **Contradictions** | Scan for `[!WARNING]` markers. List them. |
   | **Missing "Counter-Arguments and Gaps" sections** | Add empty `## Counter-Arguments and Gaps` section. |
   | **Stale pages** | Flag pages with `status: stale` in frontmatter. Emit `stale-page` if older than 90 days. |
   | **Index drift** | Compare `index.md` entries vs actual files. Add missing, remove dead. |

5. **Suggest growth opportunities and stage them in the backlog:** Based on the wiki's current content and the gaps found in step 4, generate:
   - 3-5 questions the wiki cannot yet answer well (candidates for `ecogo query`)
   - 2-3 topic areas or sources that would most strengthen the wiki

   Append each of these to `outputs/backlog.md` under `## Open` using the backlog entry format (see **backlog.md template** and **Gap Rules** in `CLAUDE.md`). Set `source: lint`, `priority: medium`, and today's date. Deduplicate against existing open/in-progress items by slug before appending. This is what lets `ecogo fetch` act on lint's findings without re-parsing the report.

6. **Write lint report** to `outputs/reports/YYYY-MM-DD-lint.md`:
   ```markdown
   # Lint Report — YYYY-MM-DD

   **Wiki:** <name> | **Issues found:** N | **Fixed:** M

   ## Issues
   <full issue table from step 4>

   ## Next Steps
   <growth suggestions from step 5>
   ```

7. **Append to `log.md`:**
   ```
   ## [YYYY-MM-DD] lint | N issues found, M fixed
   <summary of issues>
   ```

8. **Commit:**
   ```bash
    git -C ~/ObsidianVault commit -am "lint: YYYY-MM-DD"
    ```

---

## `eval [<question>]`

Run the wiki's self-evaluation. For each question in `outputs/evals/questions.md` (or a single ad-hoc `<question>` if provided), synthesize an answer using the same retrieval path as `query`, then run a **separate judge pass** to score the answer against the rubric. Record per-question detail plus an aggregate score with delta vs the previous run.

Eval exists so the wiki has a **measurable success criterion**. Every other operation (`ingest`, `compile`, `lint`) can then be judged by whether the eval score rises or falls. A fresh wiki starts near 0%; the signal is the trajectory, not the absolute number.

### Steps

1. **Detect active wiki.** Read `CLAUDE.md`.

2. **Resolve the question set:**
   - If `<question>` argument given: use just that question. This is **ad-hoc mode** — runs the pipeline but does **not** append to history.jsonl. Use it to probe a specific gap without polluting the time series.
   - Otherwise: read `outputs/evals/questions.md`. Extract questions from the `## Questions` section (each top-level `- ` bullet is one question).
   - If the file is missing, or every question still starts with `[REPLACE]`, abort: "No evaluation questions defined. Edit `outputs/evals/questions.md` and replace the `[REPLACE]` placeholders first."

3. **Create run directory:**
   ```bash
   RUN_ID=$(date -u +%Y-%m-%dT%H%M%SZ)
   mkdir -p outputs/evals/${RUN_ID}/answers
   ```

4. **For each question:**

   a. **Synthesize answer** — same retrieval path as `query` steps 2-4 (qmd if available else `index.md`; open relevant pages; follow one level of wikilinks; write prose with `[[wikilinks]]` as citations). Write to `outputs/evals/<RUN_ID>/answers/<slug>.md`. Do **not** file to `wiki/queries/` — eval answers are evaluation artifacts, not wiki content.

   b. **Judge pass (mandatory second read).** Open the answer file fresh and score it against the rubric defined in `outputs/evals/questions.md`. Default rubric, each criterion 0 or 1:
      - `grounded`: every non-trivial factual claim traces to a `[[wikilink]]` pointing at an existing page in `wiki/`
      - `cited`: answer contains at least one `[[wikilink]]`
      - `complete`: answer covers every distinct clause of the question (if the question has multiple parts joined by "and"/"or"/commas, all parts must be addressed)
      - `no_dead_links`: every `[[wikilink]]` in the answer resolves to a file in `wiki/` (check by listing `wiki/**/*.md` once per run and matching slugs)

      **Bonus (optional) — `rationale-present` (added in S1):** when the eval question implies a reasoning or "why" answer (detect keywords: `why`, `reason`, `rationale`, `tradeoff`, `chose`, `decided`), check whether the synthesized answer contains at least one wikilink to a `rationale-<slug>` entity page OR at least one rationale callout quoted from a read page. If yes → `rationale-present: 1`; if no → `rationale-present: 0`; if the question does not imply reasoning → `rationale-present: "n/a"`.

      `rationale-present` does NOT contribute to the core `total` (which still sums over the four core criteria). It is reported separately in the summary table. A wiki without rationales can still score 100% core; the bonus is a maturity indicator, not a gate.

      The judge pass **must be a separate read from the synthesizer**. Scoring while composing inflates results — the synthesizer knows which claims it fabricated. A clean re-read catches drift.

   c. **Append one line to** `outputs/evals/<RUN_ID>/detail.jsonl`:
      ```json
      {"ts":"<ISO8601>","question":"<q>","answer_path":"outputs/evals/<RUN_ID>/answers/<slug>.md","scores":{"grounded":0|1,"cited":0|1,"complete":0|1,"no_dead_links":0|1},"total":0.0-1.0,"pages_referenced":["slug1","slug2"],"failures":["short reason per failed criterion"]}
      ```

5. **Compute aggregate** by reading `detail.jsonl`: `mean_score`, `per_rubric_means` for each of the four criteria, `question_count`.

6. **Compute delta vs previous run:**
   - Read `outputs/evals/history.jsonl` if it exists. Take the last line.
   - `delta_pct = (current mean_score − previous mean_score) * 100`.
   - **Regressions:** for every question present in both the previous run's `detail.jsonl` and this one's, flag any whose `total` dropped. Record question text + old → new total + the first `failures[]` entry from the judge.
   - **Emit observations** per **Learning Subsystem → Observation emission**: one `eval-regression` if `delta_pct < 0` (evidence includes `run_id`, `previous_run_id`, `delta_pct`, and regression list); one `eval-complete-zero` per question whose `scores.complete == 0` in this run (evidence includes the question text and the run id).

7. **Append one line to** `outputs/evals/history.jsonl` (skip this step in ad-hoc mode):
   ```json
   {"ts":"<ISO8601>","run_id":"<RUN_ID>","question_count":N,"mean_score":0.0-1.0,"per_rubric_means":{"grounded":0.0-1.0,"cited":0.0-1.0,"complete":0.0-1.0,"no_dead_links":0.0-1.0},"delta_pct":<float>,"regressions":N}
   ```

8. **Write run summary** to `outputs/evals/<RUN_ID>/summary.md` using the **eval-summary.md template** below.

9. **Append to `log.md`:**
   ```
   ## [YYYY-MM-DD] eval | N questions, mean X%, delta ±Y%
   Regressions: <comma-separated question slugs or "none">. Report: outputs/evals/<RUN_ID>/summary.md.
   ```

10. **Commit** (skip in ad-hoc mode, or commit only the run directory):
    ```bash
    git -C ~/ObsidianVault add "03-Resources/<wiki-name>/" && git -C ~/ObsidianVault commit -m "eval: <RUN_ID> (mean X%, delta ±Y%)"
    ```

11. **Print** the per-rubric + per-question tables from the summary, plus the report path.

### Notes

- **Regressions matter more than absolute score.** After any `compile`, re-running `eval` should never silently drop a previously-answered question. If it does, the compile introduced a regression — investigate before moving on.
- **A failing judge is not the same as a failing wiki.** If `no_dead_links` drops, the answer likely cites pages that were renamed or removed. `ecogo lint` fixes that class of issue; re-run `eval` after.
- **The rubric is part of the schema.** If you change the rubric (e.g., add `recency` or `answer_length`), update both `outputs/evals/questions.md` and the judge-pass description in this skill. Old history entries will have a different rubric shape — that's acceptable; delta comparison should tolerate missing keys.

---

## `gap [<question>]`

Surface and record what the wiki doesn't know yet. Either scans existing gap-detection signals (lint reports, compile unresolved items, eval failures) and stages them into `outputs/backlog.md`, or takes a single user question and adds it directly.

The backlog is the bridge between "something noticed a gap" and "someone (or something) pulled sources to close it." It is append-only by default and structured so `ecogo fetch` and future automation can act on it without re-parsing prose reports.

### Steps

1. **Detect active wiki.** Read `CLAUDE.md`.

2. **Ensure `outputs/backlog.md` exists.** If missing, create it from the **backlog.md template** below.

3. **Determine mode:**
   - **Ad-hoc** (`<question>` argument): single-item. Proceed to step 5 with `{question: <question>, source: "user", priority: "medium"}`.
   - **Scan** (no argument): collect candidate items from these signals, in order:
     1. Latest `outputs/reports/YYYY-MM-DD-lint.md` "Next Steps" section — every question listed there.
     2. Latest `outputs/reports/<RUN_ID>-compile.md` "Unresolved issues" — convert each unresolved *omitted-entity* or *ungrounded-claim* flag into a question of the form "What is X?" or "What is the source for Y?".
     3. Most recent entry in `outputs/evals/history.jsonl` — if `delta_pct < 0`, open the matching `outputs/evals/<RUN_ID>/detail.jsonl` and pull every question with `total < 1.0`. These are high priority.
     4. `outputs/evals/questions.md` — any question that has never scored 100% across all `history.jsonl` entries.
     5. **`log.md` prose markers** — grep the file for lines matching any of: `follow-up`, `follow up`, `TODO` (as a whole word), `remains as`, `fix later`, `for later`, `flagged .* as`, `investigate`. For each match, take the full line plus its enclosing `## [YYYY-MM-DD]` heading as context. These are user-written gap markers that accumulate over time in prose and would otherwise sit inert. `kind: topic`, `source: log`, `priority: medium`.
     6. **Wiki-page follow-up sections** — scan `wiki/**/*.md` (and `wiki/queries/**/*.md`) for headings that **exactly are** one of these (trailing punctuation OK, case-insensitive, no extra words before or after the listed phrase):
        - `Suggested follow-ups` / `Suggested follow up`
        - `Follow-ups` / `Follow ups` / `Follow-up` / `Follow up`
        - `TODO` / `TODOs`
        - `Open Questions` / `Open Question`
        - `Known Issues` / `Known Issue`
        - `Outstanding Gaps` / `Outstanding Work`
        - `Remaining Work`
        - `Action Items`
        - `To Fix`
        - `Next Steps` (only when in a wiki page, not in lint reports where this heading has a different meaning)

        Regex: `^##[ ]+(Suggested [Ff]ollow-?ups?|[Ff]ollow[- ]?ups?|TODOs?|Open Questions?|Known Issues?|Outstanding Gaps?|Outstanding Work|Remaining Work|Action Items|To Fix|Next Steps)[ :]*$`

        For each matched heading, extract every `- ` bullet until the next `## ` heading or end-of-file. Each bullet becomes one candidate. `kind: topic`, `source: wiki-page`, `priority: medium`. The page slug goes in the entry so the user can trace back. Do NOT match partial words in headings — "with one API gap" and "The Bug (Found & Fixed)" are explicitly excluded.

     **Signal quality note:** sources 5 and 6 are pattern-based and will sometimes fire on incidental prose ("we'll tackle this later"). Dedup by slug catches most duplicates; review the first scan's output before acting on it. If a source-5 or source-6 match turns out to be noise, skip it during acceptance (don't add to backlog) or accept and immediately move to `## Skipped` — the dedup will respect the skip forever.

4. **Deduplicate.** For each candidate, compute its slug (`slugify(question)`). If an entry with that slug already exists in `backlog.md` under any section:
   - Status `open` or `in-progress` → skip.
   - Status `done` but the signal is fresh (eval regression, new compile unresolved) → move back to `## Open` with note `| reopened: YYYY-MM-DD — <reason>`.
   - Status `skip` → respect the skip, do not re-add.

5. **Assign id and priority** for each new item:
   - `id = gap-YYYY-MM-DD-NNN` where NNN is the next 3-digit sequence for today across all sections of the backlog.
   - Priority rules:
     - `high` — from eval regression (`delta_pct < 0`) or any eval question with `total = 0.0`.
     - `medium` — from lint, compile unresolved, or user.
     - `low` — from unanswered `query` operations or eval questions with partial scores.

6. **Append to `outputs/backlog.md`** under `## Open`, one line per item:
   ```
   - [ ] `<gap-id>` | **<kind>** | "<question or topic text>" | source: <lint|eval|compile|user|log|wiki-page> | priority: <low|medium|high> | added: YYYY-MM-DD
   ```
   `<kind>` is `question` (the default for eval/lint/compile/user signals) or `topic` (for log/wiki-page prose signals — these are often action items, not questions). For `source: wiki-page`, suffix the entry with `| from: <page-slug>` so the origin is traceable.

7. **Append to `log.md`:**
   ```
   ## [YYYY-MM-DD] gap | <N> items added
   Sources: <comma-separated provenance>. See outputs/backlog.md.
   ```

8. **Commit:**
   ```bash
   git -C ~/ObsidianVault add "03-Resources/<wiki-name>/" && git -C ~/ObsidianVault commit -m "gap: <N> items added"
   ```

9. **Print** the new items in a table. Suggest: "Run `ecogo fetch` to pull sources for the top items, or `ecogo fetch <gap-id>` for a specific one."

### Notes

- **Never silently overwrite a `skip`.** If the user marked an item `skip`, that's a deliberate "not worth pursuing" signal. Respect it even if the same signal keeps appearing.
- **Dedup by slug, not by exact question text.** "What is Markdown?" and "What is markdown?" should collide.
- **When processing a user-initiated skip** (user moved an item to `## Skipped` manually, or `ecogo gap` detects a new candidate whose slug matches an existing skipped entry and respects the skip), **emit `backlog-skip`** per **Learning Subsystem → Observation emission** with the question text in evidence. Over time this trains `ecogo learn` to propose narrower gap-detection rules that avoid re-proposing skipped classes.

---

## `fetch [<gap-id|question>]`

Pull external sources to close one or more backlog items. Saves fetched content to `raw/articles/` with a `fetched-for: <gap-id>` frontmatter field so `compile` step 7 can auto-close the backlog entry when the source is integrated.

Does **not** compile. Same separation as `ingest` → `compile`: fetch stages raw sources, compile integrates them. This keeps the human (or a downstream automation) in control of when new material enters the wiki.

### Steps

1. **Detect active wiki.** Read `CLAUDE.md`.

2. **Determine target(s):**
   - `<gap-id>` (matches `gap-YYYY-MM-DD-NNN`): fetch for that specific backlog item. It must currently be in `## Open` or `## In Progress`.
   - `<question>` (free-text, does not match gap-id pattern): internally call `ecogo gap "<question>"` first to create a backlog entry, then fetch for it.
   - **No argument**: take the top 3 items from `## Open`, ordered by priority (`high` → `medium` → `low`), then age (oldest `added` date first).

3. **For each target item:**

   a. **Formulate 2-3 search queries** derived from the item's question. Favour queries that surface authoritative or primary sources. Example: "How did A influence B?" → `["A influence B history", "A B relationship", "A and B biography"]`. Print the queries — they are auditable input to the search layer.

   b. **Select a fetcher**, preferring in order:
      1. **WebSearch + WebFetch** (built-in tools) — for each query, take top 3-5 unique URLs across results; WebFetch each.
      2. **`exa-search` skill / Exa MCP** if available — better for technical or recent content.
      3. **`deep-research` skill** if available — escalate only when the backlog item has `kind: topic` (broad) rather than a specific question.
      4. **None available**: print the formulated queries, mark the backlog item `in-progress` with a `pending-fetch: true` note, instruct the user: "No web tools available. Search manually, save candidate sources to `raw/articles/` with `fetched-for: <gap-id>` in frontmatter, then run `ecogo compile`." Skip the remaining sub-steps.

   c. **Filter fetched pages before saving.** Drop any page that is obviously SEO spam, adult content, unrelated material, or login-walled (content unavailable). **Emit `fetch-spam-rejected`** per dropped URL (evidence: `gap-id`, `url`, short `reason`). A smaller set of honest sources beats a larger padded set — the compile step will re-surface quality issues anyway, but filtering up front saves critique iterations.

   d. **For each accepted URL**, write to `raw/articles/YYYY-MM-DD-<slug>.md`:
      ```yaml
      ---
      date: YYYY-MM-DD
      source-type: article
      source-url: <url>
      title: <extracted title>
      compiled: false
      fetched-for: <gap-id>
      ---

      <content>
      ```

   e. **Update the backlog.** Move the item from `## Open` to `## In Progress`. Replace its line with:
      ```
      - [~] `<gap-id>` | **<kind>** | "<question>" | fetched: YYYY-MM-DD (<N> sources staged) | sources: <slug-1>, <slug-2>, …
      ```

4. **Append to `log.md`:**
   ```
   ## [YYYY-MM-DD] fetch | <N> items → <M> sources staged
   Items: <gap-id-1>, <gap-id-2>. Run `ecogo compile` to integrate.
   ```

5. **Commit:**
   ```bash
   git -C ~/ObsidianVault add "03-Resources/<wiki-name>/" && git -C ~/ObsidianVault commit -m "fetch: <M> sources for <N> backlog items"
   ```

6. **Print** a summary table: which gap ids were fetched, how many sources per id, paths to staged files. Suggest: "Run `ecogo compile` to integrate and auto-close these items."

### Notes

- **Two good sources per gap beats five mediocre.** Compile time and critique iterations are precious.
- **Do not auto-compile from fetch.** The separation of stage and integrate is deliberate — it gives the user a moment to inspect staged sources, add their own, or drop bad ones before they become wiki pages.
- **If a fetch produces zero usable sources for an item**, leave the item in `## In Progress` with `| fetched: YYYY-MM-DD (0 sources — none passed filter)`, surface it in the log, and **emit `fetch-zero-sources`** (evidence: `gap-id`, formulated `queries`, number of candidates considered). Re-running `ecogo fetch <gap-id>` will try again with fresh queries.

---

## `learn [<subcommand>]`

Distill recurring observations into named learnings, and manage their lifecycle: observing → proposed → accepted → promoted (or rejected). The subsystem is described in **Learning Subsystem** above.

Subcommands:
- (none) — **distill**: read `outputs/learnings-raw.jsonl`, group by class, update rolled-up entries in `outputs/learnings.md`, and draft a proposed rule for any class that has crossed the threshold.
- `list` — print the current state of `outputs/learnings.md` as a table.
- `accept <L-id>` — mark a proposed learning's rule as accepted. Ops will read and apply it on every subsequent run.
- `reject <L-id>` — mark rejected. Distill skips this class on future runs until re-opened manually.
- `promote <L-id>` — append the accepted rule to the wiki's `CLAUDE.md` under the appropriate Rules section. Makes the rule permanent schema rather than an overlay.

### Steps (distill — default, no subcommand)

1. **Detect active wiki.** Read `CLAUDE.md`. Read `outputs/learnings.md` if present.

2. **If `outputs/learnings.md` is missing**, create it from the **learnings.md template**.

3. **Load raw observations** from `outputs/learnings-raw.jsonl`. If missing or empty, report "No observations to distill. Run any op that emits (compile, lint, eval, fetch, gap) first." and stop.

4. **Group observations by `class`.** For each class:
   - `count` = total observations.
   - `first_seen` = earliest `ts`.
   - `last_seen` = latest `ts`.
   - `recent_evidence` = the 3 most recent `evidence` objects (used when drafting the proposed rule).

5. **Update or create rolled-up entries in `outputs/learnings.md`:**
   - If an entry with the same `class` already exists under `## Observing`, `## Proposed`, or `## Accepted`: update its `Observed:` line with the new count and timestamps; append new evidence refs (cap total evidence list at 10 — drop oldest).
   - If no entry exists: create a new one under `## Observing` with a fresh `L-YYYY-MM-DD-NNN` id.
   - Entries under `## Rejected` or `## Promoted` are **not** touched by distill. Rejected classes are effectively silenced until the user moves them back manually.

6. **Promote observing → proposed.** Threshold: `count ≥ 5 AND last_seen within the last 30 days` (configurable in the wiki's `CLAUDE.md` under Learning Rules). For each entry in `## Observing` that crosses the threshold:
   - Synthesize a `Proposed rule:` from the class and its recent evidence. The rule must be:
     - **Concrete and actionable** — reference specific ops, steps, or checks where it applies.
     - **Narrow** — constrain only the pattern, not adjacent behavior.
     - **Additive** — a new constraint or instruction, not a removal. Never propose "stop doing X" without a replacement.
     - **Honest** — if the pattern is ambiguous and the rule would be guesswork, leave the entry in `## Observing` with a note and skip proposal.
   - Move entry from `## Observing` to `## Proposed`.

7. **Never auto-accept or auto-promote.** Status transitions beyond `proposed` are explicit user decisions via the subcommands.

8. **Append to `log.md`:**
   ```
   ## [YYYY-MM-DD] learn | <N> observations distilled, <M> classes, <P> new proposals
   ```

9. **Commit:**
   ```bash
   git -C ~/ObsidianVault add "03-Resources/<wiki-name>/" && git -C ~/ObsidianVault commit -m "learn: distill (<P> new proposals)"
   ```

10. **Print** the new proposals with their `L-id`s and suggest: "Review each and run `ecogo learn accept <L-id>` or `ecogo learn reject <L-id>`."

### Steps (list)

1. Read `outputs/learnings.md`.
2. Print one table per section (Observing, Proposed, Accepted, Rejected, Promoted) with columns: `id | class | count | last seen | proposed rule (truncated to 80 chars)`.
3. Do not commit — read-only.

### Steps (accept <L-id>)

1. **Detect active wiki**, read `outputs/learnings.md`.
2. **Find entry by `L-id`.** Abort if not found, or not currently in `## Proposed`. (Entries skip straight from observing to proposed to accepted — `accept` only applies to proposed.)
3. **Move entry to `## Accepted`** with `Accepted: YYYY-MM-DD` appended to its header.
4. **Append to `log.md`:** `## [YYYY-MM-DD] learn accept | <L-id> | <class>`.
5. **Commit:** `learn: accept <L-id>`.
6. **Print:** "Rule accepted. It will be applied on every subsequent op. Promote it to CLAUDE.md with `ecogo learn promote <L-id>` once it's proven stable."

### Steps (reject <L-id>)

1. **Detect active wiki**, read `outputs/learnings.md`.
2. **Find entry by `L-id`.** Abort if not found.
3. **Optionally prompt** the user for a short reason (reason is optional, not required).
4. **Move entry to `## Rejected`** with `Rejected: YYYY-MM-DD — <reason or blank>`.
5. **Append to `log.md`:** `## [YYYY-MM-DD] learn reject | <L-id> | <class>`.
6. **Commit:** `learn: reject <L-id>`.
7. Future distill passes will skip this class. To re-open, the user manually moves the entry back to `## Observing` or deletes it.

### Steps (promote <L-id>)

1. **Detect active wiki**, read `outputs/learnings.md` and the wiki's `CLAUDE.md`.
2. **Find entry by `L-id`.** Abort if not in `## Accepted`.
3. **Select the target section in `CLAUDE.md`** based on the class:
   - `ungrounded-claim`, `fabricated-claim`, `omitted-entity`, `critique-noconverge` → `## Compile Rules`
   - `dead-link`, `orphan-page`, `stale-page` → `## Lint Rules`
   - `eval-*` → `## Eval Rules`
   - `fetch-*` → `## Fetch Rules`
   - `backlog-skip` → `## Gap Rules`
   - `other` / anything else → `## Learned Rules` (create this section at the end of CLAUDE.md if it doesn't exist).
4. **Append the rule text** to the selected section as a new numbered item. Keep prefix `(learned <YYYY-MM-DD>)` so the origin is visible in schema.
5. **Move entry** from `## Accepted` to `## Promoted` in `outputs/learnings.md` with `Promoted: YYYY-MM-DD → CLAUDE.md ## <section>`.
6. **Append to `log.md`:** `## [YYYY-MM-DD] learn promote | <L-id> | <class> → CLAUDE.md`.
7. **Commit:** `learn: promote <L-id> → CLAUDE.md`.
8. **Print** the diff applied to CLAUDE.md so the user can see exactly what became permanent schema.

### Notes

- **Distill is idempotent over its input.** Running it twice in a row with no new observations in between is a no-op.
- **Rejected classes are silenced, not forgotten.** The entry stays in `## Rejected` for historical context. A future wiki maintainer can see what was tried and deliberately dropped.
- **Promote sparingly.** A rule should prove itself through several runs under `## Accepted` before it becomes schema. CLAUDE.md is where rules go to stay.
- **The threshold is honest.** If 5 observations in 30 days isn't the right number for a low-volume wiki, edit `## Learning Rules` in the wiki's CLAUDE.md — the distill pass reads the threshold from there.

---

## `rationale [<subcommand>]`

Retroactively extract rationale from source material for concept pages that predate the S1 upgrade, or re-extract for a single page whose rationale looks wrong. Provides the backfill path; compile step 3.5 handles new pages automatically.

Sub-commands:
- (none) — **backfill**: iterate all concept pages missing `rationale-count` frontmatter (or count=0 with sources newer than page), run full extraction pipeline.
- `<page-slug>` — re-extract for one page. Replaces existing rationales, not merges.
- `list [<page-slug>]` — print rationales grouped by kind. Read-only.
- `promote <page>:<n>` — force inline rationale number `<n>` on `<page>` into a `rationale-<slug>.md` entity page. Emit `rationale-promoted-to-entity` with `explicit: true`.
- `delete <page>:<n>` — explicit delete. Emit `rationale-deleted-by-user` with `explicit: true`.

### Steps (backfill — default)

1. **Detect active wiki.** Read `CLAUDE.md`. Read `outputs/learnings.md` accepted-rules overlay.

2. **Verify v2 schema.** If `CLAUDE.md` lacks `<!-- ecogo-migrate: v2 applied -->`, abort with: "This wiki is on v1 schema. Run `ecogo migrate` first to enable rationale extraction." Stop.

3. **Build target list.** For each file in `wiki/*.md` where `type: concept` in frontmatter:
   - If `rationale-count` is absent → add to target list.
   - If `rationale-count == 0` and any cited source in `## Sources` has `mtime > page_mtime` → add to target list.
   - Otherwise skip.
   If target list empty: report "Nothing to backfill" and stop.

4. **For each target page**, in priority order (pages with more incoming wikilinks first):
   a. Open the page; collect cited sources from `## Sources` / `## Entities Mentioned`.
   b. Resolve each source-summary wikilink to its `source-url` frontmatter field → the raw source file.
   c. Run the extraction pipeline per **`skills/ecogo/references/rationale-extraction.md`** (regex pre-pass → LLM judge → validate → render).
   d. For each rationale, insert inline callout per the reference's insertion rule.
   e. Update page frontmatter: `rationale-count`, `rationale-tags`, `has-rationale-entity: false` (entity pass runs at step 5).
   f. Emit observations: `rationale-extracted` per success, `rationale-missing-per-marker` if regex fired but LLM returned empty, `rationale-no-anchor` per dropped rationale, etc.
   g. Add modified page to `touched_pages` set.

5. **Promote-to-entity pass** after all pages extracted:
   - Cluster rationales across `touched_pages` by text similarity + kind.
   - Clusters of size ≥ 3 become new `wiki/rationale-<slug>.md` entity pages.
   - Replace inline callouts on clustered pages with shortened wikilink callouts.
   - Set `has-rationale-entity: true` on affected concept pages.
   - Emit `rationale-promoted-to-entity` per promotion.
   - Add new entity pages to `touched_pages`.

6. **Update `wiki/index.md`** with new rationale entity pages under a `## Rationales` domain heading.

7. **Write run report** to `outputs/runs/rationale-<RUN_ID>.md`:
   ```markdown
   # Rationale Backfill Report — <RUN_ID>

   **Pages processed:** N | **Rationales extracted:** M | **Entities promoted:** K
   **Duration:** <seconds> | **LLM calls:** <count> | **Budget remaining:** <count>

   ## Per-page summary

   | Page | Extracted | Kinds | Notes |

   ## Promoted entities

   - [[rationale-<slug>]] — N source pages, kind=<kind>

   ## Observations emitted

   | Class | Count |
   ```

8. **Update snapshot.** Write `outputs/rationales/snapshot.json` with hashes of all current inline rationale callouts across `touched_pages`.

9. **Append to `log.md`:**
   ```
   ## [YYYY-MM-DD] rationale | backfill — N pages, M rationales, K entities promoted
   Report: outputs/runs/rationale-<RUN_ID>.md.
   ```

10. **Commit.** On the plugin repo (vault commits silently skip if not under git).

11. **Print** the run report summary + pointer to the full report file.

### Steps (single-page — `<page-slug>`)

Same as backfill but target list = `[<page-slug>]`. Replaces existing rationales (compute diff in step 3 and 4; deleted ones emit `rationale-deleted-by-user` with `reason: re-extraction`). No promote-to-entity pass (single page can't meet ≥ 3 threshold alone).

### Steps (`list [<page-slug>]`)

1. Detect active wiki.
2. If `<page-slug>`: open the page, parse all `> [!NOTE] Rationale` / `> [!WARNING] Rationale` callouts. Print as table: `index | kind | confidence | text (first 80 chars) | source`.
3. If no arg: iterate all concept pages with `rationale-count > 0`, print one line per rationale with page slug prefix.
4. Read-only — no commit, no observations.

### Steps (`promote <page>:<n>`)

1. Detect active wiki.
2. Parse the page, find the nth rationale callout.
3. Abort if not found: `"Rationale <n> not found on <page>. Run 'ecogo rationale list <page>' to see available."`.
4. Abort if already a wikilink to entity: `"Rationale <n> is already promoted to [[rationale-<slug>]]."`.
5. Synthesize entity page slug from rationale text (first 5-8 content words, lowercased, kebab-case).
6. Abort if that slug already exists: `"Entity page [[rationale-<slug>]] already exists. Choose a different rationale to promote or manually merge."`.
7. Create `wiki/rationale-<slug>.md` per the entity template in the reference doc.
8. Replace the inline callout on the source page with the shortened wikilink callout.
9. Update the source page's frontmatter: `has-rationale-entity: true`.
10. Emit `rationale-promoted-to-entity` with `{page, n, slug, explicit: true}`.
11. Append to `log.md`, commit, print confirmation.

### Steps (`delete <page>:<n>`)

1. Detect active wiki.
2. Parse the page, find the nth rationale callout.
3. Abort if not found.
4. Compute the rationale's hash (sha256 of its text, first 16 hex chars).
5. Remove the callout from the page in place. Decrement `rationale-count`; update `rationale-tags` if this was the only rationale of its kind.
6. Append the hash to `outputs/rationales/deleted.json` with `{hash, deleted_at, kind, explicit: true}`.
7. Emit `rationale-deleted-by-user` with `{page, n, hash, kind, confidence, explicit: true}`.
8. Append to `log.md`, commit, print confirmation.

### Notes

- **Budget awareness.** Backfill mode can hit the 100-LLM-call-per-op budget fast on a large wiki. If reached, the run commits partial progress and writes a `rationale-budget-exceeded` observation. The user reruns to continue (idempotency: previously-processed pages skip on next run).
- **Idempotency.** Re-running backfill mode on the same wiki should produce the same result (modulo LLM non-determinism). Pages whose cited sources haven't changed and whose mtime is newer than their sources are skipped.
- **Pair with lint.** After backfill, running `ecogo lint` cleans up any inserted-but-broken wikilinks (e.g., `[[rationale-<slug>]]` typos).

---

## `run [<profile>]`

Orchestrate a sequence of wiki operations as a single scheduled tick. Designed to be invoked by a cron trigger (via Claude Code's `schedule` skill) so the wiki evolves overnight without a user in the session.

`run` is strictly a composer — it calls existing ops in a defined sequence. It never does work that an individual op couldn't do. If a step fails, `run` records the failure and continues with the next step; it does not abort the whole tick. Every side effect `run` produces could be reproduced by invoking the underlying ops manually — so when debugging, drop into the specific op, not `run`.

### Profiles

| Profile | Sequence | Expected duration | Suggested cadence |
|---------|----------|-------------------|-------------------|
| `default` / (none) | compile → lint → eval → gap → fetch → compile → learn | 20-30 min mature wiki | daily |
| `cheap` | compile → lint | 1-5 min | hourly during working hours |
| `expensive` | eval → fetch → learn | 10-15 min (net I/O) | weekly |
| `canary` | eval (ad-hoc, single known-good question) | 30-60s | as a scheduler smoke test |

### Steps

1. **Detect active wiki.** Read `CLAUDE.md`. Read `outputs/learnings.md` accepted rules per the **Learning Subsystem → Accepted-rules overlay** — applies to the composer itself, not just the sub-ops (e.g. an accepted rule that says "skip fetch on Sundays" should be honored here).

2. **Record run id and initialize state:**
   ```
   RUN_ID = $(date -u +%Y-%m-%dT%H%M%SZ)
   run_log = []
   total_elapsed_seconds = 0
   steps_failed = []
   steps_skipped = []
   ```

3. **Idempotency gate.** Before doing anything, determine if the tick has actual work. Check all of:
   - Uncompiled raw sources exist (`raw/articles/*.md` whose slug has no matching `wiki/<slug>.md`).
   - Open backlog items with priority ≥ `medium`.
   - ≥ 24h since the last entry in `outputs/evals/history.jsonl`.
   - `outputs/learnings-raw.jsonl` has entries newer than the last distill pass (read the last `## [YYYY-MM-DD] learn` entry in `log.md` for timestamp).

   If **none** of these are true AND the profile is `default` or `expensive`: log one line "run | profile=<profile>, idle (no work)" to `log.md`, do NOT commit, return.

   Profiles `cheap` and `canary` always run their narrow sequences (they're cheap enough that empty ticks don't matter).

4. **Execute the profile sequence.** For each step, in order:

   a. Record `step_start_ts`.
   b. **Invoke the op** by following that op's own step-by-step instructions from this SKILL.md. Pass-through arguments as needed (e.g., `gap` with no arg for scan mode, `fetch` with no arg for top-N mode, `eval` canary mode = ad-hoc on the first question in `outputs/evals/questions.md`).
   c. **On error**: record `{step, error_text, duration}` in `steps_failed`. Continue to the next step. Do NOT abort the tick.
   d. **On success**: append the op's summary (pages touched, sources staged, eval delta, proposals added, etc.) to `run_log`.
   e. **Time-budget check**: if `total_elapsed_seconds > 1800` (30 min hard cap): mark remaining steps in `steps_skipped` with reason `time_budget_exceeded` and break out of the sequence.

   **Sub-op interaction notes:**
   - The inner `compile` → `compile` pattern in `default` is deliberate: the first runs on pre-existing raw sources; the second runs on whatever `fetch` just staged. Skipping the second means fetched sources sit uncompiled for a full day.
   - `gap --scan` reads the lint/eval/compile reports written earlier in this same tick, which is what lets today's regressions become tomorrow's backlog items.
   - `learn` runs last so it distills observations emitted by every preceding step of this tick — one pass catches the whole set.

5. **Write run report** to `outputs/runs/<RUN_ID>.md`:
   ```markdown
   # Run — <RUN_ID>

   **Profile:** <profile> | **Duration:** <Ns> | **Steps OK:** <N> | **Failed:** <F> | **Skipped:** <S>

   ## Steps

   | # | Op | Duration | Outcome |
   |---|----|----------|---------|
   | 1 | compile | 12s | 2 sources → 9 pages, 0 unresolved |
   | 2 | lint | 4s | 3 issues found, 3 fixed |
   | ... | | | |

   ## Net change this tick

   - Sources compiled: <N>
   - Pages touched: <N>
   - Backlog: +<opened> / -<closed>
   - Eval mean: X% (delta ±Y% vs previous run)
   - Learnings: +<P> proposals, <A> accepted, <R> rejected

   ## Failures

   <one entry per failed step with error text. Empty if none.>

   ## Skipped

   <one entry per skipped step with reason. Empty if none.>
   ```

6. **Append to `log.md`:**
   ```
   ## [YYYY-MM-DD] run | profile=<profile>, <N> steps ok, <F> failed, <S> skipped
   Duration: <Ns>. Net: +<compiled> src, +<opened>/-<closed> gaps, eval ±<delta>%. Report: outputs/runs/<RUN_ID>.md.
   ```

7. **Commit.** Three cases:
   - `steps_failed` empty AND at least one step produced changes: single rollup commit `run: <profile> (<N> steps, +<compiled> src, eval ±<delta>%)`.
   - `steps_failed` non-empty: commit with message `run: <profile> (partial — <F> failed)`. Partial progress is still committed so the next tick has a clean base.
   - No steps produced changes (all no-ops): do NOT commit. The log line from step 6 is a working-tree change that stays uncommitted until the next real change; this is intentional to avoid churn.

8. **Print** the report summary. If `steps_failed` is non-empty, highlight the failures — the next tick should be scrutinized for recurrence, and `learn` may eventually propose a rule targeting the recurring failure.

### Scheduling

Use Claude Code's `schedule` skill to wire `ecogo run` into cron triggers:

```
# Daily full tick at 3am local
/schedule create --cron "0 3 * * *" --prompt "/ecogo-workflow:ecogo run"

# Hourly cheap tick during work hours, weekdays only
/schedule create --cron "0 9-17 * * 1-5" --prompt "/ecogo-workflow:ecogo run cheap"

# Weekly expensive tick Sunday 4am
/schedule create --cron "0 4 * * 0" --prompt "/ecogo-workflow:ecogo run expensive"

# Hourly canary to verify the scheduler is firing at all
/schedule create --cron "0 * * * *" --prompt "/ecogo-workflow:ecogo run canary"
```

Each trigger fires a fresh Claude Code session, invokes this skill, and the session ends after the run commits. No open session required.

### Notes

- **Idempotency matters most here.** The scheduler fires on cron regardless of whether there's work to do. Without the step-3 gate, `log.md` and git history fill with empty daily ticks.
- **Failure is expected.** Network hiccups, qmd transient errors, rate limits — they happen. `run` treats a failed step as a data point, not a reason to abort. Recurring failures show up in `learn` as a pattern and can be proposed away.
- **One `run` at a time.** A second `run` firing while the first is still working will race on `log.md`, `learnings-raw.jsonl`, and `backlog.md`. Either spread cron times (don't schedule daily + weekly at the same minute) or add a lockfile (`outputs/.run.lock`) — v1 leaves this to the scheduler.
- **Debugging a run.** If a scheduled run produces a suspicious report, do **not** debug `run` — re-run the specific op manually and inspect. `run` is pure composition; all bugs live in the composed ops.
- **Read the runs as a trend.** `outputs/runs/` accumulates a time series of tick outcomes. Grep `| failed |` across the directory to see failure patterns. Compare eval-mean deltas week-over-week to see whether the wiki is actually getting better under autonomous operation.

---

## `remove <name>`

Delete a wiki and all its contents.

### Steps

1. **Resolve wiki path:** `~/ObsidianVault/03-Resources/<name>/`

2. **Verify it exists.** If not, abort: "Wiki '<name>' does not exist."

3. **Confirm with user:** List the directory contents and ask "This will permanently delete the '<name>' wiki and all its contents. Proceed? (y/n)"

4. **Remove qmd collection** (if qmd available):
   ```bash
   "${QMD}" collection remove <name>
   ```

5. **Remove from git and filesystem:**
   ```bash
   git -C ~/ObsidianVault rm -rf "03-Resources/<name>/" && git -C ~/ObsidianVault commit -m "remove: <name> wiki"
   ```

6. **Confirm:** "Wiki '<name>' has been removed."

---

## Error Handling

Handle these failure modes gracefully:

| Situation | Action |
|-----------|--------|
| **No active wiki found** | List available wikis in `~/ObsidianVault/03-Resources/*/wiki`. Suggest `ecogo init <name>` if none exist. |
| **qmd not available** | Fall back to `wiki/index.md` for search. Warn: "qmd unavailable — using index.md fallback." |
| **Network error on URL ingest** | Retry once. If still failing, report the error and suggest saving content manually to `raw/articles/`. |
| **Git commit fails** | Warn: "Git commit failed: <error>. Changes are saved but not committed." Continue with remaining steps. |
| **Wiki already exists** (on init) | Abort with message referencing `ecogo remove`. |
| **Raw source too large** (>50KB) | Warn: "Large source detected. Entity extraction may be incomplete. Consider splitting." Proceed anyway. |
| **log.md missing** | Create fresh log.md from template at topic root. Warn: "log.md was missing — created a new one." |
| **No uncompiled sources** (on compile) | Report: "All sources are already compiled. Nothing to do." Stop. |
| **qmd collection not found** | Warn and continue without search indexing. |
| **questions.md missing or all `[REPLACE]` placeholders** (on eval) | Abort: "No evaluation questions defined. Edit `outputs/evals/questions.md` and replace the `[REPLACE]` placeholders first." |
| **history.jsonl missing on first eval** | Normal — treat previous run as absent. Set `delta_pct = null`, report "delta: first run". |
| **Answer cites a page that no longer exists** | Score `no_dead_links = 0` and record the broken wikilink in `failures[]`. Do not auto-repair during eval — that's `lint`'s job. |
| **Self-critique loop fails to converge in 3 iterations** | Normal for large or ambiguous sources. Commit what was fixed, list the remainder in `outputs/reports/<RUN_ID>-compile.md`, surface the unresolved count in `log.md`, and continue. Human review expected. |
| **Critique would require fabricating a citation** | Remove the unsupported claim instead. Never synthesize a source. A shorter, honest page beats a padded one. |
| **Critique loop regresses** (issues rose between iterations) | Treat as a no-progress signal — stop immediately, do not apply the offending iteration's fixes. Record the regression in the critique report. |
| **`outputs/backlog.md` missing** (on gap, fetch, or lint step 5) | Create it from the **backlog.md template**. Do not fail — backlog is auto-bootstrapped. |
| **`ecogo fetch` with no web tools and no MCP available** | Print formulated queries, mark the item `in-progress` with `pending-fetch: true`, instruct user to fetch manually and tag frontmatter with `fetched-for: <gap-id>`. Do not error. |
| **`ecogo fetch <gap-id>` where id is not in backlog** | Abort with "No backlog item `<gap-id>` found. Run `ecogo gap --list` (or open `outputs/backlog.md`) to see available ids." |
| **`ecogo fetch` returns 0 usable sources for an item** | Leave item in `## In Progress` with `fetched: YYYY-MM-DD (0 sources — none passed filter)`. Surface in log. Do not flip back to Open — re-running fetch is explicit. |
| **`compile` sees `fetched-for: <id>` for an id not in backlog** | Skip backlog closure silently. The source still compiles normally. Log note: "fetched-for id `<id>` not in backlog — ignored." |
| **Duplicate gap id collision** (two entries share the same `gap-YYYY-MM-DD-NNN`) | Abort with schema-integrity error. Surface the collision in log. Do not silently renumber — let the user fix the backlog manually. |
| **`outputs/learnings-raw.jsonl` write fails** (during observation emission) | Skip silently. Observations are auxiliary — never block the primary op. Log `learnings-raw.jsonl write failed: <err>` at end of op only. |
| **`outputs/learnings.md` missing on op start** | Ignore. The accepted-rules overlay applies only if the file exists. Op runs normally. |
| **Corrupt JSON line in `outputs/learnings-raw.jsonl`** (during distill) | Skip the line, continue distill. Report count of skipped lines in the learn output. Do not fail the whole distill. |
| **`ecogo learn accept` on a learning in `## Observing`** | Abort: "Only proposed learnings can be accepted. Run `ecogo learn` to distill observations into proposals first." |
| **`ecogo learn promote` on a learning not in `## Accepted`** | Abort: "Only accepted learnings can be promoted. Use `ecogo learn accept <L-id>` first." |
| **Accepted rule contradicts a CLAUDE.md rule** (detected at op preamble read) | Apply both, note the conflict in the op's result. Do not auto-resolve — surface for user to promote or reject. |
| **`run` time budget exceeded** (total_elapsed > 1800s) | Record remaining profile steps in `steps_skipped` with reason `time_budget_exceeded`. Commit partial progress. Next tick picks up where this one left off. |
| **Sub-op fails inside `run`** | Record to `steps_failed`, continue the sequence. Never abort the tick — partial progress beats total loss. Recurring failures become a `learn` pattern. |
| **Two `run` invocations overlap** | Second invocation races on shared files. Mitigate by spreading cron times or adding `outputs/.run.lock`. If corruption is detected on next `lint`, it will surface as dead links or duplicated backlog items. |
| **`run` invoked with unknown profile** | Abort with "Unknown profile '<arg>'. Valid: default, cheap, expensive, canary." No partial work. |
| **Idempotency gate false negative** (run gate says "work" but every op is a no-op) | Each op should internally detect empty-work (e.g. compile with nothing uncompiled). `run` emits a run report anyway with all steps reporting "nothing to do" and skips the final commit. |
| **`migrate` on a wiki already at v1** | Detect marker, print "Wiki already at schema v1. Nothing to do." and exit cleanly. Not an error. |
| **`migrate` partial failure** (some files created, CLAUDE.md update fails) | Leave created files in place, print which section failed, do NOT write the version marker. User can re-run migrate; it will skip existing files and retry the CLAUDE.md update. |
| **`migrate` encounters customized CLAUDE.md with some new sections already manually added** | Skip each section by heading-presence check. Still add the marker after the remaining sections are applied. Prevents duplicate section blocks. |
| **`ecogo rationale` on a v1 wiki (no v2 marker)** | Abort with: "This wiki is on v1 schema. Run `ecogo migrate` first to enable rationale extraction." Do not silently skip — the user needs to know why nothing happened. |
| **Rationale extraction hit the 100-call LLM budget mid-run** | Stop gracefully. Commit pages already processed. Emit `rationale-budget-exceeded` observation with `pages_remaining` count. User re-runs to continue; idempotency skips already-processed pages. |
| **Regex pre-pass fired 40+ candidate windows on one source** | Take top 40 by marker strength (strong markers first, then weak). Emit `rationale-rate-limited`. Do not abort; the rest of the source compiles normally. |
| **LLM judge returned malformed JSON twice in a row** | Skip this source for rationale extraction. Emit `rationale-llm-malformed` with the first 200 chars of the raw response. The source still compiles normally (source-summary, entity extraction proceed). |
| **LLM judge returned a rationale with `source_excerpt` not in the input window** | Reject that specific rationale. Emit `rationale-fabrication-attempt`. Continue processing other rationales from the same call. |
| **Rationale's `fact_anchor` does not match any concept page** | Drop the rationale silently. Emit `rationale-no-anchor` with the attempted anchor text. |
| **Promote-to-entity finds 2 matches but not 3** | Do not promote. Keep inline on both pages. Emit `rationale-similar-but-not-identical` for `learn` to consider lowering the threshold. |
| **Slug collision when creating rationale entity page** | Append `-2`, `-3`, etc. to the slug until unique. Do not fail. |
| **`ecogo rationale list` called on a wiki with no rationale callouts anywhere** | Print: "No rationales found on this wiki. Run `ecogo rationale` (no arg) to backfill." Not an error. |
| **`ecogo rationale promote <page>:<n>` when n exceeds callout count** | Abort with: `"Rationale <n> not found on <page>. Run 'ecogo rationale list <page>' to see available."`. |
| **`ecogo rationale delete <page>:<n>` on an already-promoted rationale** | Delete the local wikilink to the entity page (which is what the page currently shows). Do NOT delete the entity page itself (other pages may still link to it). Emit `rationale-deleted-by-user` with `reason: delete-of-promoted-reference`. |
| **Rationale deleted by user, then extraction tries to re-extract same rationale** | Compute rationale text hash. If hash is in `outputs/rationales/deleted.json` and `deleted_at + 90 days > now`: silently skip. Emit `rationale-skipped-per-deletion`. (If older than 90 days, re-extract as normal.) |
| **`correct` on a page with no `## Sources` section** | Abort with suggestion to re-ingest+compile or delete the page. Do not attempt grounding without explicit sources — risks inventing citations. |
| **`correct` requests a correction that would require fabricating a replacement** | Remove the claim instead. Never synthesize a substitute. Emit `manual-correction` with `action: removed (no replacement available)`. |
| **`correct` called repeatedly on the same page with no change** (2+ times in 30 days) | Surface a `correction-declined` pattern in `learn`. Proposed rule: "When user repeatedly corrects <page> but all claims ground, the sources are likely stale — suggest `ecogo fetch` for the topic." |
| **`eco go <free text>` cannot be classified to any intent** | Ask the user: "Did you want to (1) look something up, (2) fix something, (3) save new info, (4) audit the engineering docs, (5) something else?" Emit `route-ambiguous`. Never guess on destructive routes. |
| **`eco go` default-action ladder picks an op the user didn't want** | The ladder announces the branch before acting. If the user says "no, not that" in the same turn, abandon the action. If the action already ran and produced changes, those are committed — the user can revert via git or the op's own reverse action. |

---

## Templates

Used by the `init` operation. Apply verbatim, replacing `<name>` with the wiki name.

### CLAUDE.md

```markdown
# <name> Wiki Schema

## Directory Layout
- raw/              -- immutable source drops. Never edit files here.
- raw/articles/     -- text source documents (articles, papers, transcripts).
- raw/attachments/  -- images and binary attachments.
- wiki/             -- LLM-owned pages. You have full write access here.
- wiki/index.md     -- catalog. Read this FIRST before opening any other page.
- wiki/queries/     -- filed query answers. Promote to wiki/ when durable.
- outputs/reports/  -- dated lint reports and per-compile critique reports.
- outputs/evals/    -- evaluation questions, per-run judging detail, append-only score history.
- outputs/backlog.md -- structured list of knowledge gaps. `ecogo gap` adds, `ecogo fetch` works, `ecogo compile` closes.
- outputs/learnings-raw.jsonl -- append-only observation log, written by ops during runtime.
- outputs/learnings.md -- distilled learnings (observing/proposed/accepted/rejected/promoted). Read by every op as a runtime overlay.
- outputs/runs/     -- per-tick run reports written by `ecogo run`. Grep across files for failure trends and eval-mean deltas over time.
- log.md            -- append-only operation log. Never edit existing entries.

## Entity Types and Templates

### concept.md
---
date: YYYY-MM-DD
tags: [domain]
type: concept
status: active
---
# Concept Name
<one-paragraph summary>

## Details
...

## See Also
- [[related-concept]]

## Counter-Arguments and Gaps
...

### person.md
---
date: YYYY-MM-DD
tags: [domain, person]
type: person
status: active
---
# Person Name
Role / affiliation.

## Key Contributions
...

## See Also
- [[related-concept]]

### source-summary.md
---
date: YYYY-MM-DD
tags: [domain]
type: source-summary
source-url: https://...
---
# Source Title
One-paragraph summary.

## Key Points
...

## Entities Mentioned
- [[person-or-concept]]

## Slides
To export as a Marp slide deck, add `marp: true` to frontmatter and run:
  "${MARP}" wiki/<filename>.md -o output.html

### query-output.md
---
date: YYYY-MM-DD
tags: [domain]
type: query-output
question: "<original question>"
status: filed
---
# <Question as title>
<synthesized answer>

## Sources
- [[page-1]]
- [[page-2]]

## Naming Conventions
- All filenames: lowercase-kebab-case.md
- Wikilinks: [[filename-without-extension]]
- Never use standard markdown links for internal links

## Log Format
Append to log.md after every operation. Format:
  ## [YYYY-MM-DD] <operation> | <title>
  <one-line description>

Operations: ingest | compile | query | correct | rationale | eval | gap | fetch | learn | lint | run | migrate | promote | remove

## Index Format
wiki/index.md is a human- and LLM-readable catalog. Format:
  ## Domain Name
  - [[page-name]] -- one-line description (YYYY-MM-DD)

Keep entries under 80 chars. Update after every ingest.

## Cross-Reference Rules
- Every page must link to at least one other page when content warrants it
- When creating or updating a concept page, scan index.md for related entities and add [[wikilinks]]
- Flag contradictions inline: > [!WARNING] Contradiction with [[other-page]]

## Ingest Rules
1. Acquire the source (URL or file)
2. Classify the source type
3. Save to raw/articles/ with frontmatter (compiled: false)
4. Append to log.md
5. Commit
Ingest does NOT create wiki pages. Use compile for that.

## Compile Rules
1. Identify uncompiled raw sources (no matching source-summary in wiki/)
2. For each source: write source-summary, extract entities, create/update pages.
   Track every page you create or modify as `touched_pages`.
3. Backlink audit: grep existing pages for mentions of new titles
4. Self-critique loop (max 3 iterations, bounded): re-read `touched_pages` as a
   SEPARATE pass from the synthesizer. Check dead links, wikilink density,
   missing sections, grounding, fabrications, omitted entities, length ceilings.
   Break on convergence, on no-progress (issues did not decrease), or at 3 iters.
   Never fabricate to pass a check. Remove unsupported claims rather than invent citations.
5. Write critique report to outputs/reports/<RUN_ID>-compile.md
6. Update wiki/index.md
7. Append to log.md
8. Commit
9. After compile, suggest running `ecogo eval` to measure score delta.
One source typically touches 5-15 pages. This is normal.

## Query Rules
1. Read wiki/index.md first
2. Open relevant pages
3. Synthesize answer with [[wikilinks]] as citations
4. Always file answer to wiki/queries/ (mandatory, no prompt)
5. Offer promotion to wiki/ as a concept page (y/n)
6. Append to log.md (both query and optional promote events)
7. Commit changes

## Correction Rules
1. `ecogo correct <page-slug> [<claim>]` re-grounds a page against its cited sources.
2. Grounding pass is a SEPARATE read from the synthesizer — same discipline as compile self-critique and eval judge.
3. Three outcomes per claim: grounded | miscited | ungrounded | contradicted.
4. miscited (accurate per source-roots, not per cited sources) => ADD the source to the page, DO NOT delete the claim.
5. ungrounded (nothing in cited sources AND nothing in source-roots) => remove the claim. Never invent.
6. contradicted => replace with source-supported version, inline `> [!NOTE] Corrected <date> from [[<source>]]` callout.
7. API field names, version numbers, endpoint paths, config keys, numeric thresholds require VERBATIM match. Paraphrases do not count for these.
8. Interpretive claims may be paraphrases of source material if the logical consequence is supported.
9. If a page has no cited sources AND no source-roots-grep hits, correction aborts — no grounding is possible without references.
10. If all claims ground but the user still says the page is wrong, the sources are stale — suggest `ecogo fetch` for the topic.
11. One page at a time. Batch corrections risk cross-page consistency drift.

## Source Roots (optional, schema-level)
List directories the correction grounding pass may grep when a claim isn't in the cited sources.
Without this list, every uncited claim is treated as ungrounded — safe-strict behavior.
With this list, accurate-but-miscited claims are preserved and their citation fixed.

source-roots:
  # - /path/to/your/code-repo/
  # - <kb-root>/raw/   # already auto-included
  # Uncomment and add paths applicable to this wiki. Paths are grep'd verbatim for claim tokens.

## Rationale Rules (v2 schema)
1. compile step 3.5 and `ecogo rationale` op extract rationale from sources per skills/ecogo/references/rationale-extraction.md
2. Output tiers: inline [!NOTE] callout default → rationale-<slug>.md entity page when reused ≥ 3× → frontmatter tags for Dataview discovery
3. Kinds: tradeoff | alternative | historical | gotcha | other (gotcha is a preview of S3; rationale and gotcha coexist until S3 ships)
4. Confidence: high | medium | low. low-confidence rationales are rendered but clearly flagged; can be suppressed via accepted-learnings rule
5. correct op applies a distinct rubric to rationale callouts (strict on source_excerpt verbatim, loose on text paraphrase)
6. eval op's optional rationale-present criterion is reported separately from core total
7. rationale-count, rationale-tags, has-rationale-entity are additive frontmatter fields on concept pages
8. outputs/rationales/snapshot.json tracks current callouts; outputs/rationales/deleted.json holds 90-day deleted hashes
9. Deleted rationales are respected by re-extraction (skipped for 90 days)
10. 10 new observation classes feed learn; proposed rules can tune extractor behavior

## Eval Rules
1. Questions live in outputs/evals/questions.md. Each top-level `- ` bullet is one question.
2. For each question: synthesize an answer like query, then run a SEPARATE judge pass to score it.
3. Default rubric, each 0 or 1: grounded | cited | complete | no_dead_links. total = sum / 4.
4. Answers are stored under outputs/evals/<RUN_ID>/answers/, not wiki/queries/.
5. history.jsonl is append-only. Do NOT rewrite past entries when the rubric changes.
6. Ad-hoc eval (single question argument) does not append to history.jsonl.
7. Regressions vs previous run are reported explicitly in the summary and log.

## Gap Rules
1. Backlog lives in outputs/backlog.md. It has four sections: Open, In Progress, Done, Skipped.
2. Each entry is one markdown task line with this format:
   - [ ] `gap-YYYY-MM-DD-NNN` | **question|topic** | "..." | source: lint|eval|compile|user|log|wiki-page | priority: low|medium|high | added: YYYY-MM-DD
   For `source: wiki-page`, suffix with `| from: <page-slug>`.
3. `gap --scan` reads six signals: lint reports, compile unresolved reports, eval history, questions.md, log.md prose markers (follow-up|TODO|remains as|fix later|...), and wiki-page follow-up sections.
4. Ids are unique and never reused. Collision = abort, do not renumber.
5. Dedup by slug (slugified question text), not by exact string.
6. Items with status `skip` are respected forever — do not re-add on new signals.
7. Items with status `done` may be reopened if a fresh signal proves the gap returned; annotate with `reopened: YYYY-MM-DD`.
8. `gap` only adds. Closing is done by `compile` (automatic via `fetched-for` match) or manually by the user.

## Fetch Rules
1. `fetch` stages sources to raw/articles/ with `fetched-for: <gap-id>` frontmatter. Never compiles.
2. Prefer WebSearch + WebFetch. Fall back to Exa or deep-research. No tools = print queries for manual fetch.
3. Filter pages before saving: no SEO spam, no adult/unrelated material, no login-walled empties.
4. Zero usable sources leaves the item in `In Progress` with a 0-sources note — never flip back to Open automatically.
5. Backlog closure happens in `compile` step 7, not here. The fetch→compile separation is deliberate.

## Learning Rules
1. Compile, lint, eval, fetch, and gap emit observations to outputs/learnings-raw.jsonl per the class catalog in SKILL.md.
2. `ecogo learn` distills raw observations into rolled-up entries in outputs/learnings.md.
3. Proposal threshold: class count >= 5 observations AND last_seen within the last 30 days. Edit this line to tune per wiki.
4. Entries flow: Observing -> Proposed -> Accepted -> Promoted. Rejected is a terminal silencing state.
5. Accepted rules are a runtime overlay — read at the start of every op, applied as additional constraints.
6. Promoted rules are appended to this CLAUDE.md under the appropriate section with a `(learned YYYY-MM-DD)` prefix.
7. Observations are best-effort and never block ops. If the raw log can't be written, the op continues normally.
8. Rejected entries stay in outputs/learnings.md for historical context. The distill pass skips their class forever.

## Run Rules
1. `ecogo run [<profile>]` is a pure composer — it calls existing ops. No new behavior lives in run.
2. Profiles: default (compile → lint → eval → gap → fetch → compile → learn), cheap (compile → lint), expensive (eval → fetch → learn), canary (eval ad-hoc, single known-good question).
3. Idempotency gate: default and expensive profiles skip (no commit) if there is no uncompiled raw, no open backlog items, eval is fresh, and no new observations to distill. cheap and canary always run.
4. Time budget: 1800 seconds (30 min). When exceeded, remaining steps are skipped and partial progress is committed. Next tick resumes.
5. Failures do not abort the tick. Each failed step is recorded; the tick continues. Recurring failures become learn patterns.
6. Each run produces outputs/runs/<RUN_ID>.md. Never edit these — they are historical.
7. Two concurrent runs race on shared files. Spread cron times or rely on a lockfile; v1 does neither.
8. Debugging: never debug `run` itself. Re-run the suspect sub-op manually.

## Lint Rules
Scan all pages in wiki/ and report:
- Contradictions between pages
- Orphan pages (no inbound [[links]])
- Pages with status: stale older than 90 days
- Missing Counter-Arguments and Gaps section
- Index entries pointing to missing files
After fixing, append to log.md and commit.
```

### .gitignore

```
.DS_Store
*.sqlite
*.sqlite-wal
*.sqlite-shm
```

### qmd.yml

```yaml
collections:
  <name>:
    path: ./wiki
    pattern: "**/*.md"
```

### wiki/index.md

```markdown
# <name> Wiki Index

Last updated: YYYY-MM-DD

<!-- Add entries after each ingest. Format:
## Domain
- [[page-name]] -- description (YYYY-MM-DD)
-->
```

### log.md

```markdown
# <name> Wiki Log

<!-- Append only. Never edit existing entries. Format:
## [YYYY-MM-DD] ingest | Title
One-line description.
-->
```

### outputs/evals/questions.md

```markdown
# <name> — Evaluation Questions

These questions define what this wiki should be able to answer well.
`ecogo eval` runs them all and scores the answers against the rubric below.
Edit freely: add questions as you notice gaps, remove or refine ones that
become too easy or ambiguous.

## Questions

- [REPLACE] What is the core thesis or central claim of <topic>?
- [REPLACE] Who are the key people in this domain and what did each contribute?
- [REPLACE] What is the relationship between <concept-a> and <concept-b>?

## Rubric

Each answer is judged on four binary criteria (each 0 or 1):

- **grounded**: every non-trivial factual claim traces to a `[[wikilink]]` pointing at an existing page
- **cited**: answer contains at least one `[[wikilink]]`
- **complete**: answer covers every distinct clause of the question
- **no_dead_links**: every `[[wikilink]]` in the answer resolves to a file in `wiki/`

`total = sum / 4`, reported as a percentage. Mean over all questions = run score.
```

### outputs/evals/<RUN_ID>/summary.md

```markdown
# Eval Run — <RUN_ID>

**Wiki:** <name> | **Questions:** N | **Mean score:** X% | **Delta vs previous:** ±Y%

## Per-rubric means

| Grounded | Cited | Complete | No dead links |
|----------|-------|----------|---------------|
| X%       | X%    | X%       | X%            |

## Per-question

| Question | Score | Grounded | Cited | Complete | Dead links | Pages referenced |
|----------|-------|----------|-------|----------|------------|------------------|
| ...      | X%    | ✓/✗      | ✓/✗   | ✓/✗      | ✓/✗        | [[a]], [[b]]     |

## Regressions vs previous run

- "<question>" — X% → Y%. First failure: <short reason from judge>.

## Next actions

<short heuristic list from judge: which gaps would most lift the next run>
```

### outputs/backlog.md

```markdown
# <name> — Backlog

Structured list of knowledge gaps this wiki is working to close.
`ecogo gap` appends items. `ecogo fetch` pulls sources for them. `ecogo compile`
closes items whose staged sources have been integrated.

Entry format (one line each):
`- [ ] \`gap-YYYY-MM-DD-NNN\` | **question|topic** | "..." | source: lint|eval|compile|user | priority: low|medium|high | added: YYYY-MM-DD`

Never renumber ids. Never rewrite history — move items between sections only.

## Open

<!-- new items appended by `ecogo gap` land here -->

## In Progress

<!-- items with sources fetched but not yet compiled -->

## Done

<!-- items whose backing source has compiled into the wiki -->

## Skipped

<!-- items explicitly marked out of scope. Respected forever — never auto-re-added -->
```

### outputs/learnings.md

```markdown
# <name> — Learnings

Distilled patterns from the observation log (`outputs/learnings-raw.jsonl`).
Entries flow through the sections below as their status evolves.

`ecogo learn` (no subcommand) distills raw observations into rolled-up entries
and proposes rules for classes that cross the threshold. Subcommands manage
lifecycle: `accept`, `reject`, `promote`.

Entry format:

\`\`\`
### L-YYYY-MM-DD-NNN | <class> | <severity>
Observed: <N> times (first: YYYY-MM-DD, last: YYYY-MM-DD)
Pattern: <one-sentence description synthesized from evidence>
Evidence: <up to 10 recent evidence refs — page slug, question, url, etc.>
Proposed rule: <actionable rule text, or empty if not yet proposed>
[Status-specific lines: Accepted: YYYY-MM-DD | Rejected: YYYY-MM-DD — reason | Promoted: YYYY-MM-DD → CLAUDE.md ## <section>]
\`\`\`

## Observing

<!-- classes with observations below the proposal threshold -->

## Proposed

<!-- classes that crossed the threshold and have a draft rule awaiting user review -->

## Accepted

<!-- proposed rules accepted by the user. Read at op start and applied as additional constraints. -->

## Rejected

<!-- classes the user deemed not worth acting on. Silenced forever unless manually reopened. -->

## Promoted

<!-- accepted rules that have been baked into the wiki's CLAUDE.md. Kept here as history. -->
```
