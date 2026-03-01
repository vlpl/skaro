Perform cross-validation and comprehensive code review.

## Part 1: Cross-validation

1. **SPEC ↔ CODE**: Are ALL requirements from spec implemented? Is there code not described in spec?
2. **INVARIANTS ↔ CODE**: Are architectural invariants respected in the implementation?
3. **CONSTITUTION ↔ CODE**: Are coding standards, testing requirements, and security policies followed?

## Part 2: Code Review

Review for:
- **Correctness**: logic errors, edge cases, off-by-one, null handling
- **Error handling**: are errors caught, logged, and handled gracefully?
- **Style and consistency**: naming, structure, formatting per constitution
- **Duplication**: copy-pasted logic that should be abstracted
- **Testability**: is the code testable? are tests meaningful?
- **Security**: injections (SQL, XSS), secrets in code, authorization gaps, input validation
- **Performance**: N+1 queries, unnecessary allocations, blocking IO, missing indexes

## Output format

### SPEC ↔ CODE
List each requirement and its status: ✅ implemented / ⚠️ partially / ❌ missing
List any code that exists but is NOT in the spec.

### INVARIANTS
List each invariant and whether it's respected: ✅ / ❌ with explanation.

### MUST FIX
Issues that BLOCK merge. Include file path and line if possible.

### SHOULD IMPROVE
Recommended changes for quality. Include file path.

### NICE TO HAVE
Optional improvements for later.
