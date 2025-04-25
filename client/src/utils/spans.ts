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

export const fetchSpans = async (projectUuid: string) => {
  return (await api.get<SpanPublic[]>(`/projects/${projectUuid}/traces`)).data;
};

export const spansQueryOptions = (projectUuid: string) =>
  queryOptions({
    queryKey: ["projects", projectUuid, "spans"],
    queryFn: () => fetchSpans(projectUuid),
    refetchInterval: 10000,
  });

export const fetchSpan = async (spanUuid: string) => {
  return (await api.get<SpanMoreDetails>(`/spans/${spanUuid}`)).data;
};

export const deleteSpan = async (projectUuid: string, spanUuid: string) => {
  return (
    await api.delete<boolean>(`/projects/${projectUuid}/spans/${spanUuid}`)
  ).data;
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

export const searchSpans = async (
  projectUuid: string,
  params: {
    query_string: string;
    time_range_start?: number;
    time_range_end?: number;
    limit?: number;
    scope?: string; // Assuming Scope is a string enum
    type?: string;
  }
) => {
  // Convert params object into URL search params
  const searchParams = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined) {
      searchParams.append(key, value.toString());
    }
  });

  return (
    await api.get<SpanPublic[]>(
      `/projects/${projectUuid}/spans?${searchParams.toString()}`
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
    refetchInterval: 10000,
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
    onSuccess: async (data, { spanUuid }) => {
      queryClient.setQueryData(
        ["spans", spanUuid],
        (oldData: SpanMoreDetails | undefined) => {
          if (!oldData) return oldData;
          return { ...oldData, ...data };
        }
      );

      await queryClient.invalidateQueries({
        queryKey: ["spans", spanUuid],
      });

      await queryClient.invalidateQueries({
        queryKey: ["projects"],
        predicate: (query) => {
          const queryKey = query.queryKey as string[];
          return queryKey.includes("spans") && !queryKey.includes("metadata");
        },
      });
    },
  });
};

export const useDeleteSpanMutation = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      projectUuid,
      spanUuid,
    }: {
      projectUuid: string;
      spanUuid: string;
    }) => await deleteSpan(projectUuid, spanUuid),
    onSuccess: async (_, { projectUuid, spanUuid }) => {
      queryClient.removeQueries({
        queryKey: ["spans", spanUuid],
      });

      queryClient.setQueriesData<SpanPublic[]>(
        { queryKey: ["projects", projectUuid, "spans"] },
        (oldData) => {
          if (!oldData) return oldData;
          return oldData.filter((span) => span.uuid !== spanUuid);
        }
      );

      queryClient.setQueriesData<SpanPublic[]>(
        { queryKey: ["projects", projectUuid, "functions"] },
        (oldData) => {
          if (!oldData) return oldData;
          return oldData.filter((span) => span.uuid !== spanUuid);
        }
      );

      await queryClient.invalidateQueries({
        queryKey: ["projects"],
        predicate: (query) => {
          const queryKey = query.queryKey as string[];
          return queryKey.includes("spans") && !queryKey.includes("metadata");
        },
      });
    },
  });
};

export const spansSearchQueryOptions = (
  projectUuid: string,
  params: {
    query_string: string;
    time_range_start?: number;
    time_range_end?: number;
    limit?: number;
    scope?: string;
    type?: string;
  }
) =>
  queryOptions({
    queryKey: ["projects", projectUuid, "spans", params],
    queryFn: () => searchSpans(projectUuid, params),
    enabled: !!params.query_string,
  });

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

