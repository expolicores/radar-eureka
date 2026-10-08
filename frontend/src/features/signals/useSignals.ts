import { keepPreviousData, useQuery } from "@tanstack/react-query";

import { api, unwrap, type SignalQuery } from "../../api/client";

export function useSignals(query: SignalQuery) {
  return useQuery({
    queryKey: ["signals", query],
    queryFn: async () => unwrap(await api.GET("/api/v1/signals", { params: { query } })),
    placeholderData: keepPreviousData,
  });
}

export function useSignalSummary() {
  return useQuery({
    queryKey: ["signal-summary"],
    queryFn: async () => unwrap(await api.GET("/api/v1/signals/summary")),
  });
}
