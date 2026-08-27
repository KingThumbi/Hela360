/**
 * Login page version footer.
 */

import {
  APP_NAME,
  APP_VERSION,
} from "@/constants";

export function LoginFooter() {
  return (
    <footer className="text-center text-xs text-muted-foreground">
      {APP_NAME} v{APP_VERSION}
    </footer>
  );
}
