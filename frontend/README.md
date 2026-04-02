# FinLab-X Frontend

Vite + React 19 + TypeScript + Tailwind CSS v4 + shadcn/ui frontend for FinLab-X streaming chat UI.

## Commands

```bash
pnpm install          # Install dependencies
pnpm run dev          # Dev server on :5173
pnpm run build        # Production build
pnpm run test         # Unit tests (Vitest)
pnpm run test:e2e     # E2E tests (Playwright)
pnpm run lint         # ESLint
pnpm run format       # Format with Prettier
pnpm run format:check # Check formatting (CI)
```

## Structure

```
src/
├── components/
│   ├── primitives/   # shadcn/ui CLI output (Button, etc.)
│   └── ui/           # Custom composed components
├── hooks/            # Custom hooks
├── lib/
│   └── utils.ts      # cn() utility
├── App.tsx           # App shell
├── main.tsx          # Entry point
└── index.css         # Tailwind v4 + shadcn theme
```
