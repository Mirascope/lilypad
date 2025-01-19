import api from "@/api";
import { useAuth } from "@/auth";
import { ProjectCreate, ProjectPublic } from "@/types/types";
import {
  queryOptions,
  useMutation,
  useQueryClient,
} from "@tanstack/react-query";
import { usePostHog } from "posthog-js/react";

export const fetchProjects = async () =>
  (await api.get<ProjectPublic[]>("/projects")).data;

export const fetchProject = async (projectUuid: string) => {
  return (await api.get<ProjectPublic>(`/projects/${projectUuid}`)).data;
};

export const postProject = async (projectCreate: ProjectCreate) => {
  return (await api.post<ProjectPublic>(`/projects`, projectCreate)).data;
};

export const deleteProject = async (projectUuid: string) => {
  return (await api.delete<boolean>(`/projects/${projectUuid}`)).data;
};

export const projectsQueryOptions = () =>
  queryOptions({
    queryKey: ["projects"],
    queryFn: fetchProjects,
  });

export const projectQueryOptions = (projectUuid: string) =>
  queryOptions({
    queryKey: ["projects", projectUuid],
    queryFn: () => fetchProject(projectUuid),
  });

export const useCreateProjectMutation = () => {
  const queryClient = useQueryClient();
  const posthog = usePostHog();
  const { setProject } = useAuth();
  return useMutation({
    mutationFn: async (projectCreate: ProjectCreate) =>
      await postProject(projectCreate),
    onSuccess: async () => {
      posthog.capture("projectCreated");
      await queryClient.invalidateQueries({
        queryKey: ["projects"],
      });
      const projects = queryClient.getQueryData<ProjectPublic[]>(["projects"]);
      if (projects && projects.length == 1) {
        setProject(projects[0]);
      }
    },
  });
};

export const useDeleteProjectMutation = () => {
  const queryClient = useQueryClient();
  const posthog = usePostHog();
  return useMutation({
    mutationFn: async (projectUuid: string) => await deleteProject(projectUuid),
    onSuccess: () => {
      posthog.capture("projectDeleted");
      queryClient.invalidateQueries({
        queryKey: ["projects"],
      });
    },
  });
};
