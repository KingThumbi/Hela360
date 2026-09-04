import {
  useQuery,
} from "@tanstack/react-query";

import {
  QUERY_KEYS,
} from "@/lib/queryKeys";

import {
  officeCatalogueBrandService,
} from "@/services/office";


export function useOfficeCatalogueBrands() {
  return useQuery({
    queryKey:
      QUERY_KEYS.office.brands.root(),

    queryFn: () =>
      officeCatalogueBrandService.getSummary(),
  });
}


export default useOfficeCatalogueBrands;
