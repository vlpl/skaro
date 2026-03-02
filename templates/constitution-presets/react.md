# Constitution: <project name>

## Stack
- Language: TypeScript 5.x
- Framework: React 19 + Vite 6
- State Management: Zustand / React Query
- Routing: React Router 7
- Styling: CSS Modules / Tailwind CSS 4
- Database: PostgreSQL 16 (via REST API)
- Infrastructure: Docker, Nginx

## Coding Standards
- Linter: ESLint with @eslint/js + typescript-eslint
- Formatter: Prettier (.prettierrc)
- Naming: camelCase for variables/functions, PascalCase for components/types
- Max function length: 40 lines
- Max nesting depth: 3 levels
- Components: functional only, no class components
- Prefer named exports for components
- One component per file

## Testing
- Minimum coverage: 80%
- Required: unit tests for business logic
- Required: integration tests for API contracts
- Required: component tests for UI logic
- Framework: Vitest + React Testing Library
- E2E: Playwright

## Constraints
- Browser support: last 2 versions of Chrome, Firefox, Safari, Edge
- Bundle size budget: 200 KB gzipped (initial load)
- No direct DOM manipulation — use refs when necessary
- All API calls through a centralized client module

## Security
- Authorization: JWT tokens (httpOnly cookies)
- Input validation: Zod schemas on all form inputs
- Secrets: environment variables (.env.local, never committed)
- XSS: no dangerouslySetInnerHTML without sanitization
- CSRF: SameSite cookies + custom header

## LLM Rules
- Do not leave stubs without explicit TODO with justification
- Do not duplicate code: prefer reuse and clear abstractions
- Do not make hidden assumptions — if unsure, ask
- Always generate AI_NOTES.md per template
- Follow the coding style described above
- Use React hooks correctly (deps arrays, cleanup functions)
- Prefer composition over prop drilling
