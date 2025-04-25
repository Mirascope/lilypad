import { useInfiniteQuery, InfiniteData } from "@tanstack/react-query";
import {
  tracesInfiniteQueryOptions,
  type TracePageParam,
} from "@/utils/traces";
import { PaginatedSpanPublic } from "@/types/types";
import { useMemo } from "react";

export const useInfiniteTraces = (projectUuid: string, pageSize: number, order: "asc" | "desc" = "desc",) => {
  const queryKey = ["projects", projectUuid, "traces", { order, pageSize }] as const;
  const query = useInfiniteQuery<
    PaginatedSpanPublic,
    Error,
    InfiniteData<PaginatedSpanPublic, TracePageParam>,
    typeof queryKey,
    TracePageParam
  >(tracesInfiniteQueryOptions(projectUuid, pageSize, order, queryKey));
  
  const defaultData = useMemo(
    () => query.data?.pages.flatMap((p) => p.items) ?? [],
    [query.data?.pages],
  );
  
  return { ...query, defaultData };
};
