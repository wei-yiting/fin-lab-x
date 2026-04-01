# Frontend Scaffold (S2)

Vite + React 19 + TypeScript + Tailwind CSS v4 + shadcn/ui scaffold for FinLab-X streaming chat UI.

## Commands

```bash
pnpm install          # Install dependencies
pnpm run dev          # Dev server on :5173
pnpm run build        # Production build
pnpm run test         # Unit tests (Vitest)
pnpm run test:e2e     # E2E tests (Playwright)
pnpm run lint         # ESLint
```

## Structure

```
src/
├── components/
│   ├── primitives/   # shadcn/ui CLI output (Button, etc.)
│   └── ui/           # Custom composed components (S3)
├── hooks/            # Custom hooks (S3)
├── lib/
│   └── utils.ts      # cn() utility
├── App.tsx           # App shell
├── main.tsx          # Entry point
└── index.css         # Tailwind v4 + shadcn theme
```

## Dependencies

- `ai` + `@ai-sdk/react`: Installed for S3 (not used in S2)
- `lucide-react`: Icon library (shadcn/ui default)
- `shadcn`: CLI tooling for adding primitives
