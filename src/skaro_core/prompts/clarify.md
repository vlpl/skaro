Perform structured clarification of this specification.

1. Read the spec and constitution carefully.
2. Find ALL places where:
   - Ambiguous behavior (what should happen if...?)
   - Edge cases not described
   - Possible contradictions with architectural invariants
   - Missing acceptance criteria
   - Unclear boundaries (what's included / what's excluded)
   - Implicit assumptions that should be explicit
3. Generate clarification questions with suggested answer options.

Rules:
- Generate 3–7 questions maximum
- Each question must be independent and self-contained
- For each question provide 2–4 concrete answer options
- Options should cover the most likely choices (including "not needed" where appropriate)
- Prioritize questions that would most impact implementation

Return ONLY a JSON array — no preamble, no markdown fences, no explanation.

Schema:
```json
[
  {
    "question": "Clear, specific question text",
    "context": "One sentence: why this matters for implementation",
    "options": [
      "Concrete option A (e.g., 'Use #f1c40f for --color-win-highlight')",
      "Concrete option B",
      "Not needed / skip"
    ]
  }
]
```

CRITICAL: Return raw JSON array only. No ```json fences. No text before or after.
