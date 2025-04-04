import api from "@/api";
import {
  AnnotationCreate,
  AnnotationPublic,
  AnnotationUpdate,
} from "@/types/types";

import {
  queryOptions,
  useMutation,
  useQueryClient,
} from "@tanstack/react-query";
import { usePostHog } from "posthog-js/react";

export const updateAnnotation = async (
  projectUuid: string,
  annotationUuid: string,
  annotationUpdate: AnnotationUpdate
) => {
  return (
    await api.patch<AnnotationPublic>(
      `/ee/projects/${projectUuid}/annotations/${annotationUuid}`,
      annotationUpdate
    )
  ).data;
};

export const fetchAnnotationsByFunctionUuid = async (
  projectUuid: string,
  functionUuid: string
) => {
  return (
    await api.get<AnnotationPublic[]>(
      `/ee/projects/${projectUuid}/functions/${functionUuid}/annotations`
    )
  ).data;
};

export const postAnnotations = async (
  projectUuid: string,
  annotationsCreate: AnnotationCreate[]
) => {
  return (
    await api.post<AnnotationPublic>(
      `/ee/projects/${projectUuid}/annotations`,
      annotationsCreate
    )
  ).data;
};

export const useUpdateAnnotationMutation = () => {
  const queryClient = useQueryClient();
  const posthog = usePostHog();
  return useMutation({
    mutationFn: async ({
      projectUuid,
      annotationUuid,
      annotationUpdate,
    }: {
      projectUuid: string;
      annotationUuid: string;
      annotationUpdate: AnnotationUpdate;
    }) => await updateAnnotation(projectUuid, annotationUuid, annotationUpdate),
    onSuccess: async (_, { annotationUuid }) => {
      posthog.capture("annotationUpdated");
      await queryClient.invalidateQueries({
        queryKey: ["annotations", annotationUuid],
      });
    },
  });
};

export const useCreateAnnotationsMutation = () => {
  const queryClient = useQueryClient();
  const posthog = usePostHog();
  return useMutation({
    mutationFn: async ({
      projectUuid,
      annotationsCreate,
    }: {
      projectUuid: string;
      annotationsCreate: AnnotationCreate[];
    }) => await postAnnotations(projectUuid, annotationsCreate),
    onSuccess: async () => {
      posthog.capture("annotationCreated");
      await queryClient.invalidateQueries({
        queryKey: ["annotations"],
      });
    },
  });
};

export const annotationsByFunctionQueryOptions = (
  projectUuid: string,
  functionUuid: string
) =>
  queryOptions({
    queryKey: [
      "projects",
      projectUuid,
      "functions",
      functionUuid,
      "annotations",
    ],
    queryFn: () => fetchAnnotationsByFunctionUuid(projectUuid, functionUuid),
    refetchInterval: 1000,
  });
