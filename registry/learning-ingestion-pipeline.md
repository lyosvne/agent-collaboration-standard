# Learning Ingestion Pipeline

## Purpose

Turn articles, chats, repos, and examples into useful agent behavior without creating rule clutter.

## Pipeline

1. Capture source: article, chat, repo, code file, or tool docs.
2. Classify: product, architecture, design, engineering, testing, security, workflow.
3. Extract behavior: what should an agent do differently.
4. Check reuse: global, tool-specific, project-specific, or archive only.
5. Map upstream: reuse existing code, skill, plugin, or source where possible.
6. Decide output: rule, skill, template, checklist, or no action.
7. Verify: apply once or create an example task.
8. Retire: mark replaced ideas when a better rule exists.

## Output Rules

- Global rule only if it affects all coding agents.
- Skill only if it changes behavior at a specific trigger.
- Template only if it standardizes repeated handoff or project setup.
- Archive only if useful but not actionable.

## Required Metadata

- Original source:
- Title:
- Upstream repo:
- Source files:
- Extracted lesson:
- Suggested agent behavior:
- Output decision:
- Review date:

## Anti-Patterns

- Do not convert every article into a rule.
- Do not create a new skill for every concept.
- Do not copy upstream text if a shorter local behavior rule works.
- Do not mix project-specific lessons into global standards.

