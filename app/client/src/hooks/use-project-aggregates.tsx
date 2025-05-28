import { AggregateMetrics, TimeFrame } from "@/types/types";
import { aggregatesByProjectQueryOptions } from "@/utils/spans";
import { useSuspenseQuery } from "@tanstack/react-query";
import { useCallback, useMemo } from "react";

export interface ProcessedData extends AggregateMetrics {
  date: string;
  formattedCost: string;
  total_tokens: number;
  average_duration_sec: string;
  average_duration_ms: number;
  uuid: string;
}

type ConsolidatedRecord = Record<string, Record<string, ProcessedData>>;

type FunctionAggregates = Record<string, ProcessedData>;

export const useProjectAggregates = (projectUuid: string, timeFrame: TimeFrame) => {
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

  const consolidatedData: ConsolidatedRecord = useMemo(() => {
    const consolidated: ConsolidatedRecord = {};

    processedData.forEach((item) => {
      if (!consolidated[item.date]) {
        consolidated[item.date] = {};
      }

      const functionKey = item.function_uuid ?? item.uuid;

      if (!consolidated[item.date][functionKey]) {
        consolidated[item.date][functionKey] = { ...item };
      } else {
        const existing = consolidated[item.date][functionKey];
        existing.total_cost += item.total_cost;
        existing.total_input_tokens += item.total_input_tokens;
        existing.total_output_tokens += item.total_output_tokens;
        existing.span_count += item.span_count;
        existing.total_tokens = existing.total_input_tokens + existing.total_output_tokens;
        existing.formattedCost = `${existing.total_cost.toFixed(5)}`;
      }
    });

    return consolidated;
  }, [processedData]);

  const functionAggregates: FunctionAggregates = useMemo(() => {
    const aggregates: FunctionAggregates = {};

    processedData.forEach((item) => {
      const functionKey = item.function_uuid ?? item.uuid;
      aggregates[functionKey] = item;
    });

    return aggregates;
  }, [processedData]);

  const getTotalCost = useCallback(() => {
    return processedData.reduce((sum, item) => sum + item.total_cost, 0);
  }, [processedData]);

  const getTotalTokens = useCallback(() => {
    return processedData.reduce((sum, item) => sum + item.total_tokens, 0);
  }, [processedData]);

  return {
    data: processedData,
    consolidatedData,
    functionAggregates,
    rawData: data,
    isLoading,
    error,
    refetch,
    getTotalCost,
    getTotalTokens,
  };
};
