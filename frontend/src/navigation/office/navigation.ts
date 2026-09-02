import {
  Boxes,
  LayoutDashboard,
  ListChecks,
  Shapes,
  ShieldCheck,
  Tags,
} from "lucide-react";

import { OFFICE_PATHS } from "@/routes/officeRoutes";

import {
  OFFICE_NAVIGATION_ITEM_IDS,
  OFFICE_NAVIGATION_SECTION_IDS,
} from "./ids";

import type { OfficeNavigationSection } from "./types";

export const officeNavigation: OfficeNavigationSection[] = [
  {
    id: OFFICE_NAVIGATION_SECTION_IDS.PRIMARY,
    title: "",
    items: [
      {
        id: OFFICE_NAVIGATION_ITEM_IDS.DASHBOARD,
        title: "Dashboard",
        href: OFFICE_PATHS.DASHBOARD,
        icon: LayoutDashboard,
      },
    ],
  },
  {
    id: OFFICE_NAVIGATION_SECTION_IDS.CATALOGUE,
    title: "Catalogue",
    items: [
      {
        id: OFFICE_NAVIGATION_ITEM_IDS.CATALOGUE_MASTER_ITEMS,
        title: "Master Items",
        href: OFFICE_PATHS.CATALOGUE.MASTER_ITEMS,
        icon: Boxes,
      },
      {
        id: OFFICE_NAVIGATION_ITEM_IDS.CATALOGUE_REVIEW_QUEUE,
        title: "Review Queue",
        href: OFFICE_PATHS.CATALOGUE.REVIEW_QUEUE,
        icon: ListChecks,
      },
      {
        id: OFFICE_NAVIGATION_ITEM_IDS.CATALOGUE_CATEGORIES,
        title: "Categories",
        href: OFFICE_PATHS.CATALOGUE.CATEGORIES,
        icon: Shapes,
      },
      {
        id: OFFICE_NAVIGATION_ITEM_IDS.CATALOGUE_BRANDS,
        title: "Brands",
        href: OFFICE_PATHS.CATALOGUE.BRANDS,
        icon: Tags,
      },
      {
        id: OFFICE_NAVIGATION_ITEM_IDS.CATALOGUE_DATA_QUALITY,
        title: "Data Quality",
        href: OFFICE_PATHS.CATALOGUE.DATA_QUALITY,
        icon: ShieldCheck,
      },
    ],
  },
];
