import { createBrowserRouter, Navigate } from "react-router-dom";

import { AppLayout } from "@/layouts/AppLayout";
import { OfficeAppLayout } from "@/layouts/OfficeAppLayout";
import { ROUTE_PERMISSION_REQUIREMENTS } from "@/routes/permissions";
import { OfficeProtectedRoute } from "@/routes/OfficeProtectedRoute";
import { OFFICE_PATHS } from "@/routes/officeRoutes";
import { ProtectedRoute } from "@/routes/ProtectedRoute";
import { PATHS } from "@/routes/routes";
import {
  ApplicationProvider,
  ShellProvider,
} from "@/providers";
import { LoginPage } from "@/features/auth/LoginPage";
import {
  BrandsPage,
  CategoriesPage,
  DataQualityPage,
  MasterItemDetailPage,
  MasterItemsPage,
  ReviewQueuePage,
} from "@/features/office/catalogue";
import { OfficeDashboardPage } from "@/features/office/dashboard/OfficeDashboardPage";
import {
  CatalogueSupplierDetailPage,
  CatalogueSuppliersPage,
} from "@/features/office/suppliers";
import { CustomersPage } from "@/features/customers";
import { DashboardPage } from "@/features/dashboard";
import {
  CreateStockCountPage,
  CreateStockAdjustmentPage,
  GoodsReceiptDetailPage,
  GoodsReceiptHistoryPage,
  InventoryPage,
  ReceiveStockPage,
  StockAdjustmentDetailPage,
  StockAdjustmentsPage,
  StockCountDetailPage,
  StockCountsPage,
} from "@/features/inventory";
import {
  MasterCataloguePage,
  ProductsPage,
} from "@/features/products";
import {
  PosPage,
  RefundsPage,
  SaleReceiptPage,
  SalesHistoryPage,
} from "@/features/sales";
import { SuppliersPage } from "@/features/suppliers";

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
    path: PATHS.ROOT,
    element: (
      <Navigate
        to={PATHS.DASHBOARD}
        replace
      />
    ),
  },

  /**
   * Public routes
   */
  {
    path: PATHS.LOGIN,
    element: <LoginPage />,
  },

  /**
   * Protected application
   */
  {
    element: (
      <ShellProvider>
        <ApplicationProvider>
          <ProtectedRoute>
            <AppLayout />
          </ProtectedRoute>
        </ApplicationProvider>
      </ShellProvider>    
    ),

    children: [
      {
        path: PATHS.DASHBOARD,
        element: <DashboardPage />,
      },

      /*
       * Master Data
       */

      {
        path: PATHS.PRODUCTS.ROOT,
        element: (
          <ProtectedRoute
            permission={
              ROUTE_PERMISSION_REQUIREMENTS[
                PATHS.PRODUCTS.ROOT
              ].permission
            }
          >
            <ProductsPage />
          </ProtectedRoute>
        ),
      },

      {
        path: PATHS.PRODUCTS.CATALOGUE,
        element: (
          <ProtectedRoute
            permission={
              ROUTE_PERMISSION_REQUIREMENTS[
                PATHS.PRODUCTS.CATALOGUE
              ].permission
            }
          >
            <MasterCataloguePage />
          </ProtectedRoute>
        ),
      },

      {
        path: PATHS.CUSTOMERS.ROOT,
        element: (
          <ProtectedRoute
            permission={
              ROUTE_PERMISSION_REQUIREMENTS[
                PATHS.CUSTOMERS.ROOT
              ].permission
            }
          >
            <CustomersPage />
          </ProtectedRoute>
        ),
      },

      /*
       * Inventory
       */

      {
        path: PATHS.INVENTORY.ROOT,
        element: (
          <ProtectedRoute
            permission={
              ROUTE_PERMISSION_REQUIREMENTS[
                PATHS.INVENTORY.ROOT
              ].permission
            }
          >
            <InventoryPage />
          </ProtectedRoute>
        ),
      },

      {
        path: PATHS.INVENTORY.RECEIVE,
        element: (
          <ProtectedRoute
            permission={
              ROUTE_PERMISSION_REQUIREMENTS[
                PATHS.INVENTORY.RECEIVE
              ].permission
            }
          >
            <ReceiveStockPage />
          </ProtectedRoute>
        ),
      },

      {
        path: PATHS.INVENTORY.RECEIPTS,
        element: (
          <ProtectedRoute
            permission={
              ROUTE_PERMISSION_REQUIREMENTS[
                PATHS.INVENTORY.RECEIPTS
              ].permission
            }
          >
            <GoodsReceiptHistoryPage />
          </ProtectedRoute>
        ),
      },

      {
        path: PATHS.INVENTORY.RECEIPT,
        element: (
          <ProtectedRoute
            permission={
              ROUTE_PERMISSION_REQUIREMENTS[
                PATHS.INVENTORY.RECEIPT
              ].permission
            }
          >
            <GoodsReceiptDetailPage />
          </ProtectedRoute>
        ),
      },

      {
        path: PATHS.INVENTORY.STOCK_COUNTS,
        element: (
          <ProtectedRoute
            permission={
              ROUTE_PERMISSION_REQUIREMENTS[
                PATHS.INVENTORY.STOCK_COUNTS
              ].permission
            }
          >
            <StockCountsPage />
          </ProtectedRoute>
        ),
      },

      {
        path: PATHS.INVENTORY.STOCK_COUNT_NEW,
        element: (
          <ProtectedRoute
            permission={
              ROUTE_PERMISSION_REQUIREMENTS[
                PATHS.INVENTORY.STOCK_COUNT_NEW
              ].permission
            }
          >
            <CreateStockCountPage />
          </ProtectedRoute>
        ),
      },

      {
        path: PATHS.INVENTORY.STOCK_COUNT,
        element: (
          <ProtectedRoute
            permission={
              ROUTE_PERMISSION_REQUIREMENTS[
                PATHS.INVENTORY.STOCK_COUNT
              ].permission
            }
          >
            <StockCountDetailPage />
          </ProtectedRoute>
        ),
      },

      {
        path: PATHS.INVENTORY.STOCK_ADJUSTMENTS,
        element: (
          <ProtectedRoute
            permission={
              ROUTE_PERMISSION_REQUIREMENTS[
                PATHS.INVENTORY.STOCK_ADJUSTMENTS
              ].permission
            }
          >
            <StockAdjustmentsPage />
          </ProtectedRoute>
        ),
      },

      {
        path: PATHS.INVENTORY.STOCK_ADJUSTMENT_NEW,
        element: (
          <ProtectedRoute
            permission={
              ROUTE_PERMISSION_REQUIREMENTS[
                PATHS.INVENTORY.STOCK_ADJUSTMENT_NEW
              ].permission
            }
          >
            <CreateStockAdjustmentPage />
          </ProtectedRoute>
        ),
      },

      {
        path: PATHS.INVENTORY.STOCK_ADJUSTMENT,
        element: (
          <ProtectedRoute
            permission={
              ROUTE_PERMISSION_REQUIREMENTS[
                PATHS.INVENTORY.STOCK_ADJUSTMENT
              ].permission
            }
          >
            <StockAdjustmentDetailPage />
          </ProtectedRoute>
        ),
      },

      /*
       * Sales
       */

      {
        path: PATHS.SALES.ROOT,
        element: <div>Sales Module (Coming Soon)</div>,
      },

      {
        path: PATHS.SALES.HISTORY,
        element: (
          <ProtectedRoute
            permission={
              ROUTE_PERMISSION_REQUIREMENTS[
                PATHS.SALES.HISTORY
              ].permission
            }
          >
            <SalesHistoryPage />
          </ProtectedRoute>
        ),
      },

      {
        path: PATHS.SALES.POS,
        element: (
          <ProtectedRoute
            permission={
              ROUTE_PERMISSION_REQUIREMENTS[
                PATHS.SALES.POS
              ].permission
            }
          >
            <PosPage />
          </ProtectedRoute>
        ),
      },

      {
        path: PATHS.SALES.RETURNS,
        element: (
          <ProtectedRoute
            permission={
              ROUTE_PERMISSION_REQUIREMENTS[
                PATHS.SALES.RETURNS
              ].permission
            }
          >
            <RefundsPage />
          </ProtectedRoute>
        ),
      },

      {
        path: PATHS.SALES.RECEIPT,
        element: (
          <ProtectedRoute
            permission={
              ROUTE_PERMISSION_REQUIREMENTS[
                PATHS.SALES.RECEIPT
              ].permission
            }
          >
            <SaleReceiptPage />
          </ProtectedRoute>
        ),
      },

      /*
       * Procurement
       */

      {
        path: PATHS.PROCUREMENT.ROOT,
        element: <div>Procurement Module (Coming Soon)</div>,
      },

      {
        path: PATHS.PROCUREMENT.SUPPLIERS,
        element: (
          <ProtectedRoute
            permission={
              ROUTE_PERMISSION_REQUIREMENTS[
                PATHS.PROCUREMENT.SUPPLIERS
              ].permission
            }
          >
            <SuppliersPage />
          </ProtectedRoute>
        ),
      },

      /*
       * Finance
       */

      {
        path: PATHS.FINANCE.ROOT,
        element: <div>Finance Module (Coming Soon)</div>,
      },

      /*
       * Reports
       */

      {
        path: PATHS.REPORTS.ROOT,
        element: <div>Reports Module (Coming Soon)</div>,
      },

      /*
       * Administration
       */

      {
        path: PATHS.ADMINISTRATION.ROOT,
        element: <div>Administration Module (Coming Soon)</div>,
      },

      /*
       * Settings
       */

      {
        path: PATHS.SETTINGS.ROOT,
        element: <div>Settings Module (Coming Soon)</div>,
      },
    ],
  },

  /**
   * Hela360 Office
   *
   * Platform-management application boundary.
   *
   * Authentication infrastructure is shared with the tenant ERP, while
   * application layout, navigation and admission remain separate.
   */
  {
    element: (
      <ShellProvider>
        <ApplicationProvider>
          <OfficeProtectedRoute>
            <OfficeAppLayout />
          </OfficeProtectedRoute>
        </ApplicationProvider>
      </ShellProvider>
    ),

    children: [
      {
        path: OFFICE_PATHS.ROOT,
        element: (
          <Navigate
            to={OFFICE_PATHS.DASHBOARD}
            replace
          />
        ),
      },
      {
        path: OFFICE_PATHS.DASHBOARD,
        element: <OfficeDashboardPage />,
      },
      {
        path: OFFICE_PATHS.CATALOGUE.ROOT,
        element: (
          <Navigate
            to={OFFICE_PATHS.CATALOGUE.MASTER_ITEMS}
            replace
          />
        ),
      },
      {
        path: OFFICE_PATHS.CATALOGUE.MASTER_ITEMS,
        element: <MasterItemsPage />,
      },
      {
        path: OFFICE_PATHS.CATALOGUE.MASTER_ITEM_DETAIL,
        element: <MasterItemDetailPage />,
      },
      {
        path: OFFICE_PATHS.CATALOGUE.REVIEW_QUEUE,
        element: <ReviewQueuePage />,
      },
      {
        path: OFFICE_PATHS.CATALOGUE.CATEGORIES,
        element: <CategoriesPage />,
      },
      {
        path: OFFICE_PATHS.CATALOGUE.BRANDS,
        element: <BrandsPage />,
      },
      {
        path: OFFICE_PATHS.CATALOGUE.DATA_QUALITY,
        element: <DataQualityPage />,
      },
      {
        path:
          OFFICE_PATHS
            .SUPPLIER_INTELLIGENCE
            .ROOT,
        element: (
          <Navigate
            to={
              OFFICE_PATHS
                .SUPPLIER_INTELLIGENCE
                .CATALOGUE_SUPPLIERS
            }
            replace
          />
        ),
      },
      {
        path:
          OFFICE_PATHS
            .SUPPLIER_INTELLIGENCE
            .CATALOGUE_SUPPLIERS,
        element: <CatalogueSuppliersPage />,
      },
      {
        path:
          OFFICE_PATHS
            .SUPPLIER_INTELLIGENCE
            .CATALOGUE_SUPPLIER_DETAIL,
        element: <CatalogueSupplierDetailPage />,
      },
    ],
  },

  /**
   * Catch-all
   */
  {
    path: "*",
    element: (
      <Navigate
        to={PATHS.DASHBOARD}
        replace
      />
    ),
  },
]);
