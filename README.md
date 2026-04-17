# ecogo-workflow

**A Claude Code plugin that gives software developers a self-correcting knowledge base.** It reads your RFCs, design docs, PR descriptions, and code. It answers your questions with citations. It fixes itself when the code changes. It learns *your* conventions over time.

You talk to it in plain English. It does the rest.

```
ecogo save https://my-rfc.example.com         ← feed it an RFC
ecogo how does our auth flow work?             ← get an answer with citations
ecogo the deployment runbook looks wrong       ← it re-grounds against your code
ecogo design a rate limiter                    ← walks you through a proper design
ecogo build me an auth service from scratch    ← design → plan → implementation
```

---

## Why a developer should care

Every engineering team has the same problem: **the knowledge rots faster than it's written**. Slack threads disappear. PR descriptions are one-shot. The two senior engineers who know why v1 was abandoned eventually leave. New engineers spend weeks "asking around".

ecogo-workflow is a disciplined habit that compounds. You feed it the sources you already write (RFCs, design docs, meeting notes, ADRs, code comments) and it:

| Situation | What it does |
|-----------|--------------|
| You write a new RFC | You ingest it; the plugin cross-links it to everything related |
| You join a new team | You ask in plain English and get grounded answers pointing into the real code |
| The code changed and docs didn't | `correct` re-grounds the affected page automatically |
| Same bug keeps biting you | `learn` notices the pattern and drafts a preventive rule |
| You're starting a new feature | `brainstorming` walks you from one-line idea to a written design spec before any code |
| You have a plan ready to execute | `subagent-driven-development` runs it task-by-task with two-stage review |

It runs in [Claude Code](https://claude.com/claude-code). Your knowledge lives in [Obsidian](https://obsidian.md) (so it's portable — plain markdown files on your own disk, not locked in a vendor's database).

---

## What you'll need before installing

Three tools. All free. All work on Mac and Windows.

1. **Claude Code** — Anthropic's CLI / desktop app. Get it from [claude.com/claude-code](https://claude.com/claude-code).
2. **Obsidian** — the editor where your knowledge will live. Get it from [obsidian.md](https://obsidian.md).
3. **Git** — for tracking changes to your knowledge base. Most devs already have this; if not, get it from [git-scm.com](https://git-scm.com).

You also need **Node.js 18+** — needed because the plugin auto-installs a search tool on first use. Get it from [nodejs.org](https://nodejs.org) if you don't have it.

---

## Step-by-step: Mac setup

### 1. Install Claude Code

Open Terminal (⌘+Space, type "Terminal", press Enter) and run:

```bash
npm install -g @anthropic-ai/claude-code
```

Then sign in:

```bash
claude
```

Follow the prompts to sign in with your Anthropic account.

### 2. Install Obsidian

Download the Obsidian DMG from [obsidian.md](https://obsidian.md) and drag it to Applications.

Open Obsidian and create a new vault:

- Click **Create** on the welcome screen
- Name it **ObsidianVault**
- Choose your home folder as the location (so the final path is `~/ObsidianVault`)
- Click **Create**

Inside the vault, create a folder called `03-Resources`:

- Right-click in the left sidebar → **New folder** → type `03-Resources`

That's the folder where your knowledge bases will live, one subfolder per topic.

### 3. Configure git (if you haven't already)

In Terminal:

```bash
git config --global user.name "Your Name"
git config --global user.email "you@example.com"
```

### 4. Install the ecogo-workflow plugin

In Claude Code (the `claude` CLI or the desktop app), run:

```
/plugin marketplace add alisajil/ecogo-workflow
/plugin install ecogo-workflow@ecogo-workflow
```

Then restart your Claude Code session to pick up the new commands.

### 5. Verify it works

Start a fresh session in Claude Code and type:

```
/ecogo
```

If you see a friendly "Base is idle. Nothing urgent." with a list of suggested next actions — you're set. Skip to **Your first 15 minutes** below.

---

## Step-by-step: Windows setup

### 1. Install Node.js

Download and run the Windows installer from [nodejs.org](https://nodejs.org). Pick the LTS version. Accept defaults.

Open **PowerShell** (press Windows key, type "PowerShell", press Enter) and verify:

```powershell
node --version
```

You should see `v18.x.x` or higher.

### 2. Install Claude Code

In PowerShell:

```powershell
npm install -g @anthropic-ai/claude-code
```

Then sign in:

```powershell
claude
```

Follow the prompts to sign in with your Anthropic account.

### 3. Install Obsidian

Download the Obsidian installer from [obsidian.md](https://obsidian.md) and run it. Accept defaults.

Open Obsidian and create a new vault:

- Click **Create** on the welcome screen
- Name it **ObsidianVault**
- Choose your user folder as the location — e.g. `C:\Users\<YourName>\ObsidianVault`
- Click **Create**

Inside the vault, create a folder called `03-Resources`:

- Right-click in the left sidebar → **New folder** → type `03-Resources`

### 4. Install Git (if you don't have it)

Download from [git-scm.com](https://git-scm.com). Run the installer. Accept defaults.

In PowerShell:

```powershell
git config --global user.name "Your Name"
git config --global user.email "you@example.com"
```

### 5. Install the ecogo-workflow plugin

In Claude Code, run:

```
/plugin marketplace add alisajil/ecogo-workflow
/plugin install ecogo-workflow@ecogo-workflow
```

Then restart your Claude Code session.

### 6. Verify it works

Start a fresh session and type:

```
/ecogo
```

If it responds with "Base is idle" — you're good.

---

## Your first 15 minutes

A guided walkthrough. Replace `auth-platform` with whatever topic you care about.

### Step 1 — Create your first knowledge base

In Claude Code:

```
/ecogo start a new knowledge base called auth-platform
```

This creates `~/ObsidianVault/03-Resources/auth-platform/` with folders for raw sources, wiki pages, reports, and a schema file. Open that folder in Obsidian if you want to see the structure.

### Step 2 — Feed it a source

Any URL or file. An RFC, a design doc, a Notion page, a GitHub README, a meeting transcript. Let's use a web source:

```
/ecogo save https://raw.githubusercontent.com/golang/go/master/doc/README.md
```

This downloads the content to `raw/articles/` — it's not processed yet.

### Step 3 — Compile

```
/ecogo-workflow:ecogo compile
```

The plugin reads the raw source, writes a summary page, extracts the interesting concepts into their own pages, cross-links everything, and captures rationale (the *why*) where it finds it. This takes a minute or two.

### Step 4 — Ask a question

```
/ecogo tell me about the Go documentation structure
```

You get back an answer with `[[wikilinks]]` — those are clickable in Obsidian and trace every claim back to the source you ingested. Every non-trivial factual claim is grounded.

### Step 5 — Check it

```
/ecogo audit the engineering docs
```

This runs the lint check — looks for broken links, orphan pages, missing sections. For a tiny base this should pass cleanly; you'll see results accumulate as the base grows.

### Step 6 — Do the smart thing

```
/ecogo
```

With no arguments, the plugin looks at the current state and picks the most useful action: compile if there's uncompiled raw material, lint if it's been a while, distill observations if the subsystem has new ones to roll up, etc. It announces what it's doing before doing it.

---

## Common workflows for developers

### "I just wrote an RFC and I want it integrated"

```
/ecogo save ~/work/rfcs/2026-04-auth-rotation.md
/ecogo-workflow:ecogo compile
/ecogo
```

### "I'm starting a new feature and want a proper design first"

```
/ecogo design an RBAC layer for the admin portal
```

This invokes the `brainstorming` skill. It asks clarifying questions one at a time, proposes 2-3 approaches with tradeoffs, writes a design spec, and hands it off to the plan skill. **It won't let you skip to code until you approve the design** — this is by design.

### "I have a written plan and want to execute it"

```
/ecogo implement the plan at docs/plans/rbac-plan.md
```

This invokes `subagent-driven-development`. It dispatches a fresh sub-agent per task, reviews the output in two passes (did they build what was asked? is the code good?), loops fixes until both gates pass, then moves to the next task.

### "I think the docs are out of date"

```
/ecogo the deployment runbook looks wrong
```

The plugin re-reads the cited sources, checks claims against your declared code directories (source-roots), and:
- Grounded claims stay
- Unsupported claims get removed (never replaced with invented text)
- Miscited-but-accurate claims get their citation fixed
- Contradicted claims get replaced with the source-supported version plus a visible "corrected" note

### "Same bug keeps biting the team"

Just keep using the plugin. Every `correct`, every `lint`, every `compile` emits observations. After 5+ observations of the same issue class within 30 days, the `learn` subsystem drafts a preventive rule. You accept or reject it. Accepted rules apply to every future run. Over weeks, the plugin learns your team's conventions and stops making the same class of mistake.

---

## Using it in an existing project

If you already have a repository of engineering docs, point the plugin at it as a "source-root":

1. Open `~/ObsidianVault/03-Resources/<your-base>/CLAUDE.md`
2. Find the **Source Roots** section
3. Add the path to your code repo, e.g.:
   ```yaml
   source-roots:
     - /Users/you/work/auth-service
     - /Users/you/work/internal-docs
   ```

Now when `correct` runs, it greps those directories to validate claims. **Accurate-but-miscited** becomes a first-class outcome: a claim about an API field that isn't in your RFC but IS in your code gets its citation fixed, not deleted.

This is the single biggest quality-of-life feature for teams where docs and code drift.

---

## Thirteen operations (for when you're ready to go deeper)

The router maps plain English onto these. You rarely need to call them directly, but they're here if you want to.

| Operation | Purpose |
|-----------|---------|
| `init` | Scaffold a new knowledge base |
| `migrate` | Upgrade an older base to the current schema (idempotent) |
| `ingest` | Save a source (URL or file) — does not process yet |
| `compile` | Read uncompiled sources, synthesise cross-linked pages, run self-critique |
| `query` | Answer a question with `[[wikilink]]` citations |
| `correct` | Re-ground a page against its sources and your code repos |
| `rationale` | Extract the *why* — tradeoffs, alternatives, historical decisions |
| `eval` | Score the base against a defined question set; track regressions |
| `gap` | Stage open knowledge gaps from reports and follow-up prose |
| `fetch` | Pull external sources to close open backlog items |
| `learn` | Roll up recurring observations into proposed rules |
| `lint` | Audit for dead links, orphan pages, missing sections |
| `run` | Composer that chains ops into profiled pipelines (for scheduled runs) |
| `remove` | Delete a knowledge base cleanly |

Plus bundled skills:

- **`/ecogo-workflow:brainstorming`** — design-first workflow with a hard gate
- **`/ecogo-workflow:subagent-driven-development`** — execute a plan via subagents with two-stage review

---

## Running it on a schedule

Let the plugin maintain your knowledge base overnight. In Claude Code:

```
# Daily upkeep at 3am local time
/schedule create --cron "0 3 * * *" --prompt "/ecogo-workflow:ecogo run"

# Hourly lightweight check during work hours, weekdays
/schedule create --cron "0 9-17 * * 1-5" --prompt "/ecogo-workflow:ecogo run cheap"

# Weekly deep pass Sunday morning (eval, fetch, distill)
/schedule create --cron "0 4 * * 0" --prompt "/ecogo-workflow:ecogo run expensive"
```

Each trigger fires a fresh Claude Code session, does the work, commits, and exits. The base compounds while you sleep.

---

## Troubleshooting

### "The slash command isn't found"

Restart your Claude Code session. Plugins load at session start.

### "The plugin says my base isn't at v2"

You created the base before v2 schema. Run:

```
/ecogo-workflow:ecogo migrate
```

It's idempotent and purely additive — nothing existing will be deleted.

### "I got an error about qmd"

qmd is the search tool this plugin auto-installs. It installs on first session after the plugin is added. If it didn't, reinstall the plugin:

```
/plugin install ecogo-workflow@ecogo-workflow --force
```

Then restart your session.

### "I'm on Windows and paths look weird"

The plugin uses tilde (`~`) expansion for home paths, which works on both Mac and Windows PowerShell. If you see a path error, use the full form:

- Mac: `/Users/<you>/ObsidianVault/03-Resources/<base>/`
- Windows: `C:\Users\<you>\ObsidianVault\03-Resources\<base>\`

### "My vault isn't under git"

Some features commit to your vault for history. If `~/ObsidianVault` isn't a git repo, those commit steps silently skip — the plugin still works, you just don't get the git diff trail. To add it:

```bash
cd ~/ObsidianVault
git init
git add .
git commit -m "initial commit"
```

### "The plugin is doing too much / too little"

Look at your `~/ObsidianVault/03-Resources/<base>/outputs/learnings.md`. You'll see proposed rules from the `learn` subsystem. Accept the ones that match your preferences, reject the ones that don't. The plugin progressively tunes to your style.

---

## What's inside (architecture, for the curious)

- **13 operations** covering the knowledge-base lifecycle
- **Natural-language router** that maps plain English onto ops and bundled skills
- **Self-critique loop** inside `compile` — bounded 3-iteration, catches fabrication at creation time
- **Three-way grounding** in `correct` (grounded / miscited / ungrounded / contradicted) with source-roots fallback
- **Learning subsystem** — observations → proposed rules → user accept → runtime overlay → schema promotion
- **Rationale extraction** — regex pre-pass + LLM judge + promote-to-entity clustering; tradeoff / alternative / historical / gotcha classification
- **Model routing policy** — Haiku for mechanical work, Sonnet for standard, Opus for deep reasoning
- **Effort-mode awareness** — degrades gracefully in Claude Code's fast mode; full discipline in extended-thinking mode

Full technical details live in the skill file at `skills/ecogo/SKILL.md`.

---

## Status

- `v0.3.0` — current release with intelligent skill orchestration, model routing, self-improvement loop
- MIT-licensed
- Bundles the `brainstorming` and `subagent-driven-development` skills from [superpowers](https://github.com/obra/superpowers) (MIT © Jesse Vincent)

## Contributing

Issues and PRs welcome. Every real-world use case surfaces a new signal to tune.

## License

MIT. See [LICENSE](LICENSE).

## Acknowledgments

See [ACKNOWLEDGMENTS.md](ACKNOWLEDGMENTS.md).
