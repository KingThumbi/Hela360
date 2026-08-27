import type { ReactNode } from "react";
import { Outlet } from "react-router-dom";

import {
  CONTENT_MAX_WIDTH,
} from "@/constants/layout";

export interface AppWorkspaceProps {
  children?: ReactNode;
}

export function AppWorkspace({
  children,
}: AppWorkspaceProps) {
  return (
    <section
      className="
        h-full
        min-h-0
        min-w-0
        w-full
        flex-1
        overflow-x-hidden
        overflow-y-auto
        bg-muted/20
      "
    >
      <div
        className="
          mx-auto
          flex
          min-h-full
          w-full
          min-w-0
          flex-col
          px-3
          py-4
          sm:px-4
          sm:py-5
          lg:px-6
          lg:py-6
        "
        style={{
          maxWidth: CONTENT_MAX_WIDTH,
        }}
      >
        <main
          className="
            flex
            min-h-0
            min-w-0
            w-full
            max-w-full
            flex-1
            flex-col
            overflow-x-hidden
          "
        >
          {children ?? <Outlet />}
        </main>
      </div>
    </section>
  );
}

export default AppWorkspace;
