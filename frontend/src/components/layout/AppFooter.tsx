import { Activity, Clock, ShieldCheck } from "lucide-react";

import { Separator } from "@/components/ui/separator";

import { APP_NAME, APP_VERSION } from "@/constants/app";

/**
 * ============================================================================
 * AppFooter
 * ============================================================================
 *
 * Enterprise application footer.
 *
 * Responsibilities
 * ----------------
 * • Display application identity
 * • Display application version
 * • Display system status
 * • Display copyright information
 *
 * This component intentionally contains no business logic.
 * Runtime values (health, build, uptime, deployment information, license,
 * synchronization status, etc.) will eventually be supplied by dedicated hooks
 * or providers.
 *
 * Future Integrations
 * -------------------
 * • System health service
 * • API connectivity
 * • Build metadata
 * • Git commit SHA
 * • Environment (Development / Staging / Production)
 * • Tenant license information
 * • Synchronization status
 * • Offline mode
 * • Background job status
 * • Database connectivity
 * ============================================================================
 */

const CURRENT_YEAR = new Date().getFullYear();

export function AppFooter() {
  return (
    <footer
      className="
        flex
        h-full
        items-center
        justify-between
        gap-4
        px-6
        py-2
        text-xs
        text-muted-foreground
      "
    >
      {/* ------------------------------------------------------------------ */}
      {/* Left */}
      {/* ------------------------------------------------------------------ */}

      <div className="flex items-center gap-3">
        <span className="font-medium text-foreground">
          {APP_NAME}
        </span>

        <Separator
          orientation="vertical"
          className="h-4"
        />

        <span>v{APP_VERSION}</span>

        <Separator
          orientation="vertical"
          className="h-4"
        />

        <span>
          © {CURRENT_YEAR} Hela360 Technologies
        </span>
      </div>

      {/* ------------------------------------------------------------------ */}
      {/* Right */}
      {/* ------------------------------------------------------------------ */}

      <div className="flex items-center gap-4">
        <div className="flex items-center gap-1">
          <ShieldCheck className="h-4 w-4 text-green-600" />

          <span>Secure</span>
        </div>

        <div className="flex items-center gap-1">
          <Activity className="h-4 w-4 text-green-600" />

          <span>Operational</span>
        </div>

        <div className="flex items-center gap-1">
          <Clock className="h-4 w-4" />

          <span>UTC</span>
        </div>
      </div>
    </footer>
  );
}

export default AppFooter;