import { createBrowserRouter, Navigate } from "react-router-dom";

import { AppLayout } from "@/layouts/AppLayout";
import { ProtectedRoute } from "@/routes/ProtectedRoute";

import { LoginPage } from "@/features/auth/LoginPage";
import { DashboardPage } from "@/features/dashboard/DashboardPage";

/**
 * Hela360 Application Router
 *
 * Route Structure
 *
 * /
 * ├── login
 * ├── dashboard
 * ├── products
 * ├── customers
 * ├── inventory
 * ├── sales
 * ├── procurement
 * ├── finance
 * ├── reports
 * ├── administration
 * └── settings
 *
 * Business modules will be added incrementally.
 */

export const router = createBrowserRouter([
  /**
   * Redirect root to dashboard.
   * ProtectedRoute will redirect unauthenticated users to /login.
   */
  {
    path: "/",
    element: <Navigate to="/dashboard" replace />,
  },

  /**
   * Public routes
   */
  {
    path: "/login",
    element: <LoginPage />,
  },

  /**
   * Protected application
   */
  {
    element: (
      <ProtectedRoute>
        <AppLayout />
      </ProtectedRoute>
    ),

    children: [
      {
        path: "/dashboard",
        element: <DashboardPage />,
      },

      /*
       * Master Data
       */

      {
        path: "/products",
        element: <div>Products Module (Coming Soon)</div>,
      },

      {
        path: "/customers",
        element: <div>Customers Module (Coming Soon)</div>,
      },

      /*
       * Inventory
       */

      {
        path: "/inventory",
        element: <div>Inventory Module (Coming Soon)</div>,
      },

      /*
       * Sales
       */

      {
        path: "/sales",
        element: <div>Sales Module (Coming Soon)</div>,
      },

      /*
       * Procurement
       */

      {
        path: "/procurement",
        element: <div>Procurement Module (Coming Soon)</div>,
      },

      /*
       * Finance
       */

      {
        path: "/finance",
        element: <div>Finance Module (Coming Soon)</div>,
      },

      /*
       * Reports
       */

      {
        path: "/reports",
        element: <div>Reports Module (Coming Soon)</div>,
      },

      /*
       * Administration
       */

      {
        path: "/administration",
        element: <div>Administration Module (Coming Soon)</div>,
      },

      /*
       * Settings
       */

      {
        path: "/settings",
        element: <div>Settings Module (Coming Soon)</div>,
      },
    ],
  },

  /**
   * Catch-all
   */
  {
    path: "*",
    element: <Navigate to="/dashboard" replace />,
  },
]);