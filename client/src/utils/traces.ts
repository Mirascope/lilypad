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

export const tracesInfiniteQueryOptions = (projectUuid: string) => ({
  queryKey: ["projects", projectUuid, "traces"],
  queryFn: ({ pageParam = 0 }: QueryFunctionContext) =>
    fetchTraces(projectUuid, pageParam as number, PAGE_SIZE),

  getNextPageParam: (
    lastPage: PaginatedSpanPublic,
    _allPages: PaginatedSpanPublic[],
    lastOffset: number
  ) => {
    const nextOffset = lastOffset + lastPage.items.length;
    return nextOffset < lastPage.total ? nextOffset : undefined;
  },

  initialPageParam: 0,
  staleTime: 30_000,
});
