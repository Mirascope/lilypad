import api from "@/api";
import { PaginatedSpanPublic } from "@/types/types";
import type { QueryFunctionContext } from "@tanstack/react-query";
import { PAGE_SIZE } from "@/utils/constants.ts";

export const fetchTraces = async (
  projectUuid: string,
  offset: number,
  limit: number = PAGE_SIZE,
) => {
  const { data } = await api.get<PaginatedSpanPublic>(
    `/projects/${projectUuid}/traces?limit=${limit}&offset=${offset}`,
  );
  return data;
};

export interface TracePageParam {
  offset: number;
  limit: number;
}

export const tracesInfiniteQueryOptions = (
  projectUuid: string,
  pageSize: number
) => ({
  queryKey: ["projects", projectUuid, "traces", pageSize],
  
  queryFn: ({ pageParam }: QueryFunctionContext) => {
    const { offset = 0, limit = pageSize } = pageParam as TracePageParam;
    return fetchTraces(projectUuid, offset, limit);
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