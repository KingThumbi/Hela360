export const OFFICE_NAVIGATION_SECTION_IDS = {
  PRIMARY: "office-primary",
  CATALOGUE: "office-catalogue",
} as const;

export type OfficeNavigationSectionId =
  (typeof OFFICE_NAVIGATION_SECTION_IDS)[keyof typeof OFFICE_NAVIGATION_SECTION_IDS];

export const OFFICE_NAVIGATION_ITEM_IDS = {
  DASHBOARD: "office-dashboard",

  CATALOGUE_MASTER_ITEMS: "office-catalogue-master-items",
  CATALOGUE_REVIEW_QUEUE: "office-catalogue-review-queue",
  CATALOGUE_CATEGORIES: "office-catalogue-categories",
  CATALOGUE_BRANDS: "office-catalogue-brands",
  CATALOGUE_DATA_QUALITY: "office-catalogue-data-quality",
} as const;

export type OfficeNavigationItemId =
  (typeof OFFICE_NAVIGATION_ITEM_IDS)[keyof typeof OFFICE_NAVIGATION_ITEM_IDS];
