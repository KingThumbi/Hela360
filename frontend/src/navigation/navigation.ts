import type { NavigationSection } from "@/types/navigation";
import { PATHS } from "@/routes/routes";
import { ROUTE_PERMISSION_REQUIREMENTS } from "@/routes/permissions";
import {
  NAVIGATION_ITEM_IDS,
  NAVIGATION_SECTION_IDS,
} from "./ids";

import {
  Boxes,
  Building2,
  CreditCard,
  FileBarChart2,
  LayoutDashboard,
  Package,
  Receipt,
  Settings,
  Shield,
  ShoppingCart,
  Store,
  Truck,
  Users,
  Warehouse,
} from "lucide-react";

export const navigation: NavigationSection[] = [
  {
    id: NAVIGATION_SECTION_IDS.DASHBOARD,
    title: "",
    items: [
      {
        id: NAVIGATION_ITEM_IDS.DASHBOARD,
        title: "Dashboard",
        href: PATHS.DASHBOARD,
        icon: LayoutDashboard,
      },
    ],
  },

  {
    id: NAVIGATION_SECTION_IDS.SALES,
    title: "Sales",
    items: [
      {
        id: NAVIGATION_ITEM_IDS.POS,
        title: "Point of Sale",
        href: PATHS.SALES.POS,
        icon: ShoppingCart,
        permission:
          ROUTE_PERMISSION_REQUIREMENTS[
            PATHS.SALES.POS
          ].permission,
      },
      {
        id: NAVIGATION_ITEM_IDS.SALES_HISTORY,
        title: "Sales History",
        href: PATHS.SALES.HISTORY,
        icon: Receipt,
        permission:
          ROUTE_PERMISSION_REQUIREMENTS[
            PATHS.SALES.HISTORY
          ].permission,
      },
      {
        id: NAVIGATION_ITEM_IDS.REFUNDS,
        title: "Refunds",
        href: PATHS.SALES.RETURNS,
        icon: CreditCard,
        permission:
          ROUTE_PERMISSION_REQUIREMENTS[
            PATHS.SALES.RETURNS
          ].permission,
      },
    ],
  },

  {
    id: NAVIGATION_SECTION_IDS.INVENTORY,
    title: "Inventory",
    items: [
      {
        id: NAVIGATION_ITEM_IDS.PRODUCTS,
        title: "Products",
        href: PATHS.PRODUCTS.ROOT,
        icon: Package,
        permission:
          ROUTE_PERMISSION_REQUIREMENTS[
            PATHS.PRODUCTS.ROOT
          ].permission,
      },
      {
        id: NAVIGATION_ITEM_IDS.INVENTORY,
        title: "Inventory",
        href: PATHS.INVENTORY.ROOT,
        icon: Boxes,
        permission:
          ROUTE_PERMISSION_REQUIREMENTS[
            PATHS.INVENTORY.ROOT
          ].permission,
      },
      {
        id: NAVIGATION_ITEM_IDS.INVENTORY_WAREHOUSES,
        title: "Warehouses",
        href: PATHS.WAREHOUSES.ROOT,
        icon: Warehouse,
        anyOfPermissions:
          ROUTE_PERMISSION_REQUIREMENTS[
            PATHS.WAREHOUSES.ROOT
          ].anyOf,
      },
    ],
  },

  {
    id: NAVIGATION_SECTION_IDS.CUSTOMERS,
    title: "Customers",
    items: [
      {
        id: NAVIGATION_ITEM_IDS.CUSTOMERS,
        title: "Customers",
        href: PATHS.CUSTOMERS.ROOT,
        icon: Users,
        permission:
          ROUTE_PERMISSION_REQUIREMENTS[
            PATHS.CUSTOMERS.ROOT
          ].permission,
      },
    ],
  },

  {
    id: NAVIGATION_SECTION_IDS.PROCUREMENT,
    title: "Procurement",
    items: [
      {
        id: NAVIGATION_ITEM_IDS.SUPPLIERS,
        title: "Suppliers",
        href: PATHS.PROCUREMENT.SUPPLIERS,
        icon: Truck,
        permission: "suppliers.view",
      },
    ],
  },

  {
    id: NAVIGATION_SECTION_IDS.REPORTS,
    title: "Reports",
    items: [
      {
        id: NAVIGATION_ITEM_IDS.REPORTS,
        title: "Reports",
        href: PATHS.REPORTS.ROOT,
        icon: FileBarChart2,
        permission: "reports.view",
      },
    ],
  },

  {
    id: NAVIGATION_SECTION_IDS.ADMINISTRATION,
    title: "Administration",
    items: [
      {
        id: NAVIGATION_ITEM_IDS.USERS,
        title: "Users",
        href: PATHS.ADMINISTRATION.USERS,
        icon: Users,
        permission: "users.read",
      },
      {
        id: NAVIGATION_ITEM_IDS.ROLES,
        title: "Roles",
        href: PATHS.ADMINISTRATION.ROLES,
        icon: Shield,
        permission: "roles.read",
      },
      {
        id: NAVIGATION_ITEM_IDS.BRANCHES,
        title: "Branches",
        href: PATHS.ADMINISTRATION.BRANCHES,
        icon: Building2,
        permission: "branches.read",
      },
    ],
  },

  {
    id: NAVIGATION_SECTION_IDS.SETTINGS,
    title: "Settings",
    items: [
      {
        id: NAVIGATION_ITEM_IDS.SETTINGS,
        title: "Settings",
        href: PATHS.SETTINGS.ROOT,
        icon: Settings,
        permission: "settings.manage",
      },
      {
        id: NAVIGATION_ITEM_IDS.TENANT,
        title: "Tenant",
        href: PATHS.SETTINGS.TENANT,
        icon: Store,
        permission:
          ROUTE_PERMISSION_REQUIREMENTS[
            PATHS.SETTINGS.TENANT
          ].permission,
      },
    ],
  },
];
