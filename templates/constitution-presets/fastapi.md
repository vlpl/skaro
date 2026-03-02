# Constitution: <project name>

## Stack
- Language: Python 3.12+
- Framework: FastAPI 0.115+
- ORM: SQLAlchemy 2.0 (async) + Alembic
- Database: PostgreSQL 16
- Task Queue: Celery + Redis (if needed)
- Infrastructure: Docker, uvicorn, Nginx

## Coding Standards
- Linter: Ruff (ruff.toml)
- Formatter: Ruff format
- Type checker: mypy --strict
- Naming: snake_case for functions/variables, PascalCase for classes
- Max function length: 40 lines
- Max nesting depth: 3 levels
- Project structure: domain-driven (routers, services, repositories, schemas)
- Use Pydantic v2 models for all request/response schemas
- Async endpoints by default

## Testing
- Minimum coverage: 85%
- Required: unit tests for business logic (services)
- Required: integration tests for API endpoints
- Required: repository tests with test database
- Framework: pytest + pytest-asyncio + httpx (AsyncClient)
- Fixtures: conftest.py with session-scoped DB, function-scoped transactions

## Constraints
- All endpoints must have OpenAPI documentation (summary, description)
- Database migrations via Alembic only, no manual DDL
- No business logic in routers — delegate to service layer
- Dependency injection via FastAPI Depends()

## Security
- Authorization: OAuth2 + JWT (python-jose / PyJWT)
- Input validation: Pydantic schemas on all endpoints
- Secrets: environment variables via pydantic-settings (.env, never committed)
- CORS: explicit allow-list, no wildcards in production
- Rate limiting: slowapi or middleware

## LLM Rules
- Do not leave stubs without explicit TODO with justification
- Do not duplicate code: prefer reuse and clear abstractions
- Do not make hidden assumptions — if unsure, ask
- Always generate AI_NOTES.md per template
- Follow the coding style described above
- Always add type hints to function signatures
- Use async/await consistently, avoid sync calls in async context
