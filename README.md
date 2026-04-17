# ecogo-workflow

**A self-correcting engineering knowledge base for software teams.** Capture architectural decisions, tradeoffs, and runbooks. Keep them synced with the code they describe. Onboard engineers, explain legacy, track post-mortems — all from natural-language commands in Claude Code.

```
eco go save https://my-rfc.example.com       # ingest an RFC
eco go how does our auth flow work?           # answered with citations
eco go the deployment runbook looks wrong     # re-ground against sources
eco go what should I work on next             # see open backlog
eco go audit the engineering docs             # find drift, broken refs, stale pages
```

## What it's for

Engineering teams accumulate decisions: *why* we picked gRPC over HTTP, *why* the retry strategy is 3-and-back-off, *why* we abandoned the v1 event schema. Most of that knowledge either lives in Slack threads that rot, in PR descriptions no one re-reads, or only in the heads of the two senior engineers who were there. When those engineers leave, the knowledge leaves with them.

ecogo-workflow is a workflow for building that knowledge in a place it can compound. It reads your RFCs, design docs, PR descriptions, and code, writes cross-linked wiki pages in your Obsidian vault, and — crucially — **re-verifies its own claims against the code they describe when you ask it to**.

### Use cases

- **Architectural Decision Records** — `rationale` extracts tradeoff/alternative/historical context so ADRs write themselves from your existing docs
- **Onboarding new engineers** — they ask `eco go how does X work?`, get an answer with citations into your codebase
- **Runbook upkeep** — when code changes, `correct` re-grounds a runbook page against the files it references and removes claims that no longer hold
- **Post-mortem catalogue** — the `learn` subsystem watches recurring issues and proposes preventive rules that harden future behaviour
- **API doc drift** — `eval` scores whether the base can still answer the questions it promised to answer; regressions surface automatically
- **Technical debt ledger** — `gap` scans your pages for "TODO / follow-up / remains as" prose and stages those items into an actionable backlog

### Why it works

Every claim on a wiki page traces back to a cited source. When a page looks wrong, `correct` grounds it — strictly for API names, versions, endpoints, and numeric thresholds (must appear verbatim in the source); loosely for interpretive prose. If a claim isn't in the cited source but is in a declared code repository ("source-root"), the citation is fixed rather than the claim deleted. The plugin treats "accurate but miscited" as a first-class outcome — which is a huge proportion of real-world engineering documentation.

## Thirteen operations

| Operation | Purpose |
|-----------|---------|
| `init` | Scaffold a new knowledge base inside your Obsidian vault |
| `migrate` | Upgrade an older base to the current schema — idempotent, additive |
| `ingest` | Save a source (URL or file) to `raw/` — does not process yet |
| `compile` | Read uncompiled sources, synthesise cross-linked wiki pages, run a bounded self-critique loop to catch fabrication and drift |
| `query` | Answer a question with `[[wikilink]]` citations and file the answer for later promotion to a concept page |
| `correct` | Re-ground a page against its cited sources and source-roots; remove unsupported claims, fix citations when they're wrong but the claim is right |
| `rationale` | Extract the *why* — tradeoffs, alternatives, historical decisions. Inline Obsidian callouts, promoted to shared entity pages when reused, frontmatter tags for discovery |
| `eval` | Score the base against a defined question set; track regressions over time |
| `gap` | Stage open knowledge gaps from lint reports, compile-unresolved flags, eval misses, and follow-up prose already living inside existing pages |
| `fetch` | Pull external sources to close open backlog items |
| `learn` | Roll up recurring observations into proposed rules; accept, reject, or promote them into schema |
| `lint` | Audit for dead links, orphan pages, missing sections |
| `run` | Composer that chains ops into profiled pipelines (default / cheap / expensive / canary) for scheduled runs |
| `remove` | Delete a knowledge base cleanly |

Plus a **natural-language router** — `/eco go <whatever you want in English>` — that maps plain language onto the right op.

## Bundled workflow skills

Two skills are bundled so the design-to-execution pipeline is available out of the box — no separate plugin install. Both are MIT-licensed redistributions from the superpowers plugin by Jesse Vincent. See [ACKNOWLEDGMENTS.md](ACKNOWLEDGMENTS.md) for credit and license.

### `/ecogo-workflow:brainstorming`

Before you build a new feature, run this to walk the idea from one-line intent through clarifying dialogue, approach tradeoffs, a design document, self-review, and a written spec. The skill enforces a hard gate: **no code gets written until the design has been approved**. The single highest-leverage habit for avoiding wasted engineering work in unfamiliar problem spaces.

```
/ecogo-workflow:brainstorming add RBAC to the admin portal
/ecogo-workflow:brainstorming we need a retry strategy for the upload service
/ecogo-workflow:brainstorming refactor the rate limiter into a standalone library
```

### `/ecogo-workflow:subagent-driven-development`

Executes a written implementation plan by dispatching a fresh subagent per task, reviewing the output in two passes (spec compliance then code quality), and looping fixes until both reviews approve. Keeps your own session context clean while work proceeds; catches scope drift, missing requirements, and quality issues before they compound.

Natural pipeline: `brainstorming` produces a spec → you hand it to the writing-plans convention → `subagent-driven-development` executes each task with review gates.

## Quick start

```bash
# Install
/plugin marketplace add alisajil/ecogo-workflow
/plugin install ecogo-workflow@ecogo-workflow
```

### Prerequisites

- Node.js 18+
- Git (`user.name` and `user.email` configured) — every op commits to your vault
- An Obsidian vault at `~/ObsidianVault/` with a `03-Resources/` directory (or configure a different path per base)

Dependencies (`qmd` for hybrid search, `marp-cli` for slide export) install automatically on first session start.

### Create a knowledge base for your project

```
/ecogo-workflow:ecogo init auth-platform
```

or, equivalently,

```
/eco go start a new knowledge base called auth-platform
```

### Feed it your engineering material

```
/eco go save https://example.com/our-auth-rfc.md
/eco go save ~/workspace/design-docs/auth-session-design.md
/ecogo-workflow:ecogo compile
```

`ingest` lands raw sources in `raw/articles/`. `compile` synthesises source summaries, extracts entities (services, people, concepts, technologies), cross-links everything, runs self-critique to catch fabrication, and captures rationale as inline callouts near the facts they explain.

### Ask engineering questions

```
/eco go how does our session renewal work?
/eco go what were the tradeoffs between gRPC and HTTP for the supplier service?
/eco go who owns the rate-limiter?
```

Answers come with `[[wikilinks]]` into your base. Every non-trivial claim has a source. Every answer is filed and promotable to a concept page.

### Keep it honest when code changes

```
/eco go the deployment runbook looks out of date
```

Routes to `correct <page-slug>`. The op re-reads the page's cited sources and — if you've declared a source-root like `/path/to/your/code-repo` — also greps the code tree. Ungrounded claims are removed (never invented). Miscited accurate claims get their citation fixed. Contradicted claims are replaced with the source-supported version plus a `[!NOTE] Corrected` callout that cites the source excerpt that overrode them.

### Let it learn from itself

Compile, lint, eval, fetch, gap, and correct all emit observations. `learn` distils those into named patterns. Once a class reaches a threshold (default: 5 observations within 30 days), `learn` drafts a proposed rule. You accept it and every subsequent op applies the rule as an additional constraint. You promote the rule to the base's schema once it has proven stable.

Example rules the subsystem tends to propose over time:
- *"When compiling person pages from single sources, do not add biographical claims unless verbatim in the source."*
- *"Rationales of kind `historical` are deleted 60%+ of the time on this base — downweight them during extraction."*
- *"Sources fetched from the `docs/internal/` root consistently miscite — always declare that path as a source-root on first encounter."*

### Run it on a schedule

```
# Daily full tick at 3am local
/schedule create --cron "0 3 * * *" --prompt "/ecogo-workflow:ecogo run"

# Hourly cheap tick during work hours (weekdays only)
/schedule create --cron "0 9-17 * * 1-5" --prompt "/ecogo-workflow:ecogo run cheap"

# Weekly expensive tick Sunday morning
/schedule create --cron "0 4 * * 0" --prompt "/ecogo-workflow:ecogo run expensive"
```

Each trigger fires a fresh Claude Code session. The base evolves overnight without you in the loop.

## Base layout

```
<your-vault>/03-Resources/<name>/
├── raw/
│   ├── articles/          # source documents you ingested
│   └── attachments/       # images, binaries
├── wiki/
│   ├── index.md           # catalog (read first)
│   ├── queries/           # filed query answers, promotable
│   └── <concept>.md       # entity pages
├── outputs/
│   ├── reports/           # dated lint + compile-critique reports
│   ├── evals/             # questions.md + per-run judging + history
│   ├── backlog.md         # open knowledge gaps
│   ├── learnings-raw.jsonl
│   ├── learnings.md       # distilled patterns + accepted rules
│   ├── rationales/        # snapshot + deleted-hash TTL
│   └── runs/              # per-tick reports from `run`
├── CLAUDE.md              # schema and conventions (the base's contract)
├── log.md                 # append-only operation history
├── .gitignore
└── qmd.yml                # search collection config
```

## Obsidian integration

Obsidian is the default editor because it is free, local-first, and renders markdown + wikilinks + callouts natively. You do not need to use Obsidian's UI to benefit from this plugin, but these integrations are free if you do:

- **Graph view** shows the wikilink topology — orphan pages are visually obvious
- **Dataview** queries work across the standard frontmatter fields the plugin populates
- **Web Clipper** saves articles directly to `raw/articles/`, ready to ingest
- **Marp** exports any page as a slide deck with `marp: true` in frontmatter

## Search

[`qmd`](https://github.com/tobilu/qmd) provides hybrid search (BM25 + vector) over wiki pages. Optional — the plugin falls back to `wiki/index.md` for small bases. qmd installs automatically via the SessionStart hook.

## Source-roots — the code-grounding feature

Declare one or more directories in the base's `CLAUDE.md` as source-roots:

```yaml
source-roots:
  - /path/to/your/code-repo
  - /path/to/your/internal-docs
```

Now when `correct` runs, claims that aren't in the cited wiki sources but ARE verbatim-present in a source-root directory are classified `miscited` rather than `ungrounded` — the citation gets fixed, the claim stays. This is the difference between a documentation tool that deletes accurate engineering knowledge because its paperwork was incomplete, and one that respects the fact that in real teams the code and the docs are often the same truth from different angles.

## Status

- `v0.1.0` — thirteen operations, natural-language router, self-critique loop, learning subsystem, scheduled runs, rationale extraction with tradeoff/alternative/historical/gotcha classification
- Golden test harness in `tests/rationales/` — reproducible per-page precision/recall gating (tolerant YAML comparator, shipping-bar thresholds)
- Bundles the `brainstorming` and `subagent-driven-development` skills from [superpowers](https://github.com/obra/superpowers) (MIT © Jesse Vincent)

## Contributing

Issues and PRs welcome. This plugin is young and every real-world use case surfaces a new signal to tune.

## License

MIT. See [LICENSE](LICENSE).

## Acknowledgments

See [ACKNOWLEDGMENTS.md](ACKNOWLEDGMENTS.md).
