# Rationale Extraction — Reference

Detailed spec for the rationale-extraction pipeline used by compile step 3.5 (see SKILL.md → `compile` op) and the `wiki rationale` op (see SKILL.md → `rationale` op). SKILL.md references this doc for the marker catalog, LLM judge prompt, and confidence rubric.

## Regex marker catalog

Apply all markers case-insensitively against source prose (outside code blocks, HTML comments, tables, frontmatter).

### Strong markers — each hit triggers an LLM judge call

```
\bbecause\b
\bdue to\b
\bin order to\b
\bto avoid\b
\b(?:we|they) (?:chose|picked|went with|selected|preferred|decided|ended up with)\b
\b(?:instead of|rather than)\s+\w+
\btradeoff(s)?\b
\btrade[- ]off(s)?\b
\b(?:reject(?:ed|ing)?|abandon(?:ed)?|ruled out|dropped)\b
\b(?:the|key|main) reason (?:why|being|is)\b
\b(?:we|they) (?:wanted|needed) to\b
\bhistorically\b
\blegacy\s+\w+\s+(?:reason|decision)\b
```

### Weak markers — batched; invoke LLM judge only if no strong marker fires in the same window

```
\bthis means\b
\bthis is why\b
\botherwise\b
\b(?:if we had|had we)\b
\b(?:could have|should have)\b
```

### Negative markers — skip even if a strong marker is present

- Inside fenced code blocks (```…```)
- Inside 4-space-indented code blocks
- Inside HTML comments (`<!-- … -->`)
- Inside markdown tables (pipe-delimited lines)
- Inside YAML frontmatter (between `---` delimiters at doc top)

## Candidate windowing

For each marker hit:

1. Extract the containing sentence + 1 preceding sentence + 1 following sentence.
2. Prepend a header breadcrumb: the nearest `##` or `###` heading above the hit.
3. Dedupe overlapping windows (merge).

Cap: 40 candidate windows per source. If exceeded, keep top 40 by marker strength — all strong markers first, then weak. When two candidates tie on strength, prefer the one whose marker is closest to the start of a sentence (i.e., earliest match). Emit `rationale-rate-limited` observation.

## LLM judge prompt (shape)

**System role excerpt:**

> You are extracting decision rationale from technical documentation. Your job is to identify *why* a decision was made, not *what* it was. Extract ONLY rationale that is explicit or near-verbatim in the input. Empty array is an acceptable and often correct answer. Most marker hits in prose are incidental, not actual rationale. Never invent reasoning that is not present in the input.

**User-role input per call:**

```
SOURCE METADATA:
  path: <file path>
  title: <source title if known>
  type: <article|paper|transcript|conversation|other>

HEADER BREADCRUMB:
  <nearest heading(s)>

CANDIDATE WINDOW:
<three-sentence window>

Return a JSON array (possibly empty) of rationale objects:
[
  {
    "text": "<rationale, 1-3 sentences, natural prose>",
    "kind": "tradeoff" | "alternative" | "historical" | "gotcha" | "other",
    "confidence": "high" | "medium" | "low",
    "fact_anchor": "<claim on the wiki page this rationale explains>",
    "source_excerpt": "<verbatim substring of the CANDIDATE WINDOW>"
  }
]
```

**Validation the caller must perform:**
- `source_excerpt` must be a verbatim substring of the input window. Reject rationales where it isn't; emit `rationale-fabrication-attempt`.
- `kind` must be one of the 5 enum values.
- If JSON is malformed, retry once with a stricter reminder prompt. On second failure, emit `rationale-llm-malformed` and skip.

## Confidence rubric

- **high** — rationale matches source near-verbatim AND an explicit reason marker is present in the window.
- **medium** — rationale paraphrases source-supported reasoning; marker is present; minor inference required.
- **low** — rationale is constructed from implicit reasoning. Flag clearly to the user; may be auto-suppressed by an accepted-learnings rule (see SKILL.md → Learning Subsystem → Accepted-rules overlay).

## Inline callout render format

```markdown
> [!NOTE] Rationale (<kind>, <confidence> confidence)
> <rationale text>
> — from [[<source-summary-slug>]]
```

Callout type by kind:

- `tradeoff | alternative | historical | other` → `[!NOTE]`
- `gotcha` → `[!WARNING]`

## Insertion rule on the target page

Determine the **target concept page** by matching `fact_anchor` against:

1. Exact substring match on any `## Details` / `## Key Points` / `## Key Contributions` section.
2. Token overlap ≥ 0.6 (word-level tokenization via whitespace/punctuation split; case-insensitive) on any section's prose.
3. qmd semantic search against the page text (fallback).

Insert the callout immediately after the first paragraph where the anchor was matched. If no anchor match passes, insert at page bottom before `## See Also`. If still no location, emit `rationale-no-anchor` and drop the rationale.

## Promote-to-entity criteria

After all rationales for a compile run are produced:

1. Cluster rationale texts by token-overlap similarity.
2. Two rationales are "same" if overlap ≥ 0.85 AND `kind` matches.
(The higher threshold vs. the 0.6 anchor-matching threshold in the Insertion rule is deliberate: promotion merges only near-identical rationales, while anchor matching is permissive enough to find the right insertion point even when phrasing drifts.)
3. If a cluster has ≥ 3 distinct concept pages, create `wiki/rationale-<slug>.md` (slug derived from rationale text's first 5-8 content words). Replace inline callouts on all cluster pages with a shortened wikilink callout:

```markdown
> [!NOTE] Rationale
> See [[rationale-<slug>]] for the tradeoff analysis behind this choice.
```

4. Set `has-rationale-entity: true` on each concept page.
5. Emit `rationale-promoted-to-entity` per promotion.

## Entity page template

```markdown
---
date: YYYY-MM-DD
tags: [rationale, <domain>]
type: rationale
kind: <kind>
confidence: <high|medium|low>
status: active
rationale-of: "[[concept-1]], [[concept-2]], [[concept-3]]"
source: "[[source-summary-slug]]"
---

# Rationale: <short title synthesized from the rationale text>

<rationale text, expanded slightly with source-excerpt context>

## Context

<background on when this decision was made — pulled from source text>

## Facts Explained By This

- [[concept-1]] — <one-line note>
- [[concept-2]] — <one-line note>
- [[concept-3]] — <one-line note>

## Counter-Arguments and Gaps

<alternatives not taken; constraints that could change the decision>
```

## Frontmatter additions on concept pages (v2 schema)

```yaml
rationale-count: <integer>        # number of inline rationale callouts on this page
rationale-tags: [tradeoff, alternative]    # union of kinds present on this page
has-rationale-entity: true         # true if any inline callout has been promoted
```

All three fields are additive. v1-only tooling ignores them. `wiki migrate` adds them as part of the v2 bump.

## Delete-signal detection

After compile, a hash set of all inline rationale callouts currently on concept pages is written to `outputs/rationales/snapshot.json`:

```json
{
  "as_of": "2026-04-17T10:30:00Z",
  "callouts": {
    "<page-slug>": [
      {"hash": "sha256:<16 hex chars>", "text": "<first 80 chars>", "kind": "tradeoff"}
    ]
  }
}
```

Next scan (in `wiki lint` or `run`'s drift pass) loads the previous snapshot, compares:

- Callouts present before and still present → no-op
- Callouts present before and now replaced by a wikilink to `[[rationale-<slug>]]` → promote, emit `rationale-promoted-to-entity`
- Callouts present before and absent now → delete, emit `rationale-deleted-by-user` with evidence `{page_slug, text_hash, kind, confidence, age_days}`
- Callouts new → extracted, already emitted during compile

Deleted hashes are kept in `outputs/rationales/deleted.json` for 90 days:

```json
{
  "entries": [
    {"hash": "sha256:<16 hex>", "deleted_at": "2026-04-17T10:30:00Z", "kind": "historical"}
  ]
}
```

During future extraction, any rationale whose hash matches an entry still within the 90-day TTL is silently skipped — the user has signaled "not worth it."
