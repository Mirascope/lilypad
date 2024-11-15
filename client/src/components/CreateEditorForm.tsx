import { Editor } from "@/components/Editor";

import { useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { SubmitHandler, useFieldArray } from "react-hook-form";
import { Label } from "@/components/ui/label";
import { LexicalEditor } from "lexical";
import {
  BaseEditorFormFields,
  EditorFormValues,
  formValuesToApi,
  useBaseEditorForm,
} from "@/utils/editor-form-utils";
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
  useCreateVersion,
  usePatchActiveVersion,
  useRunMutation,
} from "@/utils/versions";
import {
  FunctionCreate,
  PromptCreate,
  Provider,
  OpenAICallParams,
  AnthropicCallParams,
  GeminiCallParams,
  VersionPublic,
} from "@/types/types";
import { NotFound } from "@/components/NotFound";
import IconDialog from "@/components/IconDialog";
import { CodeSnippet } from "@/components/CodeSnippet";
import { Typography } from "@/components/ui/typography";
import ReactMarkdown from "react-markdown";

type CreateEditorFormValues = EditorFormValues & {
  inputs: Record<string, string>[];
};
export const CreateEditorForm = ({
  version,
}: {
  version: VersionPublic | null;
}) => {
  const { projectId: strProjectId, functionName } = useParams({
    strict: false,
  });
  const projectId = Number(strProjectId);
  const navigate = useNavigate();
  const createVersionMutation = useCreateVersion();
  const patchActiveVersionMutation = usePatchActiveVersion();
  const runMutation = useRunMutation();
  const methods = useBaseEditorForm<CreateEditorFormValues>({
    additionalDefaults: {
      inputs: version?.function.arg_types
        ? Object.keys(version.function.arg_types).map((key) => ({
            key,
            value: "",
          }))
        : [],
    },
  });
  const { fields, append, remove } = useFieldArray<CreateEditorFormValues>({
    control: methods.control,
    name: "inputs",
  });
  const inputs: Record<string, string>[] = methods.watch("inputs");
  const [editorErrors, setEditorErrors] = useState<string[]>([]);
  const editorRef = useRef<LexicalEditor>(null);

  if (!projectId || !functionName) return <NotFound />;
  const onSubmit: SubmitHandler<CreateEditorFormValues> = (
    data: CreateEditorFormValues,
    event
  ) => {
    event?.preventDefault();
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
      methods.trigger();
      const functionCreate: FunctionCreate = {
        name: functionName,
        arg_types: inputs.reduce(
          (acc, input) => {
            acc[input.key] = "str";
            return acc;
          },
          {} as Record<string, string>
        ),
        hash: null,
        code: null,
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
        const isValid = await methods.trigger();
        if (!isValid) return;
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
        const inputValues = inputs.reduce(
          (acc, input) => {
            acc[input.key] = input.value;
            return acc;
          },
          {} as Record<string, string>
        );

        runMutation.mutateAsync({
          projectId,
          versionId: newVersion.id,
          values: inputValues,
        });
      } catch (error) {
        console.error(error);
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
                      rules={{ required: "Value is required" }}
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Type</FormLabel>
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
  if (version && !version.prompt) {
    return (
      <div className='flex flex-col justify-center items-center h-screen'>
        {"Playground is unavailable for non-synced calls"}
      </div>
    );
  }
  const code = `import lilypad


${version?.function.code || ""}

if __name__ == "__main__":
    lilypad.configure()
    output = ${version?.function.name}(${inputs.map((item) => `"${item.value}"`).join(", ")})
    print(output)
  `;
  return (
    <div className='m-auto w-[1200px] p-4'>
      <Form {...methods}>
        <form onSubmit={methods.handleSubmit(onSubmit)}>
          <div className='flex justify-between'>
            <div className='flex items-center gap-2'>
              <Typography variant='h3'>{functionName}</Typography>
              {version && (
                <Button
                  disabled={
                    version.is_active || patchActiveVersionMutation.isPending
                  }
                  onClick={() =>
                    patchActiveVersionMutation.mutate({
                      projectId,
                      versionId: version.id,
                    })
                  }
                >
                  {version.is_active ? "Active" : "Set active"}
                </Button>
              )}
            </div>
            <div className='flex items-center gap-2'>
              {version && (
                <IconDialog
                  text='Code'
                  title='Copy Code'
                  description='Copy this codeblock into your application.'
                >
                  <CodeSnippet code={code} />
                </IconDialog>
              )}
              <Button type='submit' name='run' loading={runMutation.isPending}>
                {version ? "Run" : "Create"}
              </Button>
            </div>
          </div>
          <div className='flex gap-4'>
            <div className='lexical form-group space-y-2 w-[600px]'>
              <Label htmlFor='prompt-template'>Prompt Template</Label>
              <Editor
                inputs={inputs.map((input) => input.key)}
                ref={editorRef}
                promptTemplate={
                  (version && version.prompt && version.prompt.template) || ""
                }
              />
              {editorErrors.length > 0 &&
                editorErrors.map((error, i) => (
                  <div key={i} className='text-red-500 text-sm mt-1'>
                    {error}
                  </div>
                ))}
            </div>
            {/* @ts-ignore */}
            <BaseEditorFormFields methods={methods} />
          </div>
          {renderBottomPanel()}
        </form>
      </Form>
    </div>
  );
};
