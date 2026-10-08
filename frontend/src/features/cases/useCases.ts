import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api, unwrap, type CaseItemKind } from "../../api/client";

export function useCases() {
  return useQuery({
    queryKey: ["cases"],
    queryFn: async () => unwrap(await api.GET("/api/v1/cases")),
  });
}

export function useCase(caseId: string | undefined) {
  return useQuery({
    queryKey: ["case", caseId],
    enabled: Boolean(caseId),
    queryFn: async () =>
      unwrap(
        await api.GET("/api/v1/cases/{case_id}", { params: { path: { case_id: caseId ?? "" } } }),
      ),
  });
}

/** Mutaciones de casos: refrescan la lista y el caso afectado. */
export function useCaseMutations() {
  const client = useQueryClient();
  const refresh = async (caseId: string) => {
    await client.invalidateQueries({ queryKey: ["cases"] });
    await client.invalidateQueries({ queryKey: ["case", caseId] });
  };

  const createCase = useMutation({
    mutationFn: async (title: string) =>
      unwrap(await api.POST("/api/v1/cases", { body: { title } })),
    onSuccess: (created) => refresh(created.id),
  });

  const saveItem = useMutation({
    mutationFn: async (input: { caseId: string; kind: CaseItemKind; reference: string }) =>
      unwrap(
        await api.POST("/api/v1/cases/{case_id}/items", {
          params: { path: { case_id: input.caseId } },
          body: { kind: input.kind, reference: input.reference },
        }),
      ),
    onSuccess: (updated) => refresh(updated.id),
  });

  const addNote = useMutation({
    mutationFn: async (input: { caseId: string; body: string }) =>
      unwrap(
        await api.POST("/api/v1/cases/{case_id}/notes", {
          params: { path: { case_id: input.caseId } },
          body: { body: input.body },
        }),
      ),
    onSuccess: (updated) => refresh(updated.id),
  });

  return { createCase, saveItem, addNote };
}
