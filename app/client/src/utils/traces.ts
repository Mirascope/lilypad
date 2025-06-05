import api from "@/src/api";
import { PaginatedSpanPublic, SpanPublic } from "@/src/types/types";
import { PAGE_SIZE } from "@/src/utils/constants.ts";
import type { QueryFunctionContext } from "@tanstack/react-query";

export const fetchTraces = async (
  projectUuid: string,
  offset: number,
  limit: number = PAGE_SIZE,
  order: "desc" | "asc" = "desc"
) => {
  const params = new URLSearchParams({
    limit: String(limit),
    offset: String(offset),
    order: order,
  });
  const { data } = await api.get<PaginatedSpanPublic>(`/projects/${projectUuid}/traces?${params}`);
  return data;
};

export const fetchRootTrace = async (projectUuid: string, spanUuid: string) => {
  const { data } = await api.get<SpanPublic>(`/projects/${projectUuid}/traces/${spanUuid}/root`);
  return data;
};

export interface TracePageParam {
  offset: number;
  limit: number;
}

export const tracesInfiniteQueryOptions = <Key extends readonly unknown[]>(
  projectUuid: string,
  pageSize: number,
  order: "asc" | "desc" = "desc",
  queryKey: Key
) => ({
  queryKey,
  queryFn: ({ pageParam }: QueryFunctionContext) => {
    const { offset = 0, limit = pageSize } = pageParam as TracePageParam;
    return fetchTraces(projectUuid, offset, limit, order);
  },

  getNextPageParam: (
    lastPage: PaginatedSpanPublic,
    _pages: PaginatedSpanPublic[],
    lastParams: TracePageParam
  ) => {
    const nextOffset = lastParams.offset + lastPage.items.length;
    return nextOffset < lastPage.total
      ? { offset: nextOffset, limit: lastParams.limit }
      : undefined;
  },

  initialPageParam: { offset: 0, limit: pageSize },
  staleTime: 30_000,
});

export const rootTraceQueryOptions = (projectUuid: string, spanUuid: string) => ({
  queryKey: [`trace`, projectUuid, spanUuid],
  queryFn: () => fetchRootTrace(projectUuid, spanUuid),
  staleTime: 30_000,
});
