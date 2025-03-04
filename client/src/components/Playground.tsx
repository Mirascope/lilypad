import { Editor } from "@/components/Editor";

import { AddCardButton } from "@/components/AddCardButton";
import { CodeSnippet } from "@/components/CodeSnippet";
import { PLAYGROUND_TRANSFORMERS } from "@/components/lexical/markdown-transformers";
import { $findErrorTemplateNodes } from "@/components/lexical/template-node";
import LilypadDialog from "@/components/LilypadDialog";
import { NotFound } from "@/components/NotFound";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ToastVariants } from "@/components/ui/toast";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { Typography } from "@/components/ui/typography";
import { useToast } from "@/hooks/use-toast";
import {
  GenerationCreate,
  GenerationPublic,
  PlaygroundParameters,
} from "@/types/types";
import {
  useArchiveGenerationMutation,
  useCreateManagedGeneration,
  usePatchGenerationMutation,
  useRunMutation,
} from "@/utils/generations";
import {
  BaseEditorFormFields,
  getAvailableProviders,
  useBaseEditorForm,
} from "@/utils/playground-utils";
import { userQueryOptions } from "@/utils/users";
import { $convertToMarkdownString } from "@lexical/markdown";
import { useSuspenseQuery } from "@tanstack/react-query";
import { useNavigate, useParams } from "@tanstack/react-router";
import { LexicalEditor } from "lexical";
import { Trash, X } from "lucide-react";
import { BaseSyntheticEvent, useRef, useState } from "react";
import { SubmitHandler, useFieldArray } from "react-hook-form";
import ReactMarkdown from "react-markdown";

type EditorParameters = PlaygroundParameters & {
  inputs: Record<string, string>[];
};
export const Playground = ({
  version,
}: {
  version: GenerationPublic | null;
}) => {
  const { projectUuid, generationName } = useParams({
    strict: false,
  });
  const { toast } = useToast();
  const { data: user } = useSuspenseQuery(userQueryOptions());
  const navigate = useNavigate();
  const createGenerationMutation = useCreateManagedGeneration();
  const runMutation = useRunMutation();
  const patchGeneration = usePatchGenerationMutation();
  const archiveGeneration = useArchiveGenerationMutation();
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

  if (!projectUuid || !generationName) return <NotFound />;
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
      const generationCreate: GenerationCreate = {
        prompt_template: markdown,
        call_params: data?.generation?.call_params,
        name: generationName,
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
          generation: generationCreate,
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
          const newVersion = await createGenerationMutation.mutateAsync({
            projectUuid,
            generationCreate,
          });
          navigate({
            to: `/projects/${projectUuid}/generations/${newVersion.name}/versions/${newVersion.uuid}`,
            replace: true,
          });
        } catch (error) {
          console.error(error);
        }
      }
    });
  };
  const handleArchive = async () => {
    if (!version) return;
    let title = `Successfully deleted generation ${version.name}`;
    let variant: ToastVariants = "default";
    try {
      await archiveGeneration.mutateAsync({
        projectUuid,
        generationUuid: version.uuid,
        generationName: version.name,
      });
      navigate({
        to: `/projects/${projectUuid}/generations`,
      });
    } catch (e) {
      title = `Failed to delete generation ${version.name} v${version.version_num}. Delete generations that use ${version.name} v${version.version_num}.`;
      variant = "destructive";
    }
    toast({ title, variant });
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
              <Typography variant='h3'>{generationName}</Typography>
              {version && (
                <Button
                  disabled={version.is_default || patchGeneration.isPending}
                  onClick={(e: React.MouseEvent<HTMLButtonElement>) => {
                    e.preventDefault();
                    patchGeneration.mutate({
                      projectUuid,
                      generationUuid: version.uuid,
                      generationUpdate: { is_default: true },
                    });
                  }}
                >
                  {version.is_default ? "Default" : "Set default"}
                </Button>
              )}
              {version && (
                <LilypadDialog
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
                </LilypadDialog>
              )}
              {version && (
                <LilypadDialog
                  icon={<Trash />}
                  title={`Delete ${version.name} v${version.version_num}`}
                  description=''
                  dialogContentProps={{
                    className: "max-w-[600px]",
                  }}
                  buttonProps={{
                    variant: "outlineDestructive",
                  }}
                  dialogButtons={[
                    <Button
                      type='button'
                      variant='destructive'
                      onClick={handleArchive}
                    >
                      Delete
                    </Button>,
                    <Button type='button' variant='outline'>
                      Cancel
                    </Button>,
                  ]}
                >
                  {`Are you sure you want to delete ${version.name} v${version.version_num}?`}
                </LilypadDialog>
              )}
            </div>
            <div className='flex items-center gap-2'>
              <Button
                type='submit'
                name='save'
                loading={createGenerationMutation.isPending}
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
              <Label htmlFor='generation-template'>Generation Template</Label>
              <Editor
                inputs={inputs.map((input) => input.key)}
                ref={editorRef}
                promptTemplate={(version && version.prompt_template) || ""}
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
