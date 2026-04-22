import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "./index.css";
import App from "./App.tsx";

async function enableMocking() {
  const mode = import.meta.env.MODE;
  if (mode !== "development" && mode !== "e2e") return;
  if (!new URLSearchParams(location.search).has("msw_fixture")) return;
  const { worker } = await import("./__tests__/msw/browser");
  await worker.start({
    serviceWorker: { url: "/mockServiceWorker.js" },
    onUnhandledRequest: "bypass",
    quiet: false,
  });
}

function renderApp() {
  createRoot(document.getElementById("root")!).render(
    <StrictMode>
      <App />
    </StrictMode>,
  );
}

// Render even if MSW setup fails or hangs — firefox has been observed to hang worker.start()
// when re-registering an already-active service worker on page reload. Falling back after 3s
// keeps the app visible so tests that don't depend on fixture routing can still run.
const mockingReady = enableMocking().catch((err) => {
  console.warn("[msw] enableMocking failed:", err);
});
const mockingTimeout = new Promise<void>((resolve) => setTimeout(resolve, 3000));
Promise.race([mockingReady, mockingTimeout]).then(renderApp);
