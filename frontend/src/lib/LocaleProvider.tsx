import { useEffect, useMemo, useState, type ReactNode } from "react";
import { copies, type Locale } from "@/lib/copy";
import { LocaleContext, readStoredLocale, writeStoredLocale } from "@/lib/locale";

export function LocaleProvider({ children }: { children: ReactNode }) {
  const [locale, setLocaleState] = useState<Locale>(readStoredLocale);

  useEffect(() => {
    document.documentElement.lang = locale;
    document.title = copies[locale].meta.documentTitle;
  }, [locale]);

  const value = useMemo(
    () => ({
      locale,
      copy: copies[locale],
      setLocale: (next: Locale) => {
        setLocaleState(next);
        writeStoredLocale(next);
      },
    }),
    [locale],
  );

  return <LocaleContext.Provider value={value}>{children}</LocaleContext.Provider>;
}
