import { Button } from "@/components/primitives/button";
import { RefreshCw } from "lucide-react";
import { useLocale } from "@/lib/locale";

export function RegenerateButton({ onRegenerate }: { onRegenerate: () => void }) {
  const { copy } = useLocale();
  return (
    <Button
      variant="outline"
      size="sm"
      data-testid="regenerate-btn"
      aria-label={copy.regenerateButton.ariaLabel}
      onClick={onRegenerate}
      className="mt-2 gap-1.5 text-xs text-muted-foreground"
    >
      <RefreshCw className="h-3 w-3" />
      {copy.regenerateButton.label}
    </Button>
  );
}
