import api from "@/api";
import { TagCreate, TagPublic } from "@/types/types";
import { queryOptions, useMutation, useQueryClient } from "@tanstack/react-query";

export const fetchTags = async () => (await api.get<TagPublic[]>("/tags")).data;

export const fetchTagsByProject = async (projectUuid: string) =>
  (await api.get<TagPublic[]>(`/projects/${projectUuid}/tags`)).data;

export const fetchTag = async (tagUuid: string) => {
  return (await api.get<TagPublic>(`/tags/${tagUuid}`)).data;
};

export const postTag = async (tagCreate: TagCreate) => {
  return (await api.post<TagPublic>(`/tags`, tagCreate)).data;
};

export const patchTag = async (tagUuid: string, tagUpdate: TagCreate) => {
  return (await api.patch<TagPublic>(`/tags/${tagUuid}`, tagUpdate)).data;
};

export const deleteTag = async (tagUuid: string) => {
  return (await api.delete<boolean>(`/tags/${tagUuid}`)).data;
};

export const tagsQueryOptions = () =>
  queryOptions({
    queryKey: ["tags"],
    queryFn: fetchTags,
  });

export const tagQueryOptions = (tagUuid: string) =>
  queryOptions({
    queryKey: ["tags", tagUuid],
    queryFn: () => fetchTag(tagUuid),
  });

export const tagsByProjectsQueryOptions = (projectUuid: string) =>
  queryOptions({
    queryKey: ["projects", projectUuid, "tags"],
    queryFn: () => fetchTagsByProject(projectUuid),
  });

export const useCreateTagMutation = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (tagCreate: TagCreate) => await postTag(tagCreate),
    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: ["tags"],
      });
    },
  });
};

export const useUpdateTagMutation = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ tagUuid, tagUpdate }: { tagUuid: string; tagUpdate: TagCreate }) =>
      await patchTag(tagUuid, tagUpdate),
    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: ["tags"],
      });
    },
  });
};

export const useDeleteTagMutation = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (tagUuid: string) => await deleteTag(tagUuid),
    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: ["tags"],
      });
    },
  });
};
