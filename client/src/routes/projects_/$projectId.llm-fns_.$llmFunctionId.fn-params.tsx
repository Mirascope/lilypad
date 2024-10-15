import {
  createFileRoute,
  useLoaderData,
  useParams,
} from "@tanstack/react-router";
import { Editor } from "@/routes/-editor";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useEffect, useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { Controller, useForm, useWatch } from "react-hook-form";
import { $convertToMarkdownString } from "@lexical/markdown";
import { PLAYGROUND_TRANSFORMERS } from "@/components/lexical/markdown-transformers";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import api from "@/api";
import {
  CallArgsCreate,
  LLMFunctionBasePublic,
  Provider,
  VersionPublic,
  ResponseFormat,
} from "@/types/types";
import { Label } from "@/components/ui/label";
import { ModelCombobox } from "@/components/ui/model-combobox";
import { LexicalEditor } from "lexical";
import { Typography } from "@/components/ui/typography";
import { ArgsCards } from "@/components/ArgsCards";
import { FormSlider } from "@/components/FormSlider";
import { $findErrorTemplateNodes } from "@/components/lexical/template-node";
import { EditorForm } from "@/components/EditorForm";

type LoaderData = {
  llmFunction: LLMFunctionBasePublic;
  latestVersion: VersionPublic | null;
};

export const Route = createFileRoute(
  "/projects/$projectId/llm-fns/$llmFunctionId/fn-params"
)({
  loader: async ({
    params: { projectId, llmFunctionId },
  }): Promise<LoaderData> => {
    const llmFunction = (
      await api.get<LLMFunctionBasePublic>(
        `projects/${projectId}/llm-fns/${llmFunctionId}`
      )
    ).data;
    let latestVersion = null;
    try {
      latestVersion = (
        await api.get<VersionPublic>(
          `projects/${projectId}/versions/${llmFunction.function_name}/active`
        )
      ).data;
    } catch (error) {}
    return {
      llmFunction: llmFunction,
      latestVersion: latestVersion,
    };
  },
  pendingComponent: () => <div>Loading...</div>,
  errorComponent: ({ error }) => <div>{error.message}</div>,
  component: () => <EditorContainer />,
});

const EditorContainer = () => {
  const { llmFunction, latestVersion } = useLoaderData({
    from: Route.id,
  });
  const { projectId } = useParams({ from: Route.id });
  const queryClient = useQueryClient();
  const mutation = useMutation({
    mutationFn: (callArgsCreate: CallArgsCreate) => {
      return api.post(
        `projects/${projectId}/llm-fns/${llmFunction.id}/fn-params`,
        callArgsCreate
      );
    },
    onSuccess: () => {
      // Invalidate and refetch
      queryClient.invalidateQueries({
        queryKey: [`llmFunctions-${llmFunction.id}-fnParams`],
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
  return (
    <EditorForm
      {...{
        llmFunction,
        latestVersion,
        editorErrors,
        onSubmit,
        ref: editorRef,
        isSynced:
          !latestVersion || Boolean(latestVersion && latestVersion.fn_params),
      }}
    />
  );
};
