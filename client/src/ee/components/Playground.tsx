import { Editor } from "@/ee/components/Editor";

import { AddCardButton } from "@/components/AddCardButton";
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Sheet,
  SheetClose,
  SheetContent,
  SheetFooter,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { PLAYGROUND_TRANSFORMERS } from "@/ee/components/lexical/markdown-transformers";
import { $findErrorTemplateNodes } from "@/ee/components/lexical/template-node";
import { PlaygroundParameters } from "@/ee/types/types";
import {
  useCreateManagedGeneration,
  useRunMutation,
} from "@/ee/utils/generations";
import {
  FormItemValue,
  simplifyFormItem,
  TypedInput,
} from "@/ee/utils/input-utils";
import { GenerationCreate, GenerationPublic } from "@/types/types";
import { usePatchGenerationMutation } from "@/utils/generations";
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
import { X } from "lucide-react";
import { BaseSyntheticEvent, useRef, useState } from "react";
import { SubmitHandler, useFieldArray, useFormContext } from "react-hook-form";
import ReactMarkdown from "react-markdown";

type FormValues = {
  inputs: Record<string, any>[];
};
type EditorParameters = PlaygroundParameters & FormValues;
export const Playground = ({
  version,
}: {
  version: GenerationPublic | null;
}) => {
  const { projectUuid, generationName } = useParams({
    strict: false,
  });
  const { data: user } = useSuspenseQuery(userQueryOptions());
  const navigate = useNavigate();
  const createGenerationMutation = useCreateManagedGeneration();
  const runMutation = useRunMutation();
  const patchGeneration = usePatchGenerationMutation();
  const methods = useBaseEditorForm<EditorParameters>({
    latestVersion: version,
    additionalDefaults: {
      inputs: version?.arg_types
        ? Object.keys(version.arg_types).map((key) => ({
            key,
            type: version.arg_types?.[key] || "str",
            value: "",
          }))
        : [],
    },
  });

  const inputs = methods.watch("inputs");
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
            acc[input.key] = input.type;
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
        const newVersion = await createGenerationMutation.mutateAsync({
          projectUuid,
          generationCreate,
        });
        const inputValues = inputs.reduce(
          (acc, input) => {
            if (input.type === "list" || input.type === "dict") {
              try {
                acc[input.key] = simplifyFormItem(input as FormItemValue);
              } catch (e) {
                acc[input.key] = input.value;
              }
            } else {
              acc[input.key] = input.value;
            }
            return acc;
          },
          {} as Record<string, any>
        );
        const playgroundValues: PlaygroundParameters = {
          generation: generationCreate,
          provider: data.provider,
          model: data.model,
          arg_values: inputValues,
        };
        await runMutation.mutateAsync({
          projectUuid,
          generationUuid: newVersion.uuid,
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
            to: `/projects/${projectUuid}/generations/${newVersion.name}/${newVersion.uuid}/overview`,
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
    <Form {...methods}>
      <form onSubmit={methods.handleSubmit(onSubmit)}>
        <div className='flex flex-col gap-4'>
          <div className='flex justify-between gap-4 w-full'>
            <div className='flex items-center gap-2'>
              <Button
                type='submit'
                name='save'
                loading={createGenerationMutation.isPending}
                className='bg-mirascope hover:bg-mirascope-light text-white font-medium'
              >
                Save
              </Button>
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
                  className='border border-gray-300 bg-white hover:bg-gray-100 text-gray-700'
                  variant='outline'
                >
                  {version.is_default ? (
                    <span className='flex items-center gap-1'>
                      <span className='h-2 w-2 rounded-full bg-green-500'></span>
                      Default
                    </span>
                  ) : (
                    "Set default"
                  )}
                </Button>
              )}
            </div>
            <div className='flex items-center gap-2'>
              <InputsDrawer />
              <CallParamsDrawer />
              <Tooltip>
                <TooltipTrigger asChild>
                  <span>
                    <Button
                      name='run'
                      loading={runMutation.isPending}
                      disabled={!doesProviderExist}
                      className='bg-green-600 hover:bg-green-700 text-white font-medium'
                    >
                      Run
                    </Button>
                  </span>
                </TooltipTrigger>
                <TooltipContent className='bg-gray-700 text-white'>
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
          <div className='lexical min-w-[500px]'>
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
          {renderBottomPanel()}
        </div>
      </form>
    </Form>
  );
};

const CallParamsDrawer = () => {
  const methods = useFormContext<EditorParameters>();
  const handleClick = () => {
    methods.reset();
  };
  return (
    <Sheet>
      <SheetTrigger asChild>
        <Button
          className='border border-gray-300 bg-white hover:bg-gray-100 text-gray-700'
          variant='outline'
        >
          Configure Call Params
        </Button>
      </SheetTrigger>
      <SheetContent>
        <SheetHeader>
          <SheetTitle>Call Params</SheetTitle>
        </SheetHeader>
        <BaseEditorFormFields />
        <SheetFooter>
          <Button variant='outline' onClick={handleClick}>
            Reset to default
          </Button>
        </SheetFooter>
      </SheetContent>
    </Sheet>
  );
};

const InputsDrawer = () => {
  const methods = useFormContext<EditorParameters>();
  const { fields, append, remove } = useFieldArray<EditorParameters>({
    control: methods.control,
    name: "inputs",
  });
  const types = ["str", "int", "float", "bool", "bytes", "list", "dict"];
  return (
    <Sheet>
      <SheetTrigger asChild>
        <Button
          className='border border-gray-300 bg-white hover:bg-gray-100 text-gray-700'
          variant='outline'
        >
          Inputs
        </Button>
      </SheetTrigger>
      <SheetContent className='sm:max-w-xl md:max-w-2xl overflow-y-auto'>
        <SheetHeader>
          <SheetTitle>Inputs</SheetTitle>
        </SheetHeader>
        <div className='space-y-2'>
          <div className='flex gap-4 flex-wrap pb-4'>
            {fields.map((field, index) => {
              const type = methods.watch(`inputs.${index}.type`);
              return (
                <Card key={field.id} className='w-full flex-shrink-0 relative'>
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
                    <div className='w-full flex gap-2'>
                      <FormField
                        control={methods.control}
                        name={`inputs.${index}.type`}
                        render={({ field }) => (
                          <FormItem>
                            <FormLabel>Type</FormLabel>

                            <FormControl>
                              <Select
                                value={field.value}
                                onValueChange={field.onChange}
                              >
                                <SelectTrigger className='w-full'>
                                  <SelectValue placeholder='Select input type' />
                                </SelectTrigger>
                                <SelectContent>
                                  {types.map((type) => (
                                    <SelectItem key={type} value={type}>
                                      {type}
                                    </SelectItem>
                                  ))}
                                </SelectContent>
                              </Select>
                            </FormControl>
                            <FormMessage />
                          </FormItem>
                        )}
                      />
                      <TypedInput<EditorParameters>
                        control={methods.control}
                        name={`inputs.${index}.value`}
                        type={type}
                      />
                    </div>
                  </CardContent>
                </Card>
              );
            })}
            <AddCardButton
              className='w-full'
              onClick={() => append({ key: "", type: "str", value: "" })}
            />
          </div>
        </div>
        <SheetFooter>
          <SheetClose asChild>
            <Button variant='outline'>Close</Button>
          </SheetClose>
        </SheetFooter>
      </SheetContent>
    </Sheet>
  );
};
