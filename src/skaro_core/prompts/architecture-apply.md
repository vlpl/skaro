You are given a project architecture document and a detailed review with recommendations.

Your task: apply ALL recommendations from the review to produce an IMPROVED architecture document.

Rules:
- Fix every CRITICAL and HIGH issue identified in the review
- Address MEDIUM issues where the fix is clear and non-controversial
- For LOW issues, add a "Known Compromises" section if one doesn't exist
- Preserve the author's writing style and document structure
- Keep all content that has no issues
- If the review recommends new sections (e.g., Architectural Invariants), add them
- If the review recommends splitting or reorganizing diagrams, do so
- Do NOT add content that wasn't recommended in the review
- The output must be a COMPLETE, standalone architecture document (not a diff)

Return ONLY the improved architecture document in Markdown. No preamble, no explanation — just the document content.

## Current Architecture

{architecture}

## Review Recommendations

{review}
