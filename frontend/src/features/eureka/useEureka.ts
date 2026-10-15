import { useQuery } from "@tanstack/react-query";
import { api, unwrap } from "../../api/client";

export interface EurekaFilters {
  page: number;
  page_size: number;
  priority?: "high" | "medium" | "low";
  department?: string;
  category?: string;
  review_required?: boolean;
}
export function useEureka(filters: EurekaFilters) {
  return useQuery({
    queryKey: ["eureka", filters],
    queryFn: async () =>
      unwrap(await api.GET("/api/eureka/opportunities", { params: { query: filters } })),
  });
}
export function useEurekaDetail(id: string) {
  return useQuery({
    queryKey: ["eureka-detail", id],
    queryFn: async () =>
      unwrap(
        await api.GET("/api/eureka/opportunities/{opportunity_id}", {
          params: { path: { opportunity_id: id } },
        }),
      ),
  });
}
export function useEurekaEvidence(id: string, canonicalId: string, enabled: boolean) {
  return useQuery({
    queryKey: ["eureka-evidence", id, canonicalId],
    enabled,
    queryFn: async () =>
      unwrap(
        await api.GET("/api/eureka/opportunities/{opportunity_id}/evidence", {
          params: { path: { opportunity_id: id }, query: { canonical_fact_id: canonicalId } },
        }),
      ),
  });
}

export function useEurekaAlerts(page: number, alertId?: string) {
  return useQuery({
    queryKey: ["eureka-alerts", page, alertId],
    queryFn: async () => {
      if (alertId) {
        const alert = unwrap(
          await api.GET("/api/eureka/alerts/{alert_id}", {
            params: { path: { alert_id: alertId } },
          }),
        );
        return { items: [alert], total: 1, page: 1, page_size: 25 };
      }
      return unwrap(
        await api.GET("/api/eureka/alerts", { params: { query: { page, page_size: 25 } } }),
      );
    },
  });
}

export function useRadarRuns() {
  return useQuery({
    queryKey: ["eureka-radar-runs"],
    queryFn: async () =>
      unwrap(
        await api.GET("/api/eureka/radar-runs", { params: { query: { page: 1, page_size: 5 } } }),
      ),
  });
}
