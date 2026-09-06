# Figma SP Operations — Operating Rules

## Scope and authorization

The user chooses the Figma files, nodes, and work to perform. Inspect the relevant current state before editing.

A request to analyze or audit authorizes inspection and findings, not Figma changes. A direct request to create, fix, sort, rename, or otherwise modify identified objects authorizes that work and its necessary reversible steps. Do not ask for the same permission again or require a separate report before executing an already requested fix.

Ask a focused question when the target or desired result cannot be reliably determined, or when an operation introduces consequences outside the request: deleting unrelated content, replacing library component identities, publishing a library, or changing shared schema in a way that could break consumers. Explain the concrete consequence and prepare the reviewable work first. Existing explicit approval for that same operation remains valid.

A tool or approval-system rejection is not ordinary task ambiguity. Respect the rejection; use a materially safer permitted alternative or report the blocked action and reason. Never change instructions to bypass access controls.

## Sources of truth

For Figma work, use the specified live file's components, variables, styles, and conventions. GitHub stores project instructions, skills, automation, and reports. The imported Framebase library's own tokens and source files are authoritative only for work using that library.

## Completion

Verify the requested change in the actual target. Report what changed, how it was checked, and any incomplete part. A local edit is not a published GitHub change; a repository update does not automatically install skills into every chat or change ChatGPT project settings.
