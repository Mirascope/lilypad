import { createLazyFileRoute } from "@tanstack/react-router";
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
import { CallArgsCreate, Provider } from "@/types/types";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { ModelCombobox } from "@/components/ui/model-combobox";
import { Textarea } from "@/components/ui/textarea";
import { LexicalEditor } from "lexical";

export const Route = createLazyFileRoute("/editor")({
  component: () => <EditorContainer />,
});

const EditorContainer = () => {
  const queryClient = useQueryClient();
  const mutation = useMutation({
    mutationFn: (callArgsCreate: CallArgsCreate) => {
      return api.patch(`/${1}`, callArgsCreate);
    },
    onSuccess: () => {
      // Invalidate and refetch
      queryClient.invalidateQueries({ queryKey: ["todos"] });
    },
  });
  const [callParams, setCallParams] = useState<string>("");
  const editorRef = useRef<LexicalEditor>(null);
  const { control, handleSubmit, setValue, clearErrors, setError, getValues } =
    useForm<CallArgsCreate>({
      defaultValues: {
        provider: Provider.OPENAI,
        model: "",
        call_params: {},
      },
    });

  const provider = useWatch({
    control,
    name: "provider",
  });

  useEffect(() => {
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
      console.log(data);
      mutation.mutate(data);
    });
  };
  return (
    <form onSubmit={handleSubmit(onSubmit)} className='p-2'>
      <div className='flex gap-2'>
        <div className='lexical flex flex-col'>
          <Editor inputs={[]} ref={editorRef} />
        </div>
        <div id='call-args'>
          <div className='grid w-full max-w-sm items-center gap-1.5'>
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
              <ModelCombobox<CallArgsCreate>
                control={control}
                name='model'
                label='Choose a Model'
                options={options}
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
      </div>
      <Button type='submit' className='mt-2'>
        Submit
      </Button>
    </form>
  );
};
