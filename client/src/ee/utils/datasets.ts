import api from "@/api";
import { AnnotationPublic, DatasetRowsResponse } from "@/ee/types/types";
import {
  queryOptions,
  useMutation,
  useQueryClient,
} from "@tanstack/react-query";
import { usePostHog } from "posthog-js/react";

export const uploadDataset = async (
  projectUuid: string,
  generationUuid: string,
  annotations: AnnotationPublic[]
) => {
  return (
    await api.post<boolean>(
      `/ee/projects/${projectUuid}/generations/${generationUuid}/datasets`,
      annotations
    )
  ).data;
};

export const fetchDatasetByGenerationUuid = async (
  projectUuid: string,
  generationUuid: string
) => {
  return (
    await api.get<DatasetRowsResponse>(
      `/ee/projects/${projectUuid}/generations/${generationUuid}/datasets`
    )
  ).data;
};

export const getDatasetByGenerationUuidQueryOptions = (
  projectUuid: string,
  generationUuid: string
) =>
  queryOptions({
    queryKey: ["datasets", "generations", generationUuid],
    queryFn: () => fetchDatasetByGenerationUuid(projectUuid, generationUuid),
  });

export const useUploadDatasetMutation = () => {
  const queryClient = useQueryClient();
  const posthog = usePostHog();
  return useMutation({
    mutationFn: async ({
      projectUuid,
      generationUuid,
      annotations,
    }: {
      projectUuid: string;
      generationUuid: string;
      annotations: AnnotationPublic[];
    }) => await uploadDataset(projectUuid, generationUuid, annotations),
    onSuccess: async (_, { generationUuid }) => {
      posthog.capture("datasetUploaded");
      await queryClient.invalidateQueries({
        queryKey: [
          ["annotations"],
          ["datasets", "generations", generationUuid],
        ],
      });
    },
  });
};
