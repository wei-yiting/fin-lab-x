# FinLab-X Frontend

Next.js TypeScript application providing a Generative UI for financial analysis.

## Folder Responsibility
This directory contains the web interface that communicates with the FinLab-X Backend API to render dynamic financial artifacts.

## File Manifest
- `src/app/`: Next.js App Router definitions and page layouts.
- `src/components/`: React UI components, including Generative UI artifacts.
- `src/lib/`: API clients and Server-Sent Events (SSE) stream parsers.

## Architecture & Design
- **Generative UI**: Renders complex financial data dynamically based on agent outputs.
- **SSE Integration**: Real-time streaming of agent thoughts and tool executions.

## Implementation Guidelines
- Use functional components and React Hooks.
- Adhere to Tailwind CSS for styling.
- Ensure strict TypeScript typing (avoid `any`).
