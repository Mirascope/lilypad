import api from "@/api";
import { ProjectCreate, ProjectPublic } from "@/types/types";
import {
  queryOptions,
  useMutation,
  useQueryClient,
} from "@tanstack/react-query";

export const fetchProjects = async () =>
  (await api.get<ProjectPublic[]>("/projects")).data;

export const fetchProject = async (projectUuid: string) => {
  return (await api.get<ProjectPublic>(`/projects/${projectUuid}`)).data;
};

export const postProject = async (projectCreate: ProjectCreate) => {
  return (await api.post<ProjectPublic>(`/projects`, projectCreate)).data;
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
  return useMutation({
    mutationFn: async (projectCreate: ProjectCreate) =>
      await postProject(projectCreate),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["projects"],
      });
    },
  });
};
