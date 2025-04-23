import api from "@/api";
import {
  AggregateMetrics,
  PaginatedSpanPublic,
  SpanMoreDetails,
  SpanPublic,
  SpanUpdate,
  TimeFrame,
} from "@/types/types";
import {
  queryOptions,
  useMutation,
  useQueryClient,
} from "@tanstack/react-query";

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

export const patchSpan = async (spanUuid: string, spanUpdate: SpanUpdate) => {
  return (await api.patch<SpanPublic>(`/spans/${spanUuid}`, spanUpdate)).data;
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

export const useUpdateSpanMutation = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      spanUuid,
      spanUpdate,
    }: {
      spanUuid: string;
      spanUpdate: SpanUpdate;
    }) => await patchSpan(spanUuid, spanUpdate),
    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: ["spans"],
      });
    },
  });
};

export interface PageParam {
  offset: number;
  limit: number;
}

export const fetchSpansByFunctionUuidPaged = async (
  projectUuid: string,
  functionUuid: string,
  { offset, limit }: PageParam,
) => (
  await api.get<PaginatedSpanPublic>(
    `/projects/${projectUuid}/functions/${functionUuid}/spans/paginated` +
    `?limit=${limit}&offset=${offset}`,
  )
).data

