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

export const fetchSpansByFunctionUuid = async (
  projectUuid: string,
  functionUuid: string
) => {
  return (
    await api.get<SpanPublic[]>(
      `/projects/${projectUuid}/functions/${functionUuid}/spans`
    )
  ).data;
};

export const fetchAggregatesByProjectUuid = async (
  projectUuid: string,
  timeFrame: TimeFrame
) => {
  return (
    await api.get<AggregateMetrics[]>(
      `/projects/${projectUuid}/spans/metadata?time_frame=${timeFrame}`
    )
  ).data;
};

export const fetchAggregatesByFunctionUuid = async (
  projectUuid: string,
  functionUuid: string,
  timeFrame: TimeFrame
) => {
  return (
    await api.get<AggregateMetrics[]>(
      `/projects/${projectUuid}/functions/${functionUuid}/spans/metadata?time_frame=${timeFrame}`
    )
  ).data;
};

export const spansByFunctionQueryOptions = (
  projectUuid: string,
  functionUuid: string
) =>
  queryOptions({
    queryKey: ["projects", projectUuid, "functions", functionUuid, "spans"],
    queryFn: () => fetchSpansByFunctionUuid(projectUuid, functionUuid),
    refetchInterval: 1000,
  });

export const aggregatesByProjectQueryOptions = (
  projectUuid: string,
  timeFrame: TimeFrame
) =>
  queryOptions({
    queryKey: ["projects", projectUuid, "spans", "metadata", timeFrame],
    queryFn: () => fetchAggregatesByProjectUuid(projectUuid, timeFrame),
  });

export const aggregatesByFunctionQueryOptions = (
  projectUuid: string,
  functionUuid: string,
  timeFrame: TimeFrame
) =>
  queryOptions({
    queryKey: [
      "projects",
      projectUuid,
      "functions",
      functionUuid,
      "spans",
      "metadata",
      timeFrame,
    ],
    queryFn: () =>
      fetchAggregatesByFunctionUuid(projectUuid, functionUuid, timeFrame),
  });
