# Rationale Extraction — Golden Test Suite

Reproducible verification for `ecogo rationale` behavior. Each `<page-slug>.expected.yaml` file encodes the set of rationales that should be extractable from a specific knowledge-base page given its cited sources.

## Prerequisites

- `claude` CLI on PATH (Claude Code installed)
- A v2-migrated knowledge base at `~/ObsidianVault/03-Resources/<base-name>/` — the harness reads the target path from the `KB_PATH` env var (default: `~/ObsidianVault/03-Resources/example-wiki/`).
- Sources cited by the golden pages are readable (check with `ls` before running).

## Usage

Run the full golden suite:

```bash
./tests/rationales/run-golden.sh
```

Run a single page:

```bash
./tests/rationales/run-golden.sh provider-integration-pattern
```

Override the knowledge-base path:

```bash
KB_PATH=~/ObsidianVault/03-Resources/my-wiki ./tests/rationales/run-golden.sh
```

## Output

- Actual extraction: `tests/rationales/.actual/<page-slug>.actual.yaml`
- Diff vs expected: `tests/rationales/.actual/<page-slug>.diff.txt`
- Metrics: `tests/rationales/.actual/<page-slug>.metrics.json` with precision, recall, false-positive count

## Shipping thresholds

- Precision ≥ 0.85
- Recall ≥ 0.70
- Control page (`homepage`): exactly 0 rationales

If metrics fall below thresholds: iterate the LLM prompt in `skills/ecogo/references/rationale-extraction.md`, re-run the harness, repeat until thresholds hold.

## Expected-YAML schema

Each file is a list of expected rationales:

```yaml
# <page-slug>.expected.yaml
- text_contains:     # substrings the extracted `text` must contain (all must match)
    - "latency"
    - "tradeoff"
  kind: tradeoff
  min_confidence: medium
  source_contains:   # optional — substring required in the source footer
    - "architecture-doc"
```

An extraction is a "match" for an expected entry if:
- `text_contains` items are all substrings of the extracted `text` (case-insensitive)
- `kind` matches exactly
- Extracted `confidence` ≥ `min_confidence` (high > medium > low)
- If `source_contains` is specified, the extracted source footer contains all of its items

## Control pages

Pages in `<control>.expected.yaml` with `expected_count: 0` must produce zero extracted rationales. Any false positive is a regression.

## Included golden pages

The repo ships five expected-YAML files demonstrating the schema. They are illustrative — to actually run the harness you need concept pages with the same slugs in your knowledge base. Substitute your own page slugs for your wiki.

| Slug | Kind expected | Purpose |
|------|---------------|---------|
| `provider-integration-pattern` | tradeoff + alternative + historical | adapter/integration rationale example |
| `microservices-architecture` | tradeoff + alternative | decomposition + comms-choice example |
| `clean-architecture-pattern` | tradeoff × 2 | layered-architecture example |
| `nats-jetstream-messaging` | tradeoff + alternative | event-bus-choice example |
| `homepage` | (control — 0 rationales) | regression guard against false positives |
