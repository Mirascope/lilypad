import api from "@/src/api";
import { useAuth } from "@/src/auth";
import { ProjectCreate, ProjectPublic } from "@/src/types/types";
import { queryOptions, useMutation, useQueryClient } from "@tanstack/react-query";
import { usePostHog } from "posthog-js/react";

export const fetchProjects = async () => (await api.get<ProjectPublic[]>("/projects")).data;

export const fetchProject = async (projectUuid: string) => {
  return (await api.get<ProjectPublic>(`/projects/${projectUuid}`)).data;
};

export const postProject = async (projectCreate: ProjectCreate) => {
  return (await api.post<ProjectPublic>(`/projects`, projectCreate)).data;
};

export const patchProject = async (projectUuid: string, projectUpdate: ProjectCreate) => {
  return (await api.patch<ProjectPublic>(`/projects/${projectUuid}`, projectUpdate)).data;
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
    mutationFn: async (projectCreate: ProjectCreate) => await postProject(projectCreate),
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

export const useUpdateProjectMutation = () => {
  const queryClient = useQueryClient();
  const { setProject } = useAuth();
  return useMutation({
    mutationFn: async ({
      projectUuid,
      projectUpdate,
    }: {
      projectUuid: string;
      projectUpdate: ProjectCreate;
    }) => await patchProject(projectUuid, projectUpdate),
    onSuccess: async (data) => {
      await queryClient.invalidateQueries({
        queryKey: ["projects"],
      });
      setProject(data);
    },
  });
};

export const useDeleteProjectMutation = () => {
  const queryClient = useQueryClient();
  const posthog = usePostHog();
  const { setProject } = useAuth();
  return useMutation({
    mutationFn: async (projectUuid: string) => await deleteProject(projectUuid),
    onSuccess: async () => {
      posthog.capture("projectDeleted");
      await queryClient.invalidateQueries({
        queryKey: ["projects"],
      });
      setProject(null);
    },
  });
};
