Review this architecture as a senior architect.

Domain: {domain_description}

Architecture draft:
{architecture_draft}

Perform a thorough review:

1. **Weaknesses** — find issues with: scalability, consistency, fault tolerance, observability, maintainability
2. **Constitution compliance** — verify the architecture follows all principles from the constitution
3. **Controversial decisions** — identify trade-offs and propose alternatives
4. **ADR recommendations** — which Architecture Decision Records should be created
5. **Diagrams** — suggest minimal set of diagrams needed

Then produce an IMPROVED version of the full architecture document that:
- Fixes all critical and high-severity issues found during review
- Adds an "Architectural Invariants" section with rules that MUST hold true during implementation:
  - Data flow constraints (e.g., "all mutations go through event bus")
  - Performance contracts (e.g., "p95 latency < 200ms")
  - Security invariants (e.g., "all endpoints require authentication")
  - Consistency rules (e.g., "idempotent external calls with retry")
- Preserves the author's intent and style
- Keeps all content that has no issues

You MUST format your response as exactly TWO sections with these exact headings:

## Review

For each risk: severity (CRITICAL / HIGH / MEDIUM / LOW), description, recommendation.
Then list recommended ADRs and diagram suggestions.

## Proposed Architecture

The complete, improved architecture document in Markdown. This must be a full standalone document, not a diff or partial update. It must include an "## Architectural Invariants" section.
