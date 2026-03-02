# Constitution: <project name>

## Stack
- Language: Python 3.12+
- Framework: Django 5.1 + Django REST Framework 3.15
- ORM: Django ORM + django migrations
- Database: PostgreSQL 16
- Task Queue: Celery + Redis (if needed)
- Infrastructure: Docker, gunicorn, Nginx

## Coding Standards
- Linter: Ruff (ruff.toml)
- Formatter: Ruff format
- Type checker: mypy with django-stubs
- Naming: snake_case for functions/variables, PascalCase for classes
- Max function length: 40 lines
- Max nesting depth: 3 levels
- App structure: Django apps per domain (models, views, serializers, services)
- Fat models, thin views — business logic in model methods or service layer
- Use DRF serializers for all API input/output

## Testing
- Minimum coverage: 85%
- Required: unit tests for business logic (models, services)
- Required: integration tests for API endpoints
- Required: model tests with fixtures
- Framework: pytest-django + factory_boy
- Use APIClient for endpoint tests

## Constraints
- Database migrations via Django migrate only
- No raw SQL unless justified with comment
- No logic in views — delegate to serializers or services
- All querysets must be optimized (select_related, prefetch_related)

## Security
- Authorization: Django auth + DRF permissions (IsAuthenticated, custom)
- Input validation: DRF serializers on all endpoints
- Secrets: environment variables via django-environ (.env, never committed)
- CORS: django-cors-headers with explicit allow-list
- CSRF: Django built-in CSRF middleware
- Security headers: django-security-middleware

## LLM Rules
- Do not leave stubs without explicit TODO with justification
- Do not duplicate code: prefer reuse and clear abstractions
- Do not make hidden assumptions — if unsure, ask
- Always generate AI_NOTES.md per template
- Follow the coding style described above
- Always add type hints to function signatures
- Use Django signals sparingly — prefer explicit service calls
