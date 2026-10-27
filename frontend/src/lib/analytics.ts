import type { BeforeSend } from "@vercel/analytics/react";

/**
 * localStorage key that opts the current browser out of Vercel Web Analytics,
 * so the developer's own visits stay out of the dashboard. Set it in DevTools:
 * `localStorage.setItem("va-disable", "1")`.
 */
export const ANALYTICS_OPT_OUT_KEY = "va-disable";

function isOptedOut(): boolean {
  // localStorage access throws in some privacy modes / blocked-storage contexts.
  try {
    return localStorage.getItem(ANALYTICS_OPT_OUT_KEY) !== null;
  } catch {
    return false;
  }
}

export const dropOptedOutEvents: BeforeSend = (event) => (isOptedOut() ? null : event);
