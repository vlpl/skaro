# Constitution: <project name>

## Stack
- Language: TypeScript 5.x
- Runtime: Node.js 22 LTS
- Framework: NestJS 11
- ORM: Prisma 6 / TypeORM
- Database: PostgreSQL 16
- Task Queue: @nestjs/bull + Redis (if needed)
- Infrastructure: Docker, PM2 / Node cluster

## Coding Standards
- Linter: ESLint with typescript-eslint + @nestjs/eslint-config
- Formatter: Prettier (.prettierrc)
- Naming: camelCase for variables/functions, PascalCase for classes/decorators
- Max function length: 40 lines
- Max nesting depth: 3 levels
- Module structure: module, controller, service, repository, dto per domain
- Use DTOs with class-validator decorators for all input
- Use NestJS dependency injection — no manual instantiation

## Testing
- Minimum coverage: 85%
- Required: unit tests for services (mocked dependencies)
- Required: integration tests for controllers (TestingModule)
- Required: e2e tests for critical flows
- Framework: Jest (NestJS default) or Vitest
- Use Test.createTestingModule for DI in tests

## Constraints
- Follow NestJS module boundaries strictly
- No circular dependencies between modules
- All endpoints documented with @ApiTags, @ApiOperation (Swagger)
- Use interceptors for cross-cutting concerns (logging, transform)

## Security
- Authorization: @nestjs/passport + JWT strategy + Guards
- Input validation: class-validator + ValidationPipe (global)
- Secrets: @nestjs/config with .env (never committed)
- CORS: enableCors with explicit allow-list
- Rate limiting: @nestjs/throttler
- Helmet: helmet via NestJS middleware

## LLM Rules
- Do not leave stubs without explicit TODO with justification
- Do not duplicate code: prefer reuse and clear abstractions
- Do not make hidden assumptions — if unsure, ask
- Always generate AI_NOTES.md per template
- Follow the coding style described above
- Use decorators idiomatically (@Injectable, @Controller, etc.)
- Prefer constructor injection over property injection
