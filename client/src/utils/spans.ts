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

export const fetchSpansByVersionUuid = async (
  projectUuid: string,
  versionUuid: string
) => {
  return (
    await api.get<SpanPublic[]>(
      `/projects/${projectUuid}/versions/${versionUuid}/spans`
    )
  ).data;
};

export const versionUuidSpansQueryOptions = (
  projectUuid: string,
  versionUuid: string
) =>
  queryOptions({
    queryKey: ["projects", projectUuid, "versions", versionUuid, "spans"],
    queryFn: () => fetchSpansByVersionUuid(projectUuid, versionUuid),
    refetchInterval: 1000,
  });
