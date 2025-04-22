import { spansSearchQueryOptions } from "@/utils/spans";
import { useQuery } from "@tanstack/react-query";
import { useCallback, useState } from "react";

export interface SearchParams {
  query_string: string;
  time_range_start?: number;
  time_range_end?: number;
  limit?: number;
  scope?: string;
  type?: string;
}
export const useSearch = (projectUuid: string) => {
  // State for search parameters
  const [searchParams, setSearchParams] = useState<SearchParams>({
    query_string: "",
    limit: 100,
  });

  const queryResult = useQuery(
    spansSearchQueryOptions(projectUuid, searchParams)
  );

  // Helper functions
  const search = useCallback((query: string) => {
    setSearchParams((prev) => ({ ...prev, query_string: query }));
  }, []);

  const updateFilters = useCallback((filters: Partial<SearchParams>) => {
    setSearchParams((prev) => ({ ...prev, ...filters }));
  }, []);

  const resetSearch = useCallback(() => {
    setSearchParams({
      query_string: "",
      limit: 100,
    });
  }, []);

  const loadMore = useCallback(() => {
    setSearchParams((prev) => ({
      ...prev,
      limit: (prev.limit ?? 100) + 100,
    }));
  }, []);

  return {
    // Query state
    spans: queryResult.data ?? null,
    isLoading: queryResult.isLoading,
    isError: queryResult.isError,
    error: queryResult.error,

    // Current search state
    searchParams,

    // Actions
    search,
    updateFilters,
    resetSearch,
    loadMore,
  };
};
