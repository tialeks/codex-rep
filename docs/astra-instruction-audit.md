# SP Figma instruction audit — 2026-09-06

Baseline: `bc4faa6` on `tialeks/codex-rep`, branch `master`.
Guidance: [Using GPT-6 Astra](https://developers.openai.com/api/docs/guides/latest-model), especially Prompting best practices.

## Inspected scope

All 12 tracked Markdown files in the baseline repository, including six SKILL.md files, operating rules, README, and four imported-library Markdown documents; the sorting skill's agents/openai.yaml; tracked paths for agent/configuration files. No AGENTS.md or AGENTS.override.md was tracked in the baseline. Checked standard ancestor AGENTS.md paths and /root/.codex/AGENTS.md and AGENTS.override.md in this session; none were present. This is not an inspection of the user's computer or every possible custom CODEX_HOME.

Reviewed the installed figma-use instructions relevant to the sorting skill, plus OpenAI Docs and skill-creator guidance. Other installed plugins were reviewed only at the available description/trigger level, not a full body audit. Host instructions, model selection, and ChatGPT project settings were not modified. Repository skills are not listed as installed skills in this session; the new AGENTS.md routes an agent working in the checkout to their existing locations.

## Findings and corrections

| Finding | Correction |
| --- | --- |
| Operating rules and design/component skills could require approval again after a direct edit command | Distinguish review-only requests from authorized fixes; retain scope boundaries and concrete risk escalation |
| UX/accessibility skills demanded a report before any changes | Allow inspection, requested fix, then verified result |
| Five skills lacked YAML name/description | Added narrowly scoped discovery metadata |
| No root instruction entry point; README advertised absent figma/config directories | Added concise AGENTS.md with skill routing and corrected structure |
| Global Figma source-of-truth rule could conflict with imported Framebase token rules | Scope each source of truth to its own file/library |
| Automation skill repeated historical node/property IDs | Remove stale IDs; resolve property keys from the live instance |
| Sorting workflow could add grouping during a sort-only request or omit unrelated properties/default checks | Make grouping conditional and preserve unrelated properties, defaults, identities, and geometry |
| Sorting demanded a single large call while installed figma-use limits operation batches | Respect integration limits; require a supported recovery strategy for a schema operation that cannot fit |
| Sorting rollback statement was integration-dependent | Keep documented atomicity for current figma-use only; do not assume native Plugin API rollback |
| Sorting schema workaround requested fresh approval regardless of prior approval | Preserve existing authorization for the same operation; retain escalation for unverified compatibility |

## Validation and limits

All six skills passed the bundled quick_validate.py checker. Reviewed changed guidance for review-only vs fix requests, property-key discovery, sort-only vs grouping scope, and already-authorized vs new-risk operations. Checked relative documentation links and git diff whitespace. No Figma mutations were performed: this audit validates instructions, not live execution of sorting or schema rebuilding. No application/runtime model configuration exists in the inspected tracked tree; API parameter migration is therefore not applicable.

The current installed figma-use documents failed-call atomicity; that behavior was not independently tested. Its general batching rules may still limit large shared-schema sorting tasks. Report that concrete limitation when it occurs rather than promising a guaranteed workaround. Imported library sources, licenses, and archives were preserved.
