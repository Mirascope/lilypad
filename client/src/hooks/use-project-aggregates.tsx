import { AggregateMetrics } from "@/types/types";
import { aggregatesByProjectQueryOptions } from "@/utils/spans";
import { useSuspenseQuery } from "@tanstack/react-query";
import { useCallback, useMemo } from "react";

interface ProcessedData extends AggregateMetrics {
  date: string;
  formattedCost: string;
  total_tokens: number;
  average_duration_sec: string;
  uuid: string;
}

export const useProjectAggregates = (projectUuid: string, timeFrame: any) => {
  // Fetch data using the query
  const { data, isLoading, error, refetch } = useSuspenseQuery(
    aggregatesByProjectQueryOptions(projectUuid, timeFrame)
  );

  // Process data for visualization
  const processedData: ProcessedData[] = useMemo(
    () =>
      data.map((item) => {
        const date = item.start_date ? new Date(item.start_date) : new Date();

        return {
          ...item,
          date: date.toLocaleDateString(),
          formattedCost: `${item.total_cost.toFixed(5)}`,
          total_tokens: item.total_input_tokens + item.total_output_tokens,
          average_duration_sec: (item.average_duration_ms / 1000).toFixed(2),
          uuid: crypto.randomUUID(),
        };
      }),
    [data]
  );

  // Optional: Add helper methods for the data if needed
  const getTotalCost = useCallback(() => {
    return processedData.reduce((sum, item) => sum + item.total_cost, 0);
  }, [processedData]);

  const getTotalTokens = useCallback(() => {
    return processedData.reduce((sum, item) => sum + item.total_tokens, 0);
  }, [processedData]);

  return {
    data: processedData,
    rawData: data,
    isLoading,
    error,
    refetch,
    getTotalCost,
    getTotalTokens,
  };
};
