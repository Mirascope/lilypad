import api from "@/src/api";
import { CommentCreate, CommentPublic, CommentUpdate } from "@/src/types/types";
import { queryOptions, useMutation, useQueryClient } from "@tanstack/react-query";

export const fetchComments = async () => (await api.get<CommentPublic[]>("/comments")).data;

export const fetchCommentsBySpan = async (spanUuid: string) =>
  (await api.get<CommentPublic[]>(`/spans/${spanUuid}/comments`)).data;

export const fetchComment = async (commentUuid: string) => {
  return (await api.get<CommentPublic>(`/comments/${commentUuid}`)).data;
};

export const postComment = async (commentCreate: CommentCreate) => {
  return (await api.post<CommentPublic>(`/comments`, commentCreate)).data;
};

export const patchComment = async (commentUuid: string, commentUpdate: CommentUpdate) => {
  return (await api.patch<CommentPublic>(`/comments/${commentUuid}`, commentUpdate)).data;
};
export const deleteComment = async (commentUuid: string) => {
  return (await api.delete<boolean>(`/comments/${commentUuid}`)).data;
};

export const commentsQueryOptions = () =>
  queryOptions({
    queryKey: ["comments"],
    queryFn: fetchComments,
  });

export const commentsBySpanQueryOptions = (spanUuid: string) =>
  queryOptions({
    queryKey: ["spans", spanUuid, "comments"],
    queryFn: () => fetchCommentsBySpan(spanUuid),
  });

export const commentQueryOptions = (commentUuid: string) =>
  queryOptions({
    queryKey: ["comments", commentUuid],
    queryFn: () => fetchComment(commentUuid),
  });

export const useCreateCommentMutation = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (commentCreate: CommentCreate) => await postComment(commentCreate),
    onSuccess: async (data) => {
      await queryClient.invalidateQueries({
        queryKey: ["spans", data.span_uuid, "comments"],
      });
    },
  });
};

export const useUpdateCommentMutation = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      commentUuid,
      commentUpdate,
    }: {
      commentUuid: string;
      commentUpdate: CommentUpdate;
    }) => await patchComment(commentUuid, commentUpdate),
    onSuccess: async (data) => {
      await queryClient.invalidateQueries({
        queryKey: ["spans", data.span_uuid, "comments"],
      });
    },
  });
};

export const useDeleteCommentMutation = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ commentUuid }: { spanUuid: string; commentUuid: string }) =>
      await deleteComment(commentUuid),
    onSuccess: async (_, { spanUuid }) => {
      await queryClient.invalidateQueries({
        queryKey: ["spans", spanUuid, "comments"],
      });
    },
  });
};
