# Constitution: <project name>

## Stack
- Language: TypeScript 5.x
- Framework: React Native 0.76+ (New Architecture)
- Navigation: React Navigation 7
- State Management: Zustand + TanStack Query
- Styling: StyleSheet / NativeWind (Tailwind)
- Backend API: REST / GraphQL
- Infrastructure: EAS Build (Expo) / Fastlane

## Coding Standards
- Linter: ESLint with @react-native/eslint-config + typescript-eslint
- Formatter: Prettier (.prettierrc)
- Naming: camelCase for variables/functions, PascalCase for components
- Max function length: 40 lines
- Max nesting depth: 3 levels
- Functional components only with hooks
- One component per file
- Platform-specific code via .ios.ts / .android.ts only when necessary

## Testing
- Minimum coverage: 75%
- Required: unit tests for business logic and hooks
- Required: component tests for UI interactions
- Required: integration tests for navigation flows
- Framework: Jest + React Native Testing Library
- E2E: Detox / Maestro

## Constraints
- Support iOS 15+ and Android 8+ (API 26)
- No inline styles — use StyleSheet.create or NativeWind
- All images optimized and in @1x/@2x/@3x
- Animations via Reanimated 3, not Animated API
- No synchronous bridge calls (use Turbo Modules if native)

## Security
- Authorization: JWT tokens stored in react-native-keychain (encrypted)
- Input validation: Zod schemas on all form inputs
- Secrets: react-native-config (.env, never committed)
- Certificate pinning: for production API endpoints
- No sensitive data in AsyncStorage

## LLM Rules
- Do not leave stubs without explicit TODO with justification
- Do not duplicate code: prefer reuse and clear abstractions
- Do not make hidden assumptions — if unsure, ask
- Always generate AI_NOTES.md per template
- Follow the coding style described above
- Test on both platforms before marking task done
- Prefer cross-platform solutions over platform-specific code
