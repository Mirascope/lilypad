import api from "@/src/api";
import {
  AnnotationCreate,
  AnnotationMetrics,
  AnnotationPublic,
  AnnotationUpdate,
} from "@/src/types/types";

import { queryOptions, useMutation, useQueryClient } from "@tanstack/react-query";
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

export const deleteAnnotation = async (projectUuid: string, annotationUuid: string) => {
  return (
    await api.delete<AnnotationPublic>(`/ee/projects/${projectUuid}/annotations/${annotationUuid}`)
  ).data;
};

export const fetchAnnotationsByFunctionUuid = async (projectUuid: string, functionUuid: string) => {
  return (
    await api.get<AnnotationPublic[]>(
      `/ee/projects/${projectUuid}/functions/${functionUuid}/annotations`
    )
  ).data;
};

export const fetchAnnotationsBySpanUuid = async (
  projectUuid: string,
  spanUuid: string,
  enabled = true
) => {
  if (!enabled) return [];
  return (
    await api.get<AnnotationPublic[]>(`/ee/projects/${projectUuid}/spans/${spanUuid}/annotations`)
  ).data;
};

export const fetchAnnotationsByProjectUuid = async (projectUuid?: string) => {
  if (!projectUuid) return [];
  return (await api.get<AnnotationPublic[]>(`/ee/projects/${projectUuid}/annotations`)).data;
};

export const fetchAnnotationMetricsByFunctionUuid = async (
  projectUuid: string,
  functionUuid: string
) => {
  return (
    await api.get<AnnotationMetrics>(
      `/ee/projects/${projectUuid}/functions/${functionUuid}/annotations/metrics`
    )
  ).data;
};

export const postAnnotations = async (
  projectUuid: string,
  annotationsCreate: AnnotationCreate[]
) => {
  return (
    await api.post<AnnotationPublic>(`/ee/projects/${projectUuid}/annotations`, annotationsCreate)
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
    onSuccess: async (_, { projectUuid }) => {
      posthog.capture("annotationUpdated");
      await queryClient.invalidateQueries({
        queryKey: ["projects", projectUuid, "annotations"],
      });
      await queryClient.invalidateQueries({
        queryKey: ["projects", projectUuid, "functions"],
        predicate: (query) => query.queryKey.includes("annotations"),
      });
    },
  });
};

export const useDeleteAnnotationMutation = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      projectUuid,
      annotationUuid,
    }: {
      projectUuid: string;
      annotationUuid: string;
    }) => await deleteAnnotation(projectUuid, annotationUuid),
    onSuccess: async (_, { projectUuid }) => {
      await queryClient.invalidateQueries({
        queryKey: ["projects", projectUuid, "annotations"],
      });
      await queryClient.invalidateQueries({
        queryKey: ["projects", projectUuid, "functions"],
        predicate: (query) => query.queryKey.includes("annotations"),
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

export const annotationsByFunctionQueryOptions = (projectUuid: string, functionUuid: string) =>
  queryOptions({
    queryKey: ["projects", projectUuid, "functions", functionUuid, "annotations"],
    queryFn: () => fetchAnnotationsByFunctionUuid(projectUuid, functionUuid),
    refetchInterval: 1000,
  });

export const annotationsBySpanQueryOptions = (
  projectUuid: string,
  spanUuid: string,
  enabled = true
) =>
  queryOptions({
    queryKey: ["projects", projectUuid, "spans", spanUuid, "annotations"],
    queryFn: () => fetchAnnotationsBySpanUuid(projectUuid, spanUuid, enabled),
    enabled,
  });

export const annotationsByProjectQueryOptions = (projectUuid?: string) =>
  queryOptions({
    queryKey: ["projects", projectUuid, "annotations"],
    queryFn: () => fetchAnnotationsByProjectUuid(projectUuid),
    refetchInterval: 60000,
  });

export const annotationMetricsByFunctionQueryOptions = (
  projectUuid: string,
  functionUuid: string
) =>
  queryOptions({
    queryKey: ["projects", projectUuid, "functions", functionUuid, "annotations", "metrics"],
    queryFn: () => fetchAnnotationMetricsByFunctionUuid(projectUuid, functionUuid),
  });
