import api from "@/api";
import { PaginatedSpanPublic } from "@/types/types";
import type { QueryFunctionContext } from "@tanstack/react-query";
import { PAGE_SIZE } from "@/utils/constants.ts";

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
  const { data } = await api.get<PaginatedSpanPublic>(
    `/projects/${projectUuid}/traces?${params}`,
  );
  return data;
};

export interface TracePageParam {
  offset: number;
  limit: number;
}

export const tracesInfiniteQueryOptions = <Key extends readonly unknown[] >(
  projectUuid: string,
  pageSize: number,
  order: "asc" | "desc" = "desc",
  queryKey: Key,
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