import { useNavigate } from "@tanstack/react-router";

import { useEffect, useRef, useState } from "react";
import { $convertToMarkdownString } from "@lexical/markdown";
import { PLAYGROUND_TRANSFORMERS } from "@/components/lexical/markdown-transformers";
import {
  useMutation,
  useQueryClient,
  useSuspenseQuery,
} from "@tanstack/react-query";
import api from "@/api";
import {
  AnthropicCallParams,
  FunctionCreate,
  GeminiCallParams,
  OpenAICallParams,
  PromptCreate,
  Provider,
  VersionPublic,
} from "@/types/types";
import { LexicalEditor } from "lexical";
import { $findErrorTemplateNodes } from "@/components/lexical/template-node";
import { EditorForm } from "@/components/EditorForm";
import { EditorFormValues, formValuesToApi } from "@/utils/editor-form-utils";
import { Typography } from "@/components/ui/typography";
import { Button } from "@/components/ui/button";
import { ArgsCards } from "@/components/ArgsCards";
import { AxiosResponse } from "axios";
import { Controller, SubmitHandler, useForm } from "react-hook-form";
import {
  Card,
  CardContent,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { getErrorMessage } from "@/lib/utils";
import { CodeSnippet } from "@/components/CodeSnippet";
import ReactMarkdown from "react-markdown";
import { useCreateVersion } from "@/utils/versions";
import { spanQueryOptions } from "@/utils/spans";
import { IconDialog } from "@/components/IconDialog";
import { Code } from "lucide-react";

export const Playground = ({
  version,
  projectId,
  spanId,
}: {
  version: VersionPublic;
  projectId: number;
  spanId?: string;
}) => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { data: spanData } = useSuspenseQuery(
    spanQueryOptions(projectId, spanId)
  );
  const createVersionMutation = useCreateVersion();
  const vibeMutation = useMutation({
    mutationFn: async ({
      projectId,
      versionId,
    }: {
      projectId: number;
      versionId: string;
    }) =>
      (
        await api.post(
          `projects/${projectId}/versions/${versionId}/run`,
          getValues()
        )
      ).data,
  });
  const setActiveMutation = useMutation({
    mutationFn: async () =>
      (
        await api.patch<undefined, AxiosResponse<VersionPublic>>(
          `projects/${projectId}/versions/${version.id}/active`
        )
      ).data,
    onSuccess: (data) => {
      queryClient.invalidateQueries({
        queryKey: [
          "project",
          data.project_id?.toString(),
          "version",
          data.id.toString(),
        ],
      });
    },
  });
  let argTypes = version.function.arg_types || {};
  argTypes = Object.keys(argTypes).reduce(
    (acc, key) => {
      acc[key as keyof string] = "";
      return acc;
    },
    {} as Record<keyof string, string>
  );
  const {
    control,
    trigger,
    getValues,
    reset,
    formState: { errors },
  } = useForm({
    defaultValues: argTypes,
  });
  const [editorErrors, setEditorErrors] = useState<string[]>([]);
  const editorRef = useRef<LexicalEditor>(null);

  useEffect(() => {
    if (!spanData) return;
    const data = spanData.data;

    let argValues;
    try {
      argValues = JSON.parse(data.attributes["lilypad.arg_values"]);
    } catch (e) {
      argValues = {};
    }
    reset(argValues);
  }, [spanData, reset]);
  const onSubmit: SubmitHandler<EditorFormValues> = (
    data: EditorFormValues,
    event
  ) => {
    event?.preventDefault();
    const nativeEvent = event?.nativeEvent as SubmitEvent;
    const actionType = (nativeEvent.submitter as HTMLButtonElement).name;
    const shouldRunVibes = actionType === "vibe-button";
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
    editorState.read(async () => {
      const markdown = $convertToMarkdownString(PLAYGROUND_TRANSFORMERS);
      data.template = markdown;
      const functionCreate: FunctionCreate = {
        id: version.function.id,
        name: version.function_name,
        arg_types: version.function.arg_types,
        hash: version.function.hash,
        code: version.function.code,
      };
      let callParams:
        | OpenAICallParams
        | AnthropicCallParams
        | GeminiCallParams
        | null = null;
      if (
        data.provider == Provider.OPENAI ||
        data.provider == Provider.OPENROUTER
      ) {
        callParams = data.openaiCallParams as OpenAICallParams;
        if (
          data.provider == Provider.OPENAI ||
          data.provider == Provider.OPENROUTER
        ) {
          callParams as OpenAICallParams;
        }
      } else if (data.provider == Provider.ANTHROPIC) {
        callParams = data.anthropicCallParams as AnthropicCallParams;
      } else if (data.provider == Provider.GEMINI) {
        callParams = data.geminiCallParams as GeminiCallParams;
      }
      callParams = formValuesToApi(callParams);
      const promptCreate: PromptCreate = {
        template: data.template,
        provider: data.provider,
        model: data.model,
        call_params: callParams,
      };
      try {
        const newVersion = await createVersionMutation.mutateAsync({
          projectId,
          versionCreate: {
            function_create: functionCreate,
            prompt_create: promptCreate,
          },
        });
        navigate({
          to: `/projects/${projectId}/functions/${newVersion.function_name}/versions/${newVersion.id}`,
          replace: true,
        });
        if (shouldRunVibes) {
          const isValid = await trigger();
          if (isValid) {
            vibeMutation.mutate({
              projectId,
              versionId: newVersion.id.toString(),
            });
          }
        }
      } catch (error) {
        console.error(error);
      }
    });
  };
  const playgroundButton = (
    <Button
      key={"vibe-button"}
      type='submit'
      variant='outline'
      name='vibe-button'
      loading={vibeMutation.isPending}
    >
      {"Vibe"}
    </Button>
  );
  const renderEditableArgs = (key: string, value: string) => {
    let component;
    switch (value) {
      case "str":
      case "int":
        component = (
          <Controller
            name={key}
            control={control}
            rules={{ required: "This field is required" }}
            render={({ field }) => (
              <Input
                {...field}
                placeholder='Enter value'
                type={value === "str" ? "text" : "number"}
                value={field.value}
                onChange={field.onChange}
              />
            )}
          />
        );
        break;
    }
    return (
      <>
        <CardContent>{component}</CardContent>
        {errors[key] && (
          <CardFooter className='text-red-500 text-sm mt-1'>
            {getErrorMessage(errors[key].message)}
          </CardFooter>
        )}
      </>
    );
  };
  if (version && !version.prompt) {
    return (
      <div className='flex flex-col justify-center items-center'>
        {"Playground is unavailable for non-synced calls"}
        <Button
          onClick={() => {
            navigate({
              to: `/projects/${projectId}/`,
            });
          }}
        >
          Back to Traces
        </Button>
      </div>
    );
  }
  return (
    <div className='p-4 flex flex-col gap-2'>
      <div className='flex justify-between'>
        <div className='flex items-center gap-2'>
          <Typography variant='h3'>{version.function.name}</Typography>
          <Button
            disabled={version.is_active || setActiveMutation.isPending}
            onClick={() => setActiveMutation.mutate()}
          >
            {version.is_active ? "Active" : "Set active"}
          </Button>
        </div>
        <IconDialog
          icon={<Code />}
          title='Copy Code'
          description='Copy this codeblock into your application.'
        >
          <CodeSnippet code={version.function.code} />
        </IconDialog>
      </div>
      {version.function.arg_types && (
        <div className='flex'>
          <ArgsCards
            args={version.function.arg_types}
            customContent={renderEditableArgs}
          />
        </div>
      )}
      <EditorForm
        {...{
          llmFunction: version.function,
          latestVersion: version,
          editorErrors,
          onSubmit,
          ref: editorRef,
          isSynced: !version || Boolean(version && version.prompt),
          formButtons: [playgroundButton],
        }}
      />
      {vibeMutation.isSuccess && (
        <Card className='mt-2'>
          <CardHeader>
            <CardTitle>{"Output"}</CardTitle>
          </CardHeader>
          <CardContent className='flex flex-col'>
            <ReactMarkdown>{vibeMutation.data}</ReactMarkdown>
          </CardContent>
        </Card>
      )}
    </div>
  );
};
