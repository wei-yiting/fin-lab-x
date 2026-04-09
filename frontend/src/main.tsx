import { StrictMode } from "react"
import { createRoot } from "react-dom/client"
import "./index.css"
import App from "./App.tsx"

async function enableMocking() {
  if (import.meta.env.MODE !== "development") return
  if (!new URLSearchParams(location.search).has("msw_fixture")) return
  const { worker } = await import("./__tests__/msw/browser")
  await worker.start({
    serviceWorker: { url: "/mockServiceWorker.js" },
    onUnhandledRequest: "bypass",
    quiet: false,
  })
}

enableMocking().then(() => {
  createRoot(document.getElementById("root")!).render(
    <StrictMode>
      <App />
    </StrictMode>,
  )
})
