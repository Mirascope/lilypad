import { Editor } from "@/components/Editor";

import { BaseSyntheticEvent, useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { SubmitHandler, useFieldArray } from "react-hook-form";
import { Label } from "@/components/ui/label";
import { LexicalEditor } from "lexical";
import {
  BaseEditorFormFields,
  getAvailableProviders,
  useBaseEditorForm,
} from "@/utils/playground-utils";
import { Input } from "@/components/ui/input";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { X } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { AddCardButton } from "@/components/AddCardButton";
import { $findErrorTemplateNodes } from "@/components/lexical/template-node";
import { $convertToMarkdownString } from "@lexical/markdown";
import { PLAYGROUND_TRANSFORMERS } from "@/components/lexical/markdown-transformers";
import { useNavigate, useParams } from "@tanstack/react-router";
import {
  useCreatePrompt,
  usePatchPromptMutation,
  useRunMutation,
} from "@/utils/prompts";
import {
  PromptCreate,
  PromptPublic,
  PlaygroundParameters,
} from "@/types/types";
import { NotFound } from "@/components/NotFound";
import IconDialog from "@/components/IconDialog";
import { CodeSnippet } from "@/components/CodeSnippet";
import { Typography } from "@/components/ui/typography";
import ReactMarkdown from "react-markdown";
import { useAuth } from "@/auth";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";

type EditorParameters = PlaygroundParameters & {
  inputs: Record<string, string>[];
};
export const Playground = ({ version }: { version: PromptPublic | null }) => {
  const { projectUuid, promptName } = useParams({
    strict: false,
  });
  const { user } = useAuth();
  const navigate = useNavigate();
  const createPromptMutation = useCreatePrompt();
  const runMutation = useRunMutation();
  const patchPrompt = usePatchPromptMutation();
  const methods = useBaseEditorForm<EditorParameters>({
    latestVersion: version,
    additionalDefaults: {
      inputs: version?.arg_types
        ? Object.keys(version.arg_types).map((key) => ({
            key,
            value: "",
          }))
        : [],
    },
  });
  const { fields, append, remove } = useFieldArray<EditorParameters>({
    control: methods.control,
    name: "inputs",
  });

  const inputs: Record<string, string>[] = methods.watch("inputs");
  const [editorErrors, setEditorErrors] = useState<string[]>([]);
  const editorRef = useRef<LexicalEditor>(null);

  if (!projectUuid || !promptName) return <NotFound />;
  const onSubmit: SubmitHandler<EditorParameters> = (
    data: EditorParameters,
    event?: BaseSyntheticEvent
  ) => {
    event?.preventDefault();
    methods.clearErrors();
    setEditorErrors([]);
    if (!editorRef?.current) return;
    const buttonName = (
      event?.nativeEvent as unknown as { submitter: HTMLButtonElement }
    ).submitter.name;
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
      const promptCreate: PromptCreate = {
        template: markdown,
        call_params: data?.prompt?.call_params,
        name: promptName,
        arg_types: inputs.reduce(
          (acc, input) => {
            acc[input.key] = "str";
            return acc;
          },
          {} as Record<string, string>
        ),
        signature: "",
        hash: "",
        code: "",
      };
      const isValid = await methods.trigger();
      if (buttonName === "run") {
        let hasErrors = false;
        data.inputs.forEach((input, index) => {
          if (!input.value) {
            methods.setError(`inputs.${index}.value`, {
              type: "required",
              message: "Value is required for Run",
            });
            hasErrors = true;
          }
        });
        if (!isValid || hasErrors) return;
        const inputValues = inputs.reduce(
          (acc, input) => {
            acc[input.key] = input.value;
            return acc;
          },
          {} as Record<string, string>
        );
        const playgroundValues: PlaygroundParameters = {
          prompt: promptCreate,
          provider: data.provider,
          model: data.model,
          arg_values: inputValues,
        };
        await runMutation.mutateAsync({
          projectUuid,
          playgroundValues,
        });
      } else {
        try {
          if (!isValid) return;
          const newVersion = await createPromptMutation.mutateAsync({
            projectUuid,
            promptCreate,
          });
          navigate({
            to: `/projects/${projectUuid}/prompts/${newVersion.name}/versions/${newVersion.uuid}`,
            replace: true,
          });
        } catch (error) {
          console.error(error);
        }
      }
    });
  };
  const renderBottomPanel = () => {
    return (
      <>
        <div className='space-y-2'>
          <FormLabel className='text-base'>{"Inputs"}</FormLabel>
          <div className='flex gap-4 flex-wrap pb-4'>
            {fields.map((field, index) => (
              <Card key={field.id} className='w-64 flex-shrink-0 relative'>
                <Button
                  type='button'
                  variant='ghost'
                  size='icon'
                  onClick={() => remove(index)}
                  className='h-6 w-6 absolute top-2 right-2 hover:bg-gray-100'
                >
                  <X className='h-4 w-4' />
                </Button>
                <CardContent className='pt-6 space-y-4'>
                  <div className='w-full'>
                    <FormField
                      control={methods.control}
                      name={`inputs.${index}.key`}
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Args</FormLabel>
                          <FormControl>
                            <Input placeholder='Args' {...field} />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                  </div>
                  <div className='w-full'>
                    <FormField
                      control={methods.control}
                      name={`inputs.${index}.value`}
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Value</FormLabel>
                          <FormControl>
                            <Input
                              {...field}
                              placeholder='Enter value'
                              value={field.value}
                              onChange={field.onChange}
                            />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                  </div>
                </CardContent>
              </Card>
            ))}
            <AddCardButton onClick={() => append({ key: "", value: "" })} />
          </div>
        </div>
        {runMutation.isSuccess && (
          <div>
            <FormLabel className='text-base'>{"Outputs"}</FormLabel>
            <Card className='mt-2'>
              <CardContent className='flex flex-col p-6'>
                <ReactMarkdown>{runMutation.data}</ReactMarkdown>
              </CardContent>
            </Card>
          </div>
        )}
      </>
    );
  };
  const doesProviderExist = getAvailableProviders(user).length > 0;
  return (
    <div className='m-auto w-[1200px] p-4'>
      <Form {...methods}>
        <form onSubmit={methods.handleSubmit(onSubmit)}>
          <div className='flex justify-between'>
            <div className='flex items-center gap-2'>
              <Typography variant='h3'>{promptName}</Typography>
              {version && (
                <Button
                  disabled={version.is_default || patchPrompt.isPending}
                  onClick={(e: React.MouseEvent<HTMLButtonElement>) => {
                    e.preventDefault();
                    patchPrompt.mutate({
                      projectUuid,
                      promptUuid: version.uuid,
                      promptUpdate: { is_default: true },
                    });
                  }}
                >
                  {version.is_default ? "Default" : "Set default"}
                </Button>
              )}
              {version && (
                <IconDialog
                  text='Code'
                  title='Copy Code'
                  description='Copy this codeblock into your application.'
                  dialogContentProps={{
                    className: "max-w-[600px]",
                  }}
                  buttonProps={{
                    disabled: methods.formState.isDirty,
                  }}
                >
                  <CodeSnippet code={version.code} />
                </IconDialog>
              )}
            </div>
            <div className='flex items-center gap-2'>
              <Button
                type='submit'
                name='save'
                loading={createPromptMutation.isPending}
              >
                Save
              </Button>
              <Tooltip>
                <TooltipTrigger asChild>
                  <span>
                    <Button
                      name='run'
                      loading={runMutation.isPending}
                      disabled={!doesProviderExist}
                    >
                      Run
                    </Button>
                  </span>
                </TooltipTrigger>
                <TooltipContent className='bg-gray-500'>
                  <p className='max-w-xs break-words'>
                    {doesProviderExist ? (
                      "Run the playground with the selected provider."
                    ) : (
                      <span>
                        You need to add an API key to run the playground.
                      </span>
                    )}
                  </p>
                </TooltipContent>
              </Tooltip>
            </div>
          </div>
          <div className='flex gap-4'>
            <div className='lexical form-group space-y-2 w-[600px]'>
              <Label htmlFor='prompt-template'>Prompt Template</Label>
              <Editor
                inputs={inputs.map((input) => input.key)}
                ref={editorRef}
                promptTemplate={(version && version.template) || ""}
              />
              {editorErrors.length > 0 &&
                editorErrors.map((error, i) => (
                  <div key={i} className='text-red-500 text-sm mt-1'>
                    {error}
                  </div>
                ))}
            </div>
            <BaseEditorFormFields />
          </div>
          {renderBottomPanel()}
        </form>
      </Form>
    </div>
  );
};
