import { useAuth } from "@/src/auth";
import {
  aggregatesByProjectQueryOptions,
  spansQueryOptions,
  spansSearchQueryOptions,
} from "@/src/utils/spans";
import {
  functionsByNameQueryOptions,
  functionsQueryOptions,
  uniqueLatestVersionFunctionNamesQueryOptions,
} from "@/src/utils/functions";
import { annotationsByProjectQueryOptions } from "@/src/ee/utils/annotations";
import { useMemo } from "react";
import { TimeFrame, Scope } from "@/src/types/types";

export const useEnvironmentQueries = () => {
  const { activeEnvironment } = useAuth();

  return useMemo(
    () => ({
      // Spans query options
      spansQueryOptions: (projectUuid?: string) => ({
        ...spansQueryOptions(projectUuid),
        queryKey: ["projects", projectUuid, "spans", activeEnvironment?.uuid],
      }),

      aggregatesByProjectQueryOptions: (projectUuid: string, timeFrame: TimeFrame) => ({
        ...aggregatesByProjectQueryOptions(projectUuid, timeFrame),
        queryKey: [
          "projects",
          projectUuid,
          "spans",
          "metadata",
          timeFrame,
          activeEnvironment?.uuid,
        ],
      }),

      spansSearchQueryOptions: (
        projectUuid: string,
        params: {
          query_string?: string;
          time_range_start?: number;
          time_range_end?: number;
          limit?: number;
          scope?: Scope;
          type?: string;
        }
      ) => ({
        ...spansSearchQueryOptions(projectUuid, params),
        queryKey: ["projects", projectUuid, "spans", params, activeEnvironment?.uuid],
      }),

      // Functions query options
      functionsQueryOptions: (projectUuid: string) => ({
        ...functionsQueryOptions(projectUuid),
        queryKey: ["functions", projectUuid, activeEnvironment?.uuid],
      }),

      uniqueLatestVersionFunctionNamesQueryOptions: (projectUuid?: string) => ({
        ...uniqueLatestVersionFunctionNamesQueryOptions(projectUuid),
        queryKey: ["projects", projectUuid, "functions", "unique", activeEnvironment?.uuid],
      }),

      functionsByNameQueryOptions: (functionName: string, projectUuid: string) => ({
        ...functionsByNameQueryOptions(functionName, projectUuid),
        queryKey: ["functions", "name", functionName, projectUuid, activeEnvironment?.uuid],
      }),

      // Annotations query options
      annotationsByProjectQueryOptions: (projectUuid?: string) => ({
        ...annotationsByProjectQueryOptions(projectUuid),
        queryKey: ["projects", projectUuid, "annotations", activeEnvironment?.uuid],
      }),
    }),
    [activeEnvironment?.uuid]
  );
};
