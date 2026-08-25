/**
 * Resolves backend API endpoint URLs. In dev and tests VITE_API_BASE_URL is
 * unset, so paths stay relative and flow through the Vite proxy / MSW
 * handlers unchanged. Deployed builds set it to the backend origin, making
 * every endpoint a direct cross-origin call. Components pass a path and never
 * read the env var themselves.
 */
const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? "").replace(/\/+$/, "");

export function apiUrl(path: string): string {
  return `${API_BASE_URL}${path}`;
}
