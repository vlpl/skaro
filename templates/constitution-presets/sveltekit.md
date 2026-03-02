# Constitution: <project name>

## Stack
- Language: TypeScript 5.x
- Framework: SvelteKit 2 + Svelte 5
- State Management: Svelte stores + runes ($state, $derived)
- Styling: CSS scoped / Tailwind CSS 4
- Database: PostgreSQL 16 (via Drizzle ORM)
- Infrastructure: Docker, Node adapter

## Coding Standards
- Linter: ESLint with eslint-plugin-svelte + typescript-eslint
- Formatter: Prettier with prettier-plugin-svelte
- Naming: camelCase for variables/functions, PascalCase for components
- Max function length: 40 lines
- Max nesting depth: 3 levels
- Prefer Svelte 5 runes ($state, $derived, $effect) over legacy stores
- One component per .svelte file
- Use +page.server.ts for data loading

## Testing
- Minimum coverage: 80%
- Required: unit tests for business logic
- Required: integration tests for API routes
- Required: component tests for interactive UI
- Framework: Vitest + @testing-library/svelte
- E2E: Playwright

## Constraints
- SSR by default, CSR only where justified
- Bundle size budget: 150 KB gzipped (initial load)
- No direct DOM manipulation outside actions
- Form handling via SvelteKit form actions

## Security
- Authorization: session cookies (httpOnly, secure)
- Input validation: Zod schemas in form actions and API routes
- Secrets: $env/static/private, never exposed to client
- XSS: no {@html} without sanitization
- CSRF: SvelteKit built-in CSRF protection

## LLM Rules
- Do not leave stubs without explicit TODO with justification
- Do not duplicate code: prefer reuse and clear abstractions
- Do not make hidden assumptions — if unsure, ask
- Always generate AI_NOTES.md per template
- Follow the coding style described above
- Use load functions for data fetching, not onMount
- Prefer server-side logic in +page.server.ts / +server.ts
