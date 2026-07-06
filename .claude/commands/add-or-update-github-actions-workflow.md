---
name: add-or-update-github-actions-workflow
description: Workflow command scaffold for add-or-update-github-actions-workflow in studious-umbrella.
allowed_tools: ["Bash", "Read", "Write", "Grep", "Glob"]
---

# /add-or-update-github-actions-workflow

Use this workflow when working on **add-or-update-github-actions-workflow** in `studious-umbrella`.

## Goal

Add or update a GitHub Actions workflow for CI/CD, code analysis, or automation.

## Common Files

- `.github/workflows/*.yml`

## Suggested Sequence

1. Understand the current state and failure mode before editing.
2. Make the smallest coherent change that satisfies the workflow goal.
3. Run the most relevant verification for touched files.
4. Summarize what changed and what still needs review.

## Typical Commit Signals

- Create or update a YAML workflow file under .github/workflows/ (e.g., codeql.yml, summary.yml, stale.yml).
- Commit the workflow file with a descriptive message.

## Notes

- Treat this as a scaffold, not a hard-coded script.
- Update the command if the workflow evolves materially.