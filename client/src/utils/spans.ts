import api from "@/api";
import { SpanPublic } from "@/types/types";
import { queryOptions } from "@tanstack/react-query";

export const fetchSpan = async (projectId: number, spanId?: string) => {
  if (!spanId) {
    return null;
  }
  return (await api.get<SpanPublic>(`/projects/${projectId}/spans/${spanId}`))
    .data;
};

export const spanQueryOptions = (projectId: number, spanId?: string) =>
  queryOptions({
    queryKey: ["projects", projectId, "spans", spanId],
    queryFn: () => fetchSpan(projectId, spanId),
    enabled: Boolean(spanId),
    retry: false,
  });
