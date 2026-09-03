import {
  useQuery,
} from "@tanstack/react-query";

import {
  QUERY_KEYS,
} from "@/lib/queryKeys";

import {
  officeCatalogueDataQualityService,
} from "@/services/office";


export function useOfficeCatalogueDataQuality() {
  return useQuery({
    queryKey:
      QUERY_KEYS.office.dataQuality.root(),

    queryFn: () =>
      officeCatalogueDataQualityService.getSummary(),
  });
}


export default useOfficeCatalogueDataQuality;
