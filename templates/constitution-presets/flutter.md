# Constitution: <project name>

## Stack
- Language: Dart 3.6+
- Framework: Flutter 3.27+
- State Management: Riverpod 2 / Bloc
- Navigation: GoRouter
- Networking: Dio + Retrofit
- Database: Drift (local SQLite) / Hive
- Infrastructure: Codemagic / GitHub Actions, Firebase (optional)

## Coding Standards
- Linter: flutter_lints + custom analysis_options.yaml
- Formatter: dart format (line length: 100)
- Naming: camelCase for variables/functions, PascalCase for classes/widgets
- Max function length: 40 lines
- Max nesting depth: 3 levels
- Architecture: Clean Architecture (data, domain, presentation layers)
- One widget per file, colocate widget + state
- Use freezed for immutable data classes and unions

## Testing
- Minimum coverage: 80%
- Required: unit tests for business logic (use cases, repositories)
- Required: widget tests for UI components
- Required: integration tests for critical user flows
- Framework: flutter_test + mockito / mocktail
- Golden tests for visual regression

## Constraints
- Support iOS 15+ and Android 8+ (API 26)
- Responsive layout: support phones and tablets
- No setState in production widgets — use state management solution
- All assets registered in pubspec.yaml
- Localization via flutter_localizations + arb files

## Security
- Authorization: JWT tokens stored in flutter_secure_storage
- Input validation: form validators + custom validation layer
- Secrets: --dart-define for build-time, never in source
- Certificate pinning: for production API endpoints
- Obfuscation: --obfuscate --split-debug-info for release builds

## LLM Rules
- Do not leave stubs without explicit TODO with justification
- Do not duplicate code: prefer reuse and clear abstractions
- Do not make hidden assumptions — if unsure, ask
- Always generate AI_NOTES.md per template
- Follow the coding style described above
- Use const constructors wherever possible
- Prefer composition of widgets over inheritance
