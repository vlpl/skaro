# Constitution: <project name>

## Stack
- Language: TypeScript 5.x
- Framework: Vue 3.5 + Vite 6
- State Management: Pinia
- Routing: Vue Router 4
- Styling: SCSS Modules / UnoCSS
- Database: PostgreSQL 16 (via REST API)
- Infrastructure: Docker, Nginx

## Coding Standards
- Linter: ESLint with eslint-plugin-vue + typescript-eslint
- Formatter: Prettier (.prettierrc)
- Naming: camelCase for variables/functions, PascalCase for components
- Max function length: 40 lines
- Max nesting depth: 3 levels
- Components: Composition API with `<script setup>`, no Options API
- One component per .vue file
- Props: defineProps with TypeScript types

## Testing
- Minimum coverage: 80%
- Required: unit tests for business logic
- Required: integration tests for API contracts
- Required: component tests for UI interactions
- Framework: Vitest + Vue Test Utils
- E2E: Playwright / Cypress

## Constraints
- Browser support: last 2 versions of Chrome, Firefox, Safari, Edge
- Bundle size budget: 180 KB gzipped (initial load)
- No mixins — use composables for shared logic
- All API calls through a centralized composable (useApi)

## Security
- Authorization: JWT tokens (httpOnly cookies)
- Input validation: Zod / Valibot schemas on all form inputs
- Secrets: environment variables (.env.local, never committed)
- XSS: no v-html without sanitization
- CSRF: SameSite cookies + custom header

## LLM Rules
- Do not leave stubs without explicit TODO with justification
- Do not duplicate code: prefer reuse and clear abstractions
- Do not make hidden assumptions — if unsure, ask
- Always generate AI_NOTES.md per template
- Follow the coding style described above
- Use composables for reusable logic
- Prefer provide/inject over deep prop drilling
