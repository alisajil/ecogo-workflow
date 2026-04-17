# Acknowledgments

The general idea of having a language model read source material, write cross-linked wiki pages from it, file query answers back into the knowledge base, and periodically audit the base for gaps and contradictions was popularised by Andrej Karpathy in late 2025. That public pattern — not any specific implementation — inspired parts of this project's high-level architecture.

Everything in this repository that is original to it, including the thirteen operations, the evaluation harness, the learning subsystem, the self-correction pipeline with source-roots grounding, the natural-language routing layer, the scheduled-run composer, the rationale-extraction pipeline, and the golden test harness, was designed and written by Ali Sajil.

## Bundled third-party skills

### `skills/brainstorming/`

Bundled unmodified. Copyright © 2025 Jesse Vincent. MIT License.
Original source: https://github.com/obra/superpowers
The license text travels with the skill at `skills/brainstorming/LICENSE`.

This skill is included so `/ecogo-workflow:brainstorming` is available without requiring a separate plugin install. All credit for the brainstorming methodology, prompt design, and workflow goes to Jesse Vincent.

### `skills/subagent-driven-development/`

Bundled unmodified. Copyright © 2025 Jesse Vincent. MIT License.
Original source: https://github.com/obra/superpowers
The license text travels with the skill at `skills/subagent-driven-development/LICENSE`.

This skill is included so `/ecogo-workflow:subagent-driven-development` is available for executing implementation plans via per-task subagents with two-stage review (spec compliance then code quality). All credit for the subagent-driven development methodology, prompt templates, and review loops goes to Jesse Vincent.

## External tooling

Obsidian, qmd, and Marp are external tools this plugin integrates with. They are independent open-source projects and are credited through their own licenses and release notes.
