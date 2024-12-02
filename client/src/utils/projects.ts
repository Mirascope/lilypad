import api from "@/api";
import { ProjectPublic } from "@/types/types";
import { queryOptions } from "@tanstack/react-query";

export const fetchProjects = async () =>
  (await api.get<ProjectPublic[]>("/projects")).data;

export const fetchProject = async (projectUuid: string) => {
  return (await api.get<ProjectPublic>(`/projects/${projectUuid}`)).data;
};

export const projectsQueryOptions = () =>
  queryOptions({
    queryKey: ["projects"],
    queryFn: fetchProjects,
  });

export const projectQueryOptions = (projectUuid: string) =>
  queryOptions({
    queryKey: ["project", projectUuid],
    queryFn: () => fetchProject(projectUuid),
  });
