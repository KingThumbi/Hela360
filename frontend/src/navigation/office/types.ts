import type { LucideIcon } from "lucide-react";

import type {
  OfficeNavigationItemId,
  OfficeNavigationSectionId,
} from "./ids";

export interface OfficeNavigationItem {
  id: OfficeNavigationItemId;
  title: string;
  href: string;
  icon: LucideIcon;
}

export interface OfficeNavigationSection {
  id: OfficeNavigationSectionId;
  title: string;
  items: OfficeNavigationItem[];
}
