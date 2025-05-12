import LilypadDialog from "@/components/LilypadDialog";
import { Button } from "@/components/ui/button";
import { DialogClose } from "@/components/ui/dialog";
import { Form } from "@/components/ui/form";
import { Separator } from "@/components/ui/separator";
import { Editor } from "@/ee/components/Editor";
import { PLAYGROUND_TRANSFORMERS } from "@/ee/components/lexical/markdown-transformers";
import {
  CommentCreate,
  CommentPublic,
  CommentUpdate,
  UserPublic,
} from "@/types/types";
import {
  commentsBySpanQueryOptions,
  useCreateCommentMutation,
  useDeleteCommentMutation,
  useUpdateCommentMutation,
} from "@/utils/comments";
import { formatRelativeTime } from "@/utils/strings";
import {
  userQueryOptions,
  usersByOrganizationQueryOptions,
} from "@/utils/users";
import { $convertToMarkdownString } from "@lexical/markdown";
import { useSuspenseQuery } from "@tanstack/react-query";
import { CLEAR_EDITOR_COMMAND, LexicalEditor } from "lexical";
import {
  CheckIcon,
  MessageSquareMore,
  PencilIcon,
  Trash,
  XIcon,
} from "lucide-react";
import { ReactNode, useEffect, useRef, useState } from "react";
import { useForm } from "react-hook-form";
import ReactMarkdown from "react-markdown";
import { toast } from "sonner";

export const CommentCards = ({ spanUuid }: { spanUuid: string }) => {
  const { data: spanComments } = useSuspenseQuery(
    commentsBySpanQueryOptions(spanUuid)
  );
  return (
    <>
      {spanComments.map((comment) => (
        <CommentCardContainer key={comment.uuid} comment={comment} />
      ))}
    </>
  );
};

const CommentCardContainer = ({ comment }: { comment: CommentPublic }) => {
  const { data: user } = useSuspenseQuery(userQueryOptions());

  const commentRef = useRef<LexicalEditor>(null);
  const methods = useForm<CommentUpdate>({
    defaultValues: {
      text: "",
    },
  });

  const [isEditing, setIsEditing] = useState(false);

  const isOwnComment = user?.uuid === comment.user_uuid;
  const updateCommentMutation = useUpdateCommentMutation();

  const handleEdit = () => {
    setIsEditing(true);
  };

  const handleCancel = () => {
    setIsEditing(false);
  };

  const onSubmit = () => {
    if (!commentRef?.current) return;

    const editorState = commentRef.current.getEditorState();

    void editorState.read(async () => {
      const markdown = $convertToMarkdownString(PLAYGROUND_TRANSFORMERS);
      await updateCommentMutation
        .mutateAsync({
          commentUuid: comment.uuid,
          commentUpdate: {
            text: markdown,
          },
        })
        .catch(() => toast.error("Error updating comment"));
      toast.success("Comment updated");
      setIsEditing(false);
    });
  };
  const renderEdit = (
    <div className="flex flex-col gap-4">
      <Form {...methods}>
        <form
          id={`comment-form-${comment.uuid}`}
          onSubmit={methods.handleSubmit(onSubmit)}
          className="flex flex-col gap-4"
        >
          <Editor
            ref={commentRef}
            editorClassName="h-[100px]"
            placeholderText="Comment..."
            template={comment.text}
          />
          <div className="flex justify-end gap-2">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={handleCancel}
              disabled={updateCommentMutation.isPending}
            >
              <XIcon className="mr-2 h-4 w-4" />
              Cancel
            </Button>
            <Button
              type="submit"
              variant="default"
              size="sm"
              disabled={updateCommentMutation.isPending}
            >
              <CheckIcon className="mr-2 h-4 w-4" />
              Update
            </Button>
          </div>
        </form>
      </Form>
    </div>
  );
  const renderControls = () => {
    if (!isOwnComment || isEditing) return null;
    return (
      <div>
        <Button
          variant="ghost"
          size="sm"
          onClick={handleEdit}
          className="h-8 w-8 p-0 opacity-0 group-hover:opacity-100 transition-opacity"
        >
          <PencilIcon className="h-4 w-4" />
          <span className="sr-only">Edit comment</span>
        </Button>
        <DeleteComment comment={comment} />
      </div>
    );
  };
  return (
    <CommentCard
      comment={comment}
      renderEdit={isEditing ? renderEdit : undefined}
      renderControls={renderControls}
    />
  );
};
interface CommentCardProps {
  comment: CommentPublic;
  renderControls?: () => ReactNode;
  renderEdit?: ReactNode;
}
export const CommentCard = ({
  comment,
  renderControls,
  renderEdit,
}: CommentCardProps) => {
  const { data: users } = useSuspenseQuery(usersByOrganizationQueryOptions());

  const userMap = users.reduce(
    (acc, user) => {
      acc[user.uuid] = user;
      return acc;
    },
    {} as Record<string, UserPublic>
  );
  const commentUser = userMap[comment.user_uuid];
  return (
    <div className="flex flex-col gap-4 pr-2">
      <div className="flex items-start gap-4">
        {/* <Avatar>
          <AvatarFallback>
            {commentUser.first_name.charAt(0)}
            {commentUser.last_name?.charAt(0)}
          </AvatarFallback>
        </Avatar> */}
        <div className="mb-2">
          <div className="flex items-center justify-between">
            <div className="flex gap-2 flex-wrap items-center">
              <div className="font-medium">
                {commentUser.first_name} {commentUser.last_name}
              </div>
              <div className="text-xs text-gray-500 dark:text-gray-400">
                {comment.updated_at && "Edited "}
                {formatRelativeTime(comment.updated_at ?? comment.created_at)}
              </div>
            </div>
            {renderControls?.()}
          </div>

          {renderEdit ?? <ReactMarkdown>{comment.text}</ReactMarkdown>}
        </div>
      </div>
    </div>
  );
};

const DeleteComment = ({ comment }: { comment: CommentPublic }) => {
  const deleteMutation = useDeleteCommentMutation();
  const handleDeleteComment = async () => {
    await deleteMutation
      .mutateAsync({
        spanUuid: comment.span_uuid,
        commentUuid: comment.uuid,
      })
      .catch(() => toast.error("Error removing comment"));
    toast.success("Successfully removed comment");
  };
  return (
    <LilypadDialog
      customTrigger={
        <Button
          variant="ghostDestructive"
          size="sm"
          className="h-8 w-8 p-0 opacity-0 group-hover:opacity-100 transition-opacity"
        >
          <Trash className="h-4 w-4" />
          <span className="sr-only">Delete comment</span>
        </Button>
      }
      title="Delete Comment"
      description="This action cannot be undone. Are you sure you want to delete this comment?"
    >
      <div className="flex flex-col gap-4">
        <CommentCard comment={comment} />
        <DialogClose asChild>
          <Button
            variant="outlineDestructive"
            size="sm"
            onClick={handleDeleteComment}
          >
            Delete
          </Button>
        </DialogClose>
      </div>
    </LilypadDialog>
  );
};

export const AddComment = ({ spanUuid }: { spanUuid: string }) => {
  const methods = useForm<CommentCreate>({
    defaultValues: {
      text: "",
      span_uuid: spanUuid,
    },
  });

  useEffect(() => {
    methods.setValue("span_uuid", spanUuid);
  }, [spanUuid, methods]);

  const commentCreate = useCreateCommentMutation();
  const commentRef = useRef<LexicalEditor>(null);
  const onSubmit = (data: CommentCreate) => {
    if (!commentRef?.current) return;
    const editorState = commentRef.current.getEditorState();

    void editorState.read(() => {
      const markdown = $convertToMarkdownString(PLAYGROUND_TRANSFORMERS);
      data.text = markdown;
    });
    commentCreate.mutate(data, {
      onSuccess: () => {
        methods.reset();
        commentRef?.current?.dispatchCommand(CLEAR_EDITOR_COMMAND, undefined);
        toast.success("Comment created");
      },
      onError: () => {
        toast.error("Error creating comment");
      },
    });
  };
  return (
    <Form {...methods}>
      <form
        id={`comment-form-${Math.random().toString(36).substring(7)}`}
        onSubmit={methods.handleSubmit(onSubmit)}
        className="comment-form flex flex-col gap-2 mx-2"
      >
        <Editor
          ref={commentRef}
          editorClassName="h-[100px] p-4"
          placeholderClassName="p-4"
          placeholderText="Comment..."
        />
        <Button className="mb-2" type="submit">
          Comment
        </Button>
      </form>
    </Form>
  );
};
export const Comment = ({ spanUuid }: { spanUuid: string }) => {
  return (
    <>
      <div className="flex-1 min-h-0">
        <CommentCards spanUuid={spanUuid} />
      </div>
      <div className="mt-4 shrink-0">
        <Separator />
        <div className="mt-4">
          <AddComment spanUuid={spanUuid} />
        </div>
      </div>
    </>
  );
};
export const CommentButton = ({ spanUuid }: { spanUuid: string }) => {
  const [showComments, setShowComments] = useState(false);
  const { data: spanComments } = useSuspenseQuery(
    commentsBySpanQueryOptions(spanUuid)
  );
  return (
    <div className={`flex flex-col ${showComments ? "h-full" : ""}`}>
      <div className="shrink-0">
        <Button
          size="icon"
          className="h-8 w-8 relative"
          variant="outline"
          onClick={() => setShowComments(!showComments)}
        >
          <MessageSquareMore />
          {spanComments.length > 0 && (
            <div className="absolute -top-2 -right-2 bg-primary text-primary-foreground text-xs rounded-full h-5 w-5 flex items-center justify-center font-medium">
              {spanComments.length > 9 ? "9+" : spanComments.length}
            </div>
          )}
        </Button>
      </div>
      {showComments && <Comment spanUuid={spanUuid} />}
    </div>
  );
};
