import { Editor } from "@/components/Editor";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { ForwardedRef, forwardRef, useEffect, useRef } from "react";
import { Button } from "@/components/ui/button";
import { Controller, SubmitHandler, useForm, useWatch } from "react-hook-form";
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
import { FormSlider } from "@/components/FormSlider";

interface EditorFormProps {
  latestVersion?: VersionPublic | null;
  llmFunction: LLMFunctionBasePublic;
  onSubmit: SubmitHandler<CallArgsCreate>;
  editorErrors: string[];
  formButtons?: React.ReactNode[];
}
export const EditorForm = forwardRef(
  (
    {
      latestVersion,
      llmFunction,
      onSubmit,
      editorErrors,
      formButtons,
    }: EditorFormProps,
    ref: ForwardedRef<LexicalEditor>
  ) => {
    const isInitialRender = useRef<boolean>(true);
    const { control, handleSubmit, setValue, getValues } =
      useForm<CallArgsCreate>({
        defaultValues: {
          provider:
            latestVersion && latestVersion.fn_params
              ? latestVersion.fn_params.provider
              : Provider.OPENAI,
          model:
            latestVersion && latestVersion.fn_params
              ? latestVersion.fn_params.model
              : "",
          call_params:
            latestVersion && latestVersion.fn_params
              ? latestVersion.fn_params.call_params
              : {
                  response_format: {
                    type: "text",
                  },
                  temperature: 1,
                  max_tokens: 2048,
                  top_p: 1,
                  frequency_penalty: 0,
                  presence_penalty: 0,
                },
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
    const responseFormatTypes: ResponseFormat["type"][] = [
      "text",
      "json_object",
      "json_schema",
    ];
    const inputs = llmFunction.arg_types
      ? Object.keys(JSON.parse(llmFunction.arg_types))
      : [];
    return (
      <div className='flex flex-col gap-2'>
        <form onSubmit={handleSubmit(onSubmit)}>
          <div className='flex gap-2'>
            <div className='lexical form-group'>
              <Label htmlFor='prompt-template'>Prompt Template</Label>
              <Editor
                inputs={inputs}
                ref={ref}
                promptTemplate={
                  (latestVersion &&
                    latestVersion.fn_params &&
                    latestVersion.fn_params.prompt_template) ||
                  ""
                }
              />
              {editorErrors.length > 0 &&
                editorErrors.map((error, i) => (
                  <div key={i} className='text-red-500 text-sm mt-1'>
                    {error}
                  </div>
                ))}
            </div>
            <div className='w-full max-w-sm flex flex-col gap-3'>
              <div className='form-group'>
                <Label htmlFor='provider'>Provider</Label>
                <Controller
                  name='provider'
                  control={control}
                  render={({ field }) => (
                    <Select value={field.value} onValueChange={field.onChange}>
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
              <div className='form-group'>
                <ModelCombobox<CallArgsCreate, "model">
                  control={control}
                  name='model'
                  label='Choose a Model'
                  options={options}
                  defaultValue={getValues("model")}
                />
              </div>
              <div className='form-group'>
                <Label htmlFor='response-format'>Response Format</Label>
                <Controller
                  name='call_params.response_format.type'
                  control={control}
                  render={({ field }) => (
                    <Select value={field.value} onValueChange={field.onChange}>
                      <SelectTrigger className='w-full'>
                        <SelectValue placeholder='Select a response format' />
                      </SelectTrigger>
                      <SelectContent>
                        {responseFormatTypes.map((type) => (
                          <SelectItem key={type} value={type}>
                            {type}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  )}
                />
              </div>
              <FormSlider<CallArgsCreate>
                {...{
                  control,
                  name: "call_params.max_tokens",
                  label: "Max Tokens",
                  sliderProps: {
                    name: "max-tokens",
                    min: 1,
                    max: 4095,
                    step: 1,
                  },
                  showInput: true,
                  inputProps: { step: 1, className: "w-[100px] h-[1.5rem]" },
                }}
              />
              <FormSlider<CallArgsCreate>
                {...{
                  control,
                  name: "call_params.temperature",
                  label: "Temperature",
                  sliderProps: {
                    name: "temperature",
                    min: 0,
                    max: 2,
                    step: 0.01,
                  },
                  showInput: true,
                  inputProps: { step: 0.01, className: "w-[100px] h-[1.5rem]" },
                }}
              />
              <FormSlider<CallArgsCreate>
                {...{
                  control,
                  name: "call_params.top_p",
                  label: "Top P",
                  sliderProps: {
                    name: "top-p",
                    min: 0,
                    max: 1,
                    step: 0.01,
                  },
                  showInput: true,
                  inputProps: { step: 0.01, className: "w-[100px] h-[1.5rem]" },
                }}
              />
              <FormSlider<CallArgsCreate>
                {...{
                  control,
                  name: "call_params.frequency_penalty",
                  label: "Frequency Penalty",
                  sliderProps: {
                    name: "frequency-penalty",
                    min: 0,
                    max: 2,
                    step: 0.01,
                  },
                  showInput: true,
                  inputProps: { step: 0.01, className: "w-[100px] h-[1.5rem]" },
                }}
              />
              <FormSlider<CallArgsCreate>
                {...{
                  control,
                  name: "call_params.presence_penalty",
                  label: "Presence Penalty",
                  sliderProps: {
                    name: "presence-penalty",
                    min: 0,
                    max: 2,
                    step: 0.01,
                  },
                  showInput: true,
                  inputProps: { step: 0.01, className: "w-[100px] h-[1.5rem]" },
                }}
              />
            </div>
          </div>
          <div className='button-group'>
            <Button type='submit' name='create-version'>
              Create version
            </Button>
            {formButtons && formButtons.map((button) => button)}
          </div>
        </form>
      </div>
    );
  }
);
