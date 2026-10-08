import { keepPreviousData, useQuery } from "@tanstack/react-query";

import { api, unwrap, type PurchaseQuery } from "../../api/client";

export function usePurchases(query: PurchaseQuery) {
  return useQuery({
    queryKey: ["purchases", query],
    queryFn: async () => unwrap(await api.GET("/api/v1/purchases", { params: { query } })),
    placeholderData: keepPreviousData,
  });
}

export function usePurchaseFilters() {
  return useQuery({
    queryKey: ["purchase-filters"],
    queryFn: async () => unwrap(await api.GET("/api/v1/purchases/filters")),
    staleTime: 5 * 60_000,
  });
}
