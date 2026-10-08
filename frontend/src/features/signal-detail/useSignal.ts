import { useQuery } from "@tanstack/react-query";

import { ApiError, api, unwrap } from "../../api/client";

export function useSignal(code: string) {
  return useQuery({
    queryKey: ["signal", code],
    queryFn: async () =>
      unwrap(await api.GET("/api/v1/signals/{code}", { params: { path: { code } } })),
    // Un 404 no se reintenta: la señal no existe o ya no está vigente.
    retry: (count, error) => !(error instanceof ApiError && error.status === 404) && count < 1,
  });
}
