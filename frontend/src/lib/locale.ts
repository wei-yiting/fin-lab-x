import { createContext, useContext } from "react";
import { en, type Copy, type Locale } from "@/lib/copy";

export const LOCALES: readonly Locale[] = ["en", "zh-TW"];

/** Each locale labelled in its own language, so the toggle reads the same in either UI. */
export const LOCALE_LABELS: Record<Locale, { short: string; name: string }> = {
  en: { short: "EN", name: "English" },
  "zh-TW": { short: "中文", name: "繁體中文" },
};

export const LOCALE_STORAGE_KEY = "finlab-x:locale";

function isLocale(value: unknown): value is Locale {
  return LOCALES.includes(value as Locale);
}

/** Storage can throw (private mode, blocked site data) — fall back to English. */
export function readStoredLocale(): Locale {
  try {
    const stored = window.localStorage.getItem(LOCALE_STORAGE_KEY);
    return isLocale(stored) ? stored : "en";
  } catch {
    return "en";
  }
}

export function writeStoredLocale(locale: Locale): void {
  try {
    window.localStorage.setItem(LOCALE_STORAGE_KEY, locale);
  } catch {
    // Persistence is a convenience; the in-memory choice still applies.
  }
}

export interface LocaleContextValue {
  locale: Locale;
  copy: Copy;
  setLocale: (locale: Locale) => void;
}

// Outside a provider (isolated component tests) everything renders in English.
export const LocaleContext = createContext<LocaleContextValue>({
  locale: "en",
  copy: en,
  setLocale: () => {},
});

export function useLocale(): LocaleContextValue {
  return useContext(LocaleContext);
}
