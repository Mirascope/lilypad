import api from "@/api";
import {
  AggregateMetrics,
  SpanMoreDetails,
  SpanPublic,
  TimeFrame,
} from "@/types/types";
import { queryOptions } from "@tanstack/react-query";

export const fetchSpan = async (spanUuid: string) => {
  return (await api.get<SpanMoreDetails>(`/spans/${spanUuid}`)).data;
};

export const spanQueryOptions = (spanUuid: string) =>
  queryOptions({
    queryKey: ["spans", spanUuid],
    queryFn: () => fetchSpan(spanUuid),
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

export const fetchAggregatesByGenerationUuid = async (
  projectUuid: string,
  generationUuid: string,
  timeFrame: TimeFrame
) => {
  return (
    await api.get<AggregateMetrics[]>(
      `/projects/${projectUuid}/generations/${generationUuid}/spans/metadata?time_frame=${timeFrame}`
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

export const aggregatesByGenerationQueryOptions = (
  projectUuid: string,
  generationUuid: string,
  timeFrame: TimeFrame
) =>
  queryOptions({
    queryKey: [
      "projects",
      projectUuid,
      "generations",
      generationUuid,
      "spans",
      "metadata",
      timeFrame,
    ],
    queryFn: () =>
      fetchAggregatesByGenerationUuid(projectUuid, generationUuid, timeFrame),
  });
