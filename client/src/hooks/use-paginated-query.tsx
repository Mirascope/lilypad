import { type PaginatedSpanPublic } from "@/types/types";
import { PAGE_SIZE } from "@/utils/constants";
import { fetchSpansByFunctionUuidPaged, type PageParam } from "@/utils/spans";
import { InfiniteData, useInfiniteQuery } from "@tanstack/react-query";
import { useMemo } from "react";

export const usePaginatedSpansByFunction = (
  projectUuid: string,
  order: "asc" | "desc",
  functionUuid?: string,
  { enabled = true }: { enabled?: boolean } = {}
) => {
  const isEnabled = enabled && !!functionUuid;

  const queryKey = [
    "projects",
    projectUuid,
    "functions",
    functionUuid ?? "disabled",
    "spans",
    { order },
  ] as const;

  const query = useInfiniteQuery<
    PaginatedSpanPublic,
    Error,
    InfiniteData<PaginatedSpanPublic, PageParam>,
    typeof queryKey,
    PageParam
  >({
    queryKey,
    enabled: isEnabled,
    initialPageParam: { offset: 0, limit: PAGE_SIZE, order },

    queryFn: async ({ pageParam = { offset: 0, limit: PAGE_SIZE } }) => {
      if (!isEnabled) {
        return Promise.resolve({
          items: [],
          limit: PAGE_SIZE,
          offset: pageParam.offset,
          total: 0,
        });
      }

      const page = await fetchSpansByFunctionUuidPaged(
        projectUuid,
        functionUuid,
        { ...pageParam, order }
      );
      return {
        ...page,
        limit: page.limit ?? pageParam.limit,
        offset: page.offset ?? pageParam.offset,
        items: page.items ?? [],
      };
    },

    getNextPageParam: (lastPage) => {
      if (!isEnabled) return undefined;

      const fetched = lastPage.items?.length ?? 0;
      const nextLimit = lastPage.limit ?? PAGE_SIZE;
      const nextOff = (lastPage.offset ?? 0) + fetched;

      return nextOff >= lastPage.total
        ? undefined
        : ({
            offset: nextOff,
            limit: nextLimit,
            order: order,
          } satisfies PageParam);
    },

    staleTime: 30_000,
  });
  const defaultData = useMemo(
    () => query.data?.pages.flatMap((p) => p.items) ?? [],
    [query.data?.pages]
  );
  return { ...query, defaultData };
};
