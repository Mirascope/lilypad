import {
  createFileRoute,
  useLoaderData,
  useMatch,
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
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import api from "@/api";
import { CallArgsCreate, LLMFunctionBasePublic, Provider } from "@/types/types";
import { Label } from "@/components/ui/label";
import { ModelCombobox } from "@/components/ui/model-combobox";
import { Textarea } from "@/components/ui/textarea";
import { LexicalEditor } from "lexical";
import { Typography } from "@/components/ui/typography";
import { InputsCards } from "@/components/InputsCards";

type LoaderData = {
  llmFunction: LLMFunctionBasePublic;
  providerCallParams: CallArgsCreate;
};

export const Route = createFileRoute(
  "/llmFunctions/$llmFunctionId/providerCallParams"
)({
  loader: async ({ params: { llmFunctionId } }): Promise<LoaderData> => {
    const [llmFunction, providerCallParams] = await Promise.all([
      api.get<LLMFunctionBasePublic>(`/llm-functions/${llmFunctionId}`),
      api.get<CallArgsCreate>(
        `/llm-functions/${Number(llmFunctionId)}/provider-call-params`
      ),
    ]);
    return {
      llmFunction: llmFunction.data,
      providerCallParams: providerCallParams.data,
    };
  },
  pendingComponent: () => <div>Loading...</div>,
  errorComponent: ({ error }) => <div>{error.message}</div>,
  component: () => <EditorContainer />,
});

const EditorContainer = () => {
  const { llmFunction, providerCallParams } = useLoaderData({
    from: Route.id,
  });
  const queryClient = useQueryClient();
  const mutation = useMutation({
    mutationFn: (callArgsCreate: CallArgsCreate) => {
      return api.post(
        `/llm-functions/${llmFunction.id}/provider-call-params`,
        callArgsCreate
      );
    },
    onSuccess: () => {
      // Invalidate and refetch
      queryClient.invalidateQueries({
        queryKey: [`llmFunctions-${llmFunction.id}-providerCallParams`],
      });
    },
  });

  const [callParams, setCallParams] = useState<string>("");
  const isInitialRender = useRef<boolean>(true);
  const editorRef = useRef<LexicalEditor>(null);
  const { control, handleSubmit, setValue, clearErrors, setError, getValues } =
    useForm<CallArgsCreate>({
      defaultValues: {
        provider: providerCallParams.provider,
        model: providerCallParams.model || "foo",
        call_params: providerCallParams.call_params,
      },
    });
  const provider = useWatch({
    control,
    name: "provider",
  });

  useEffect(() => {
    if (isInitialRender.current) {
      isInitialRender.current = false;
      return;
    }
    setValue("model", "");
  }, [provider]);

  const modelOptions = {
    [Provider.OPENAI]: [
      { value: "gpt-4o", label: "GPT-4o" },
      { value: "gpt-4o-mini", label: "GPT-4o-mini" },
      { value: "o1-preview", label: "o1-preview" },
      { value: "o1-mini", label: "o1-mini" },
      { value: "gpt-4-turbo", label: "GPT-4 Turbo" },
      { value: "gpt-3.5-turbo", label: "GPT-3.5 Turbo" },
    ],
    [Provider.ANTHROPIC]: [
      { value: "claude-3-5-sonnet-20240620", label: "Claude 3.5 Sonnet" },
      { value: "claude-3-opus-20240229", label: "Claude 3 Opus" },
      { value: "claude-3-sonnet-20240229", label: "Claude 3 Sonnet" },
      { value: "claude-3-haiku-20240307", label: "Claude 3 Haiku" },
    ],
  };

  const options = modelOptions[provider] || [];
  const onSubmit = (data: CallArgsCreate) => {
    if (!editorRef?.current) return;
    const editorState = editorRef.current.getEditorState();
    editorState.read(() => {
      const markdown = $convertToMarkdownString(PLAYGROUND_TRANSFORMERS);
      data.prompt_template = markdown;
      data.editor_state = JSON.stringify(editorState);
      mutation.mutate(data);
      window.close();
    });
  };
  const inputs = llmFunction.input_arguments
    ? Object.keys(JSON.parse(llmFunction.input_arguments))
    : [];
  return (
    <div className='p-2 flex flex-col gap-2'>
      <Typography variant='h3'>{llmFunction.function_name}</Typography>
      {llmFunction.input_arguments && (
        <div className='flex'>
          <InputsCards inputValues={JSON.parse(llmFunction.input_arguments)} />
        </div>
      )}
      <form onSubmit={handleSubmit(onSubmit)}>
        <div className='flex gap-2'>
          <div className='lexical form-group'>
            <Label htmlFor='prompt-template'>Prompt Template</Label>
            <Editor
              inputs={inputs}
              ref={editorRef}
              editorState={providerCallParams.editor_state}
            />
          </div>
          <div className='w-full max-w-sm gap-1.5'>
            <div className='form-group'>
              <Label htmlFor='provider'>Provider</Label>
              <Controller
                name='provider'
                control={control}
                render={({ field }) => (
                  <Select
                    value={field.value}
                    onValueChange={field.onChange}
                    // You can include additional props here
                  >
                    <SelectTrigger className='w-full'>
                      <SelectValue placeholder='Select a provider' />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value='openai'>OpenAI</SelectItem>
                      <SelectItem value='anthropic'>Anthropic</SelectItem>
                    </SelectContent>
                  </Select>
                )}
              />
            </div>
            {/* <div className='flex items-center space-x-2'>
                <Controller
                  name='json_mode'
                  control={control}
                  render={({ field }) => (
                    <Switch
                      checked={field.value === true}
                      onCheckedChange={field.onChange}
                    />
                  )}
                />
                <Label htmlFor='diff-view'>JSON Mode</Label>
              </div> */}
            <div className='form-group mt-4'>
              <ModelCombobox<CallArgsCreate, "model">
                control={control}
                name='model'
                label='Choose a Model'
                options={options}
                defaultValue={getValues("model")}
              />
            </div>
            <Controller
              name='call_params'
              control={control}
              rules={{
                validate: (value) => (value ? true : "Invalid JSON data"),
              }}
              render={({ field, fieldState: { error } }) => (
                <div className='form-group mt-4'>
                  <Label htmlFor='call_params'>Call Params</Label>
                  <Textarea
                    id='call_params'
                    value={callParams}
                    onChange={(e) => {
                      const inputValue = e.target.value;
                      setCallParams(inputValue);

                      try {
                        const parsedJson = JSON.parse(inputValue);
                        field.onChange(parsedJson); // Update form state with parsed object
                        clearErrors("call_params"); // Clear any previous errors
                      } catch (err) {
                        field.onChange(null); // Set form state to null if invalid
                        setError("call_params", {
                          type: "validate",
                          message: "Invalid JSON data",
                        });
                      }
                    }}
                    placeholder='{"key": "value"}'
                    rows={10}
                    className='w-full'
                  />
                  {error && (
                    <p className='text-red-500 text-sm mt-1'>{error.message}</p>
                  )}
                </div>
              )}
            />
          </div>
        </div>
        <Button type='submit' className='mt-2'>
          Submit
        </Button>
      </form>
    </div>
  );
};
