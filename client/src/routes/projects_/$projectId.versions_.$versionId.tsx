import {
  createFileRoute,
  useLoaderData,
  useParams,
} from "@tanstack/react-router";

import { useRef, useState } from "react";
import { $convertToMarkdownString } from "@lexical/markdown";
import { PLAYGROUND_TRANSFORMERS } from "@/components/lexical/markdown-transformers";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import api from "@/api";
import { CallArgsCreate, VersionPublic } from "@/types/types";
import { LexicalEditor } from "lexical";
import { $findErrorTemplateNodes } from "@/components/lexical/template-node";
import { EditorForm } from "@/components/EditorForm";
import { Typography } from "@/components/ui/typography";
import { Button } from "@/components/ui/button";

export const Route = createFileRoute(
  "/projects/$projectId/versions/$versionId"
)({
  loader: async ({
    params: { projectId, versionId },
  }): Promise<VersionPublic> =>
    (
      await api.get<VersionPublic>(
        `projects/${projectId}/versions/${versionId}`
      )
    ).data,
  pendingComponent: () => <div>Loading...</div>,
  errorComponent: ({ error }) => <div>{error.message}</div>,
  component: () => <EditorContainer />,
});

const EditorContainer = () => {
  const version = useLoaderData({
    from: Route.id,
  });
  const { projectId, versionId } = useParams({ from: Route.id });
  const queryClient = useQueryClient();
  const mutation = useMutation({
    mutationFn: (callArgsCreate: CallArgsCreate) => {
      return api.post(
        `projects/${projectId}/llm-fns/${version.llm_fn.id}/fn-params`,
        callArgsCreate
      );
    },
    onSuccess: () => {
      // Invalidate and refetch
      queryClient.invalidateQueries({
        queryKey: [`versions-${versionId}`],
      });
    },
  });
  const [editorErrors, setEditorErrors] = useState<string[]>([]);
  const editorRef = useRef<LexicalEditor>(null);

  const onSubmit = (data: CallArgsCreate) => {
    if (!editorRef?.current) return;

    const editorErrors = $findErrorTemplateNodes(editorRef.current);
    if (editorErrors.length > 0) {
      setEditorErrors(
        editorErrors.map(
          (node) => `'${node.getValue()}' is not a function argument.`
        )
      );
      return;
    }
    const editorState = editorRef.current.getEditorState();
    editorState.read(() => {
      const markdown = $convertToMarkdownString(PLAYGROUND_TRANSFORMERS);
      data.prompt_template = markdown;
      mutation.mutate(data);
      window.close();
    });
  };
  const vibeCheck = async () => {
    await api.get(`projects/${projectId}/versions/${versionId}/vibe`);
  };
  const playgroundButton = (
    <Button variant='outline' onClick={vibeCheck}>
      {"Vibe"}
    </Button>
  );
  return (
    <>
      <Typography variant='h2'>{"Playground"}</Typography>
      <EditorForm
        {...{
          llmFunction: version.llm_fn,
          latestVersion: version,
          editorErrors,
          onSubmit,
          ref: editorRef,
          isSynced: !version || Boolean(version && version.fn_params),
          formButtons: [playgroundButton],
        }}
      />
    </>
  );
};
