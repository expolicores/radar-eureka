import { useQuery } from "@tanstack/react-query";

import { ApiError, api, unwrap } from "../../api/client";

export function usePurchase(purchaseId: string) {
  return useQuery({
    queryKey: ["purchase", purchaseId],
    queryFn: async () =>
      unwrap(
        await api.GET("/api/v1/purchases/{purchase_id}", {
          params: { path: { purchase_id: purchaseId } },
        }),
      ),
    retry: (count, error) =>
      !(error instanceof ApiError && [400, 404].includes(error.status)) && count < 1,
  });
}
