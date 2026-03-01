You are given a project's architecture document and (optionally) the review feedback.

Generate Architecture Decision Records (ADRs) for every significant architectural decision found in the architecture.

An ADR captures WHY a decision was made, what alternatives were considered, and what the consequences are.

Look for decisions about:
- Technology choices (language, framework, database, message broker, etc.)
- Architectural patterns (monolith vs microservices, event-driven, CQRS, etc.)
- Data storage and access patterns
- API design (REST, GraphQL, gRPC, etc.)
- Authentication and authorization approach
- Deployment and infrastructure choices
- Testing strategy
- Any trade-off or "we chose X over Y" situation

For each ADR, provide:
- **number** — sequential integer starting from 1
- **title** — concise decision title (e.g., "Use PostgreSQL as primary database")
- **content** — full ADR document in this exact format:

{adr_template}

Rules:
- Status for all generated ADRs must be "proposed"
- Date must be {today}
- Be specific: "Use PostgreSQL 16" not "Choose a database"
- The Alternatives section must list at least 2 real alternatives with concrete reasons for rejection
- The Consequences section must have Positive, Negative, and Risks
- Generate 3–10 ADRs depending on the architecture complexity
- Do NOT generate ADRs for obvious/trivial decisions

Return ONLY a single JSON array wrapped in ```json fences:
```json
[
  {{
    "number": 1,
    "title": "Use PostgreSQL as primary database",
    "content": "# ADR-001: Use PostgreSQL as primary database\n\n**Status:** proposed\n**Date:** {today}\n\n## Context\n..."
  }}
]
```

Architecture:
{architecture}

{review_section}
