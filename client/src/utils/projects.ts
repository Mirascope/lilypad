import api from "@/api";
import { ProjectPublic } from "@/types/types";
import { queryOptions } from "@tanstack/react-query";

export const fetchProjects = async () =>
  (await api.get<ProjectPublic[]>("/projects")).data;

export const fetchProject = async (projectId: number) => {
  return (await api.get<ProjectPublic>(`/projects/${projectId}`)).data;
};

export const projectsQueryOptions = () =>
  queryOptions({
    queryKey: ["projects"],
    queryFn: fetchProjects,
  });

export const projectQueryOptions = (projectId: number) =>
  queryOptions({
    queryKey: ["project", projectId],
    queryFn: () => fetchProject(projectId),
  });
