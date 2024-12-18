import api from "@/api";
import { SpanPublic } from "@/types/types";
import { queryOptions } from "@tanstack/react-query";

export const fetchSpan = async (projectUuid: string, spanUuid?: string) => {
  if (!spanUuid) {
    return null;
  }
  return (
    await api.get<SpanPublic>(`/projects/${projectUuid}/spans/${spanUuid}`)
  ).data;
};

export const spanQueryOptions = (projectUuid: string, spanUuid?: string) =>
  queryOptions({
    queryKey: ["projects", projectUuid, "spans", spanUuid],
    queryFn: () => fetchSpan(projectUuid, spanUuid),
    enabled: Boolean(spanUuid),
    retry: false,
  });

export const fetchSpansByGenerationUuid = async (
  projectUuid: string,
  generationUuid: string
) => {
  return (
    await api.get<SpanPublic[]>(
      `/projects/${projectUuid}/generations/${generationUuid}/spans`
    )
  ).data;
};

export const spansByGenerationQueryOptions = (
  projectUuid: string,
  generationUuid: string
) =>
  queryOptions({
    queryKey: ["projects", projectUuid, "generations", generationUuid, "spans"],
    queryFn: () => fetchSpansByGenerationUuid(projectUuid, generationUuid),
    refetchInterval: 1000,
  });
