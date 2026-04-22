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

// Belt-and-suspenders: render even if MSW setup fails or hangs. The refresh-invariant
// test-side fix (unregister SWs before reload) covers the specific Firefox hang we saw,
// but keeping a 3s escape hatch here protects against future regressions of similar shape.
const mockingReady = enableMocking().catch((err) => {
  console.warn("[msw] enableMocking failed:", err);
});
const mockingTimeout = new Promise<void>((resolve) => setTimeout(resolve, 3000));
Promise.race([mockingReady, mockingTimeout]).then(renderApp);
