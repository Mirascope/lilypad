import {
  createFileRoute,
  useLoaderData,
  useNavigate,
  useParams,
} from "@tanstack/react-router";

import { useRef, useState } from "react";
import { $convertToMarkdownString } from "@lexical/markdown";
import { PLAYGROUND_TRANSFORMERS } from "@/components/lexical/markdown-transformers";
import { QueryClient, useMutation } from "@tanstack/react-query";
import api from "@/api";
import { CallArgsCreate, VersionPublic } from "@/types/types";
import { LexicalEditor } from "lexical";
import { $findErrorTemplateNodes } from "@/components/lexical/template-node";
import { EditorForm } from "@/components/EditorForm";
import { Typography } from "@/components/ui/typography";
import { Button } from "@/components/ui/button";
import { ArgsCards } from "@/components/ArgsCards";
import { AxiosResponse } from "axios";
import {
  Controller,
  FormProvider,
  SubmitHandler,
  useForm,
} from "react-hook-form";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";

const versionQuery = (projectId: string, versionId: string) => ({
  queryKey: ["project", projectId, "version", versionId],
  queryFn: async () =>
    (await api.get(`projects/${projectId}/versions/${versionId}`)).data,
});

type PlaygroundCallArgsCreate = CallArgsCreate & {
  shouldRunVibes?: boolean;
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
  component: () => <PlaygroundContainer />,
});

const PlaygroundContainer = () => {
  const version = useLoaderData({
    from: Route.id,
  });
  const navigate = useNavigate();
  const { projectId } = useParams({ from: Route.id });
  const mutation = useMutation({
    mutationFn: ({
      shouldRunVibes,
      ...callArgsCreate
    }: PlaygroundCallArgsCreate) =>
      api.post<CallArgsCreate, AxiosResponse<VersionPublic>>(
        `projects/${projectId}/llm-fns/${version.llm_fn.id}/fn-params`,
        callArgsCreate
      ),
    onSuccess: (data, variables) => {
      navigate({
        to: `/projects/${projectId}/versions/${data.data.id.toString()}`,
        replace: true,
      });
      if (variables.shouldRunVibes) {
        vibeCheck(data.data);
      }
    },
  });
  const { control, trigger, getValues } = useForm({});
  const [output, setOutput] = useState<string>("");
  const [editorErrors, setEditorErrors] = useState<string[]>([]);
  const editorRef = useRef<LexicalEditor>(null);

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
  const vibeCheck = async (version: VersionPublic) => {
    trigger();

    const results = await api.post(
      `projects/${projectId}/versions/${version.id}/vibe`,
      getValues()
    );
    setOutput(results.data);
  };
  const playgroundButton = (
    <Button
      key={"vibe-button"}
      type='submit'
      variant='outline'
      name='vibe-button'
    >
      {"Vibe"}
    </Button>
  );
  const renderEditableArgs = (key: string, value: string) => {
    let component;
    switch (value) {
      case "str":
        component = (
          <Controller
            name={key}
            control={control}
            rules={{ required: true }}
            render={({ field }) => (
              <Input
                {...field}
                placeholder='Enter value'
                type='text'
                value={field.value}
                onChange={field.onChange}
              />
            )}
          />
        );
        break;
      case "int":
        component = (
          <Controller
            name={key}
            control={control}
            rules={{ required: true }}
            render={({ field }) => (
              <Input
                {...field}
                placeholder='Enter value'
                type='number'
                value={field.value}
                onChange={field.onChange}
              />
            )}
          />
        );
        break;
    }
    return <CardContent>{component}</CardContent>;
  };
  return (
    <div className='p-2'>
      <Typography variant='h2'>{"Playground"}</Typography>
      <Typography variant='h3'>{version.llm_fn.function_name}</Typography>
      {version.llm_fn.arg_types && (
        <div className='flex'>
          <ArgsCards
            args={JSON.parse(version.llm_fn.arg_types)}
            customContent={renderEditableArgs}
          />
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
      {output && (
        <Card>
          <CardHeader>
            <CardTitle>{"Output"}</CardTitle>
          </CardHeader>
          <CardContent className='flex'>{output}</CardContent>
        </Card>
      )}
    </div>
  );
};
