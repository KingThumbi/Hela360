import {
  useQuery,
} from "@tanstack/react-query";

import {
  QUERY_KEYS,
} from "@/lib/queryKeys";

import {
  officeCatalogueCategoryService,
} from "@/services/office";


export function useOfficeCatalogueCategories() {
  return useQuery({
    queryKey:
      QUERY_KEYS.office.categories.root(),

    queryFn: () =>
      officeCatalogueCategoryService.getSummary(),
  });
}


export default useOfficeCatalogueCategories;
