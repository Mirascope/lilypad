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

export const tracesInfiniteQueryOptions = (projectUuid: string) => ({
  queryKey: ["projects", projectUuid, "traces"],
  queryFn: ({ pageParam }: QueryFunctionContext) => {
    const { offset = 0, limit = PAGE_SIZE } = pageParam as TracePageParam;
    return fetchTraces(projectUuid, offset, limit);
  },
  getNextPageParam: (
    lastPage: PaginatedSpanPublic,
    _allPages: PaginatedSpanPublic[],
    lastPageParam: TracePageParam
  ) => {
    const nextOffset = lastPageParam.offset + lastPage.items.length;
    if (nextOffset >= lastPage.total) return undefined;
    return { offset: nextOffset, limit: lastPageParam.limit };
  },
  
  initialPageParam: { offset: 0, limit: PAGE_SIZE },
  staleTime: 30_000,
});