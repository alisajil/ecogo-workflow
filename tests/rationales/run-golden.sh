#!/usr/bin/env bash
# Golden test harness for rationale extraction.
# Invokes `claude` with a prompt that executes ecogo rationale for each page,
# captures the structured output, and diffs against the expected YAML.
#
# Usage:
#   run-golden.sh                   # run all golden pages
#   run-golden.sh <page-slug>       # run one page
#   KB_PATH=/path/to/base run-golden.sh
#
# Requires: claude CLI, PyYAML, a v2-migrated knowledge base at KB_PATH.

set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
KB_PATH="${KB_PATH:-${HOME}/ObsidianVault/03-Resources/example-wiki}"
ACTUAL_DIR="${HERE}/.actual"
mkdir -p "${ACTUAL_DIR}"

# Pre-flight
if ! command -v claude >/dev/null 2>&1; then
    echo "ERROR: claude CLI not on PATH" >&2
    exit 2
fi
if [ ! -d "${KB_PATH}" ]; then
    echo "ERROR: knowledge base not found at ${KB_PATH}." >&2
    echo "       Set KB_PATH to point at a v2-migrated base." >&2
    exit 2
fi
if ! grep -qF "v2 applied" "${KB_PATH}/CLAUDE.md" 2>/dev/null; then
    echo "ERROR: ${KB_PATH} is not v2-migrated. Run 'ecogo migrate' first." >&2
    exit 2
fi

# Target pages: either the single arg or every .expected.yaml in this dir
if [ "$#" -ge 1 ]; then
    SLUGS=("$1")
else
    SLUGS=()
    for f in "${HERE}"/*.expected.yaml; do
        slug="$(basename "$f" .expected.yaml)"
        SLUGS+=("$slug")
    done
fi

if [ "${#SLUGS[@]}" -eq 0 ]; then
    echo "ERROR: no .expected.yaml files found in ${HERE}" >&2
    exit 2
fi

PASSED=0
FAILED=0
RESULTS=()

for slug in "${SLUGS[@]}"; do
    expected="${HERE}/${slug}.expected.yaml"
    actual="${ACTUAL_DIR}/${slug}.actual.yaml"
    metrics="${ACTUAL_DIR}/${slug}.metrics.json"

    if [ ! -f "$expected" ]; then
        echo "SKIP: no expected file for ${slug}" >&2
        continue
    fi

    # Control pages (expected_count: 0) skip the claude call entirely
    expected_count_flag=""
    if grep -qE "^expected_count:\s*0\b" "$expected"; then
        expected_count_flag="--expected-count=0"
        echo '[]' > "${actual}.prep"
    fi

    echo "=== ${slug} ==="

    if [ -z "$expected_count_flag" ]; then
        PROMPT=$(cat <<PROMPT_END
You are running a golden-test harness. Do NOT ask for confirmation, do NOT print prose, do NOT commit, do NOT modify any base files.

Perform a dry-run of ecogo rationale for this exact page:
  Base: ${KB_PATH}
  Page: wiki/${slug}.md

Read the page's ## Sources section. Resolve cited source-summary wikilinks to their source-url paths. Read those raw source files.

Run the rationale-extraction pipeline from skills/ecogo/references/rationale-extraction.md:
  - regex pre-pass on source prose
  - LLM judge on each candidate window
  - validate (source_excerpt must be verbatim substring)

Output a JSON array of the validated rationale objects and NOTHING ELSE. Do not write to disk. Do not modify the page. Do not promote to entity pages.

If zero rationales are produced, output exactly: []
PROMPT_END
)
        set +e
        RAW=$(cd / && claude -p "$PROMPT" 2>/dev/null)
        set -e
        echo "$RAW" | awk 'BEGIN{p=0} /^\[/{p=1} p; /^\]$/{p=0}' > "${actual}.raw.json"

        # Convert JSON array to YAML list for the comparator
        python3 -c "
import json, sys, yaml
with open('${actual}.raw.json') as f:
    try:
        data = json.load(f) or []
    except Exception:
        data = []
print(yaml.safe_dump(data, sort_keys=False, default_flow_style=False), end='')
" > "$actual"
    fi

    # Compare
    set +e
    python3 "${HERE}/compare.py" "$expected" "${actual:-${actual}.prep}" $expected_count_flag > "$metrics"
    RC=$?
    set -e

    if [ $RC -eq 0 ]; then
        echo "PASS"
        PASSED=$((PASSED + 1))
        RESULTS+=("PASS: ${slug}")
    else
        echo "FAIL"
        FAILED=$((FAILED + 1))
        RESULTS+=("FAIL: ${slug}")
        echo "  See ${metrics} for detail"
    fi

    cat "$metrics"
    echo
done

echo "=== SUITE ==="
for line in "${RESULTS[@]}"; do
    echo "  $line"
done
echo "Passed: ${PASSED}  Failed: ${FAILED}"

exit $FAILED
