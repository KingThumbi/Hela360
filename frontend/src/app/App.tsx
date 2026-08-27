/**
 * ============================================================================
 * Hela360 Enterprise Application
 * ============================================================================
 *
 * Root application component.
 *
 * Responsibilities
 * ----------------
 * • Bootstrap the application router
 * • Render the route tree
 *
 * Infrastructure such as:
 *
 * • Theme
 * • React Query
 * • Authentication
 * • Shell state
 * • Notifications
 * • Global UI providers
 *
 * is composed by AppProvider.
 *
 * ============================================================================
 */

import { RouterProvider } from "react-router-dom";

import { router } from "./router";

/* ============================================================================
 * Application
 * ============================================================================
 */

export function App() {
  return <RouterProvider router={router} />;
}

export default App;