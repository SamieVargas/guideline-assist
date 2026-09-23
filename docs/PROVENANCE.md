# Provenance of ported patterns

This repo is Python on the plain Anthropic SDK. Patterns from the two earlier builds were ported, not copied; each row names the source file and commit it was read from.

## pixels-rag, `SamieVargas/pixels-rag` @ `e01e9ed7043376f3b18e9d184d1f66f0cb4de87a` (read 2026-09-23)

| Pattern | Source | Here |
| --- | --- | --- |
| Tolerant JSON parser as the fallback behind native structured output, recording the path (native, recovered, failed) | `core/parse.py` | `core/parse.py` (ported nearly as is) |
| Constants and JSON Schemas in one module so prompt, schema and code cannot drift; list prices with a read-on date; a model with no price row raises | `core/contracts.py` | `core/contracts.py`, `core/models.py` |
| Validator returns a list of violations; citations enforced in code, not trusted from the prompt | `core/validate.py` | `core/validate.py` |
| `output_config.format` json_schema on the native contract, the shape in the system prompt on the prompt contract, one reject-and-retry with the violations named as the next user turn, `first_violations` kept | `core/answer.py`, `core/router.py` | `core/llm.py` |
| Eval runner: `--offline` path with no key, stamped markdown table plus raw JSON records, a `-partial` file on Ctrl+C, cost rows from recorded tokens | `evals/run.py` | `evals/common.py`, `evals/run_*.py` |
| Scripted stub client that pops replies and keeps every request | `tests/stubs.py` | `tests/stubs.py` (adds a responder function and cache usage fields) |
| CI runs the offline tests on every push and PR with no API key | `.github/workflows/tests.yml` | `.github/workflows/tests.yml` |

## Field-Sales-Build, `SamieVargas/Field-Sales-Build` (not read)

The brief asks for FDB's `core/validate.js`, `core/agreement.js` and its injection eval layer to be read first. FDB is a private repository and access to it was not granted in the session that built this repo, so none of its files were read and no commit can be recorded. The patterns the brief attributes to it were built from the brief's own description:

| Pattern (as the brief describes it) | Here | To do |
| --- | --- | --- |
| Closed-enum picklist generated from the library, not typed by hand | `scripts/gen_enums.py` → `core/enums.py`, drift test in `tests/test_library.py` | compare with FDB's generator and record the commit |
| Validator with reject-and-retry | `core/validate.py`, `core/llm.py` (from pixels-rag, which is read) | compare with `core/validate.js` |
| Shadow agreement against real human behaviour | `evals/run_shadow.py` | compare with `core/agreement.js`, especially how disagreements are split |
| Injection fixtures with a clean twin, several runs each, pass only on an unchanged decision | `evals/run_injection.py`, `evals/fixtures/` | compare with FDB's injection layer |

When FDB is readable, fill in the commit and adjust anything that differs; the tests pin the current behaviour.
