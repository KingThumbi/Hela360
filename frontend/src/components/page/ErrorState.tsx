import type { ReactNode } from "react";

import { AlertTriangle } from "lucide-react";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

/**
 * ============================================================================
 * ErrorState
 * ============================================================================
 *
 * Enterprise error presentation.
 *
 * Used for:
 *
 * • API failures
 * • Network failures
 * • Unexpected errors
 * • Retryable operations
 *
 * Future Integrations
 * -------------------
 * • Error IDs
 * • Logging
 * • Sentry
 * • Support links
 * ============================================================================
 */

export interface ErrorStateProps {
  title?: string;

  description?: string;

  icon?: ReactNode;

  retryLabel?: string;

  onRetry?: () => void;

  className?: string;
}

export function ErrorState({
  title = "Something went wrong",
  description = "An unexpected error occurred while loading this page.",
  icon,
  retryLabel = "Try Again",
  onRetry,
  className,
}: ErrorStateProps) {
  return (
    <div
      className={cn(
        "flex min-h-[320px] flex-col items-center justify-center rounded-lg border bg-background p-10 text-center",
        className,
      )}
    >
      <div className="mb-4 text-destructive">
        {icon ?? <AlertTriangle className="h-12 w-12" />}
      </div>

      <h2 className="text-xl font-semibold">
        {title}
      </h2>

      <p className="mt-2 max-w-md text-sm text-muted-foreground">
        {description}
      </p>

      {onRetry && (
        <Button
          variant="outline"
          className="mt-6"
          onClick={onRetry}
        >
          {retryLabel}
        </Button>
      )}
    </div>
  );
}

export default ErrorState;