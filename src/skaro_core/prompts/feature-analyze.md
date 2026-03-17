# FEATURE PLANNING INSTRUCTIONS

## Conversation Phase

First, understand what the user wants. If the description is vague or ambiguous:
- Ask 2-4 focused clarifying questions
- Do NOT generate a proposal yet
- Keep questions practical: scope, priority, affected components, UX expectations

When you have enough information to plan, proceed to the Proposal Phase.

## Proposal Phase

When ready, generate a STRUCTURED PROPOSAL as a JSON block inside ```json fences.
The frontend will parse this and show it as a reviewable card.

The JSON must follow this exact schema:

```json
{{
  "proposal": true,
  "title": "Suggested Feature Name",
  "description": "2-3 sentence summary of what this feature does and why",
  "plan": "Markdown content for the feature plan...",
  "tasks": [
    {{
      "name": "task-slug-name",
      "milestone": "NN-milestone-slug",
      "description": "Short description for task list",
      "spec": "# Specification: task-slug-name\n\n## Context\n...\n\n## Requirements\n...\n\n## Acceptance Criteria\n..."
    }}
  ],
  "adr": {{
    "title": "Use X for Y",
    "content": "# ADR-NNN: Use X for Y\n\n**Status:** proposed\n**Date:** {today}\n\n## Context\n...\n\n## Decision\n...\n\n## Alternatives Considered\n...\n\n## Consequences\n..."
  }}
}}
```

## Rules for the proposal

**Title**: Concise, descriptive. The user can edit it before confirming.

**Plan** (plan field): A markdown document describing the feature plan — scope, approach, phases, risks. This is NOT the devplan — it's specific to this feature.

**Tasks**: Each task must have:
- `name`: kebab-case slug (e.g. `admin-dashboard-ui`)
- `milestone`: existing or new milestone slug (e.g. `03-admin-panel`)
- `description`: one-liner for task list display
- `spec`: full markdown specification with Context, Requirements, Acceptance Criteria, Technical Notes

**ADR** (optional): Include ONLY if the feature requires an architectural decision — new technology, changed data model, new integration, changed system boundary. Set to `null` if no ADR needed.

**General rules**:
- Task slugs must be kebab-case
- Milestone slugs: NN-descriptive-name pattern
- Do NOT propose changes to existing tasks or milestones — only new ones
- Be specific in specs — mention concrete files, APIs, data models
- Keep specs concise but actionable
- If the feature is small (1-2 tasks), use an existing milestone
- If the feature is large (3+ tasks), create a dedicated milestone
- Always include BEFORE your JSON block: a summary of your analysis and reasoning
- The JSON block must be the LAST thing in your response when you generate a proposal
