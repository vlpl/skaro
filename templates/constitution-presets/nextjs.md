# Constitution: <project name>

## Stack
- Language: TypeScript 5.x
- Framework: Next.js 15 (App Router)
- State Management: React Context + TanStack Query
- Styling: Tailwind CSS 4 / CSS Modules
- ORM: Prisma 6 / Drizzle
- Database: PostgreSQL 16
- Infrastructure: Docker, Vercel / Node.js

## Coding Standards
- Linter: ESLint with next/core-web-vitals + typescript-eslint
- Formatter: Prettier (.prettierrc)
- Naming: camelCase for variables/functions, PascalCase for components
- Max function length: 40 lines
- Max nesting depth: 3 levels
- Use Server Components by default, 'use client' only when needed
- Colocate components with routes in app/ directory
- One component per file

## Testing
- Minimum coverage: 80%
- Required: unit tests for business logic and utilities
- Required: integration tests for API routes
- Required: component tests for interactive UI
- Framework: Vitest + React Testing Library
- E2E: Playwright

## Constraints
- Server Components by default, Client Components only for interactivity
- Bundle size budget: 200 KB gzipped (initial JS)
- Images via next/image only
- All data fetching in Server Components or Route Handlers

## Security
- Authorization: NextAuth.js / Auth.js with JWT sessions
- Input validation: Zod schemas in Server Actions and Route Handlers
- Secrets: environment variables (NEXT_PUBLIC_ prefix only for client)
- XSS: no dangerouslySetInnerHTML without sanitization
- CSRF: Server Actions have built-in CSRF protection

## LLM Rules
- Do not leave stubs without explicit TODO with justification
- Do not duplicate code: prefer reuse and clear abstractions
- Do not make hidden assumptions — if unsure, ask
- Always generate AI_NOTES.md per template
- Follow the coding style described above
- Prefer Server Components; add 'use client' only with justification
- Use server actions for mutations where appropriate
