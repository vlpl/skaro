# Constitution: <project name>

## Stack
- Language: TypeScript 5.x
- Runtime: Node.js 22 LTS
- Framework: Express 5
- ORM: Prisma 6 / TypeORM
- Database: PostgreSQL 16
- Task Queue: BullMQ + Redis (if needed)
- Infrastructure: Docker, PM2 / Node cluster

## Coding Standards
- Linter: ESLint with typescript-eslint
- Formatter: Prettier (.prettierrc)
- Naming: camelCase for variables/functions, PascalCase for classes/interfaces
- Max function length: 40 lines
- Max nesting depth: 3 levels
- Project structure: controllers, services, repositories, middleware, dto
- Use DTO classes/interfaces for request/response typing
- Async error handling via express-async-errors or wrapper

## Testing
- Minimum coverage: 80%
- Required: unit tests for business logic (services)
- Required: integration tests for API endpoints
- Required: middleware tests
- Framework: Vitest + supertest
- Use test database with transactions for isolation

## Constraints
- No business logic in controllers — delegate to services
- All routes must have input validation middleware
- Error handling via centralized error middleware
- Logging via structured logger (pino / winston)

## Security
- Authorization: JWT (jsonwebtoken) + middleware guard
- Input validation: Zod / class-validator on all endpoints
- Secrets: environment variables via dotenv (.env, never committed)
- CORS: cors package with explicit allow-list
- Rate limiting: express-rate-limit
- Helmet: helmet package for security headers

## LLM Rules
- Do not leave stubs without explicit TODO with justification
- Do not duplicate code: prefer reuse and clear abstractions
- Do not make hidden assumptions — if unsure, ask
- Always generate AI_NOTES.md per template
- Follow the coding style described above
- Always type function parameters and return values
- Use async/await, no callback-style code
