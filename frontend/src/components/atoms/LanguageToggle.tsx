import { cn } from "@/lib/utils";
import { LOCALE_LABELS, LOCALES, useLocale } from "@/lib/locale";

export function LanguageToggle() {
  const { locale, copy, setLocale } = useLocale();

  return (
    <div
      role="group"
      aria-label={copy.chatHeader.languageGroupAriaLabel}
      data-testid="language-toggle"
      className="flex items-center rounded-md border border-border p-0.5 text-xs font-medium"
    >
      {LOCALES.map((option) => {
        const active = option === locale;
        return (
          <button
            key={option}
            type="button"
            lang={option}
            aria-label={LOCALE_LABELS[option].name}
            aria-pressed={active}
            data-locale={option}
            onClick={() => setLocale(option)}
            className={cn(
              "whitespace-nowrap rounded px-2 py-1 transition-colors sm:px-2.5",
              active
                ? "bg-secondary text-foreground"
                : "text-muted-foreground hover:text-foreground",
            )}
          >
            {LOCALE_LABELS[option].short}
          </button>
        );
      })}
    </div>
  );
}
