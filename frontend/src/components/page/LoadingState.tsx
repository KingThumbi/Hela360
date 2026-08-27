import { Loader2 } from "lucide-react";

import { cn } from "@/lib/utils";

/**
 * ============================================================================
 * LoadingState
 * ============================================================================
 *
 * Standard loading state used throughout Hela360.
 *
 * Responsibilities
 * ----------------
 * • Display a loading indicator
 * • Provide optional loading message
 * • Maintain consistent spacing
 *
 * Future Integrations
 * -------------------
 * • Skeleton layouts
 * • Progress indicators
 * • Cancellable operations
 * • Loading variants
 * ============================================================================
 */

export interface LoadingStateProps {
  title?: string;

  description?: string;

  className?: string;
}

export function LoadingState({
  title = "Loading...",
  description = "Please wait while we retrieve your data.",
  className,
}: LoadingStateProps) {
  return (
    <div
      className={cn(
        "flex min-h-[320px] flex-col items-center justify-center gap-4 text-center",
        className,
      )}
    >
      <Loader2 className="h-10 w-10 animate-spin text-primary" />

      <div className="space-y-1">
        <h2 className="text-lg font-semibold">
          {title}
        </h2>

        <p className="text-sm text-muted-foreground">
          {description}
        </p>
      </div>
    </div>
  );
}

export default LoadingState;