import {
  createFileRoute,
  useLoaderData,
  useNavigate,
  useParams,
  useSearch,
} from "@tanstack/react-router";

import { useEffect, useRef, useState } from "react";
import { $convertToMarkdownString } from "@lexical/markdown";
import { PLAYGROUND_TRANSFORMERS } from "@/components/lexical/markdown-transformers";
import { QueryClient, useMutation, useQuery } from "@tanstack/react-query";
import api from "@/api";
import { CallArgsCreate, SpanPublic, VersionPublic } from "@/types/types";
import { LexicalEditor } from "lexical";
import { $findErrorTemplateNodes } from "@/components/lexical/template-node";
import { EditorForm } from "@/components/EditorForm";
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
import { SkeletonCard } from "@/components/SkeletonCard";
import { getErrorMessage } from "@/lib/utils";

const versionQuery = (projectId: string, versionId: string) => ({
  queryKey: ["project", projectId, "version", versionId],
  queryFn: async () =>
    (await api.get(`projects/${projectId}/versions/${versionId}`)).data,
});

type PlaygroundCallArgsCreate = CallArgsCreate & {
  shouldRunVibes?: boolean;
};

type PlaygroundSearchParams = {
  spanId?: string;
};

export const loader =
  (queryClient: QueryClient) =>
  async ({
    params: { projectId, versionId },
  }: {
    params: { projectId: string; versionId: string };
  }) => {
    const query = versionQuery(projectId, versionId);
    return (
      queryClient.getQueryData(query.queryKey) ??
      (await queryClient.fetchQuery(query))
    );
  };
const queryClient = new QueryClient();
export const Route = createFileRoute(
  "/projects/$projectId/versions/$versionId"
)({
  loader: loader(queryClient),
  pendingComponent: () => <div>Loading...</div>,
  errorComponent: ({ error }) => <div>{error.message}</div>,
  validateSearch: (search: Record<string, unknown>): PlaygroundSearchParams => {
    return search.spanId ? { spanId: search.spanId as string } : {};
  },
  component: () => <PlaygroundContainer />,
});

const PlaygroundContainer = () => {
  const version = useLoaderData({
    from: Route.id,
  }) as VersionPublic;
  const navigate = useNavigate();
  const { projectId } = useParams({ from: Route.id });
  const { spanId } = useSearch({ from: Route.id });

  const { isLoading, data: spanData } = useQuery<SpanPublic>({
    queryKey: ["span", spanId],
    queryFn: async () =>
      (await api.get(`/projects/${projectId}/spans/${spanId}`)).data,
    retry: false,
    enabled: Boolean(spanId),
  });
  const mutation = useMutation({
    mutationFn: ({
      shouldRunVibes,
      ...callArgsCreate
    }: PlaygroundCallArgsCreate) =>
      api.post<CallArgsCreate, AxiosResponse<VersionPublic>>(
        `projects/${projectId}/llm-fns/${version.llm_fn.id}/fn-params`,
        callArgsCreate
      ),
    onSuccess: async (data, variables) => {
      navigate({
        to: `/projects/${projectId}/versions/${data.data.id.toString()}`,
        replace: true,
      });
      if (variables.shouldRunVibes) {
        const isValid = await trigger();
        if (isValid) {
          vibeMutation.mutate();
        }
      }
    },
  });
  const vibeMutation = useMutation({
    mutationFn: async () =>
      (
        await api.post(
          `projects/${projectId}/versions/${version.id}/vibe`,
          getValues()
        )
      ).data,
  });

  let argTypes = version.llm_fn.arg_types || {};
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
  const onSubmit: SubmitHandler<CallArgsCreate> = (data, event) => {
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
    editorState.read(() => {
      const markdown = $convertToMarkdownString(PLAYGROUND_TRANSFORMERS);
      data.prompt_template = markdown;
      mutation.mutate({
        ...data,
        shouldRunVibes,
      });
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
  if (version && !version.fn_params) {
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
    <div className='p-2'>
      <Typography variant='h2'>{"Playground"}</Typography>
      <Typography variant='h3'>{version.llm_fn.function_name}</Typography>
      {version.llm_fn.arg_types && (
        <div className='flex'>
          {isLoading ? (
            <SkeletonCard />
          ) : (
            <ArgsCards
              args={version.llm_fn.arg_types}
              customContent={renderEditableArgs}
            />
          )}
        </div>
      )}
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
      {vibeMutation.isSuccess && (
        <Card>
          <CardHeader>
            <CardTitle>{"Output"}</CardTitle>
          </CardHeader>
          <CardContent className='flex'>{vibeMutation.data}</CardContent>
        </Card>
      )}
    </div>
  );
};
