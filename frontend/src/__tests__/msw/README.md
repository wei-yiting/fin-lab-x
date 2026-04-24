# MSW Test Infrastructure

MSW (Mock Service Worker) provides API mocking for both browser and Node environments:

- **Browser** (Playwright E2E): Uses the service worker at `public/mockServiceWorker.js` to intercept network requests in the browser.
- **Node** (Vitest component tests): Uses `setupServer` from `msw/node` to intercept requests in the test process.

## Fixtures

Fixtures are SSE stream definitions that map to BDD scenarios. Each fixture file exports a typed object (`SSEStreamFixture`, `PreStreamErrorFixture`, or `NetworkFailureFixture`) describing the server response for a specific test scenario.

## URL Gating

In development mode, append `?msw_fixture=<name>` to the page URL to activate MSW with a specific fixture. Without this query parameter, MSW is not registered and the app behaves normally.

The handler reads the fixture name from the `Referer` header because `useChat`'s internal fetch does not carry the page's query string. The `Referer` header preserves the original page URL including query parameters.
