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
import {
  Controller,
  FormProvider,
  SubmitHandler,
  useForm,
  useWatch,
} from "react-hook-form";
import {
  CallArgsCreate,
  LLMFunctionPublic,
  Provider,
  VersionPublic,
  ResponseFormat,
  AnthropicCallArgsCreate,
  OpenAICallArgsCreate,
  GeminiCallArgsCreate,
} from "@/types/types";
import { Label } from "@/components/ui/label";
import { ModelCombobox } from "@/components/ui/model-combobox";
import { LexicalEditor } from "lexical";
import { FormSlider } from "@/components/FormSlider";
import { FormCombobox } from "@/components/FormCombobox";
import { Switch } from "@/components/ui/switch";
import { Input } from "@/components/ui/input";

interface EditorFormProps {
  latestVersion?: VersionPublic | null;
  llmFunction: LLMFunctionPublic;
  onSubmit: SubmitHandler<CallArgsCreate>;
  editorErrors: string[];
  formButtons?: React.ReactNode[];
}

type CallArgsCreateOptional = Record<string, boolean>;
export type EditorFormValues = CallArgsCreate & {
  isOptional?: CallArgsCreateOptional;
};

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
    const anthropicCallParamsDefault: AnthropicCallArgsCreate = {
      max_tokens: 1024,
      temperature: 1.0,
      stop_sequences: undefined,
      top_k: undefined,
      top_p: undefined,
    };
    const openaiCallParamsDefault: OpenAICallArgsCreate = {
      response_format: {
        type: "text",
      },
      temperature: 1,
      max_tokens: 2048,
      top_p: 1,
      frequency_penalty: 0,
      presence_penalty: 0,
    };
    const geminiCallParamsDefault: GeminiCallArgsCreate = {
      response_mime_type: "text/plain",
      max_output_tokens: undefined,
      temperature: undefined,
      top_p: undefined,
      top_k: undefined,
      frequency_penalty: undefined,
      presence_penalty: undefined,
      response_schema: undefined,
    };
    const methods = useForm<EditorFormValues>({
      defaultValues: latestVersion
        ? {
            ...latestVersion?.fn_params,
            call_params:
              latestVersion && latestVersion.fn_params
                ? latestVersion.fn_params.provider === Provider.OPENAI ||
                  latestVersion.fn_params.provider === Provider.OPENROUTER
                  ? openaiCallParamsDefault
                  : latestVersion.fn_params.provider === Provider.ANTHROPIC
                    ? anthropicCallParamsDefault
                    : latestVersion.fn_params.provider === Provider.GEMINI
                      ? geminiCallParamsDefault
                      : {}
                : {},
            isOptional: {},
          }
        : {
            provider: Provider.OPENAI,
            model: "gpt-4o",
            call_params: openaiCallParamsDefault,
          },
    });
    const { control, handleSubmit, getValues, reset } = methods;
    const provider = useWatch({
      control,
      name: "provider",
    });
    const isOptionalStopSequences = useWatch({
      control,
      name: "isOptional.stop_sequences",
    });
    useEffect(() => {
      if (isInitialRender.current) {
        isInitialRender.current = false;
        return;
      }
      if (provider === Provider.OPENAI) {
        reset({
          provider: Provider.OPENAI,
          model: "gpt-4o",
          call_params: openaiCallParamsDefault,
        });
      } else if (provider === Provider.ANTHROPIC) {
        reset({
          provider: Provider.ANTHROPIC,
          model: "claude-3-5-sonnet-20240620",
          call_params: anthropicCallParamsDefault,
        });
      } else if (provider === Provider.OPENROUTER) {
        reset({
          provider: Provider.OPENROUTER,
          model: "openai/chatgpt-4o-latest",
          call_params: openaiCallParamsDefault,
        });
      } else if (provider === Provider.GEMINI) {
        reset({
          provider: Provider.GEMINI,
          model: "gemini-1.5-flash",
          call_params: geminiCallParamsDefault,
        });
      }
    }, [provider, reset]);
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
        { value: "claude-3-5-sonnet-latest", label: "Claude 3.5 Sonnet (New)" },
        { value: "claude-3-5-sonnet-20240620", label: "Claude 3.5 Sonnet" },
        { value: "claude-3-opus-20240229", label: "Claude 3 Opus" },
        { value: "claude-3-sonnet-20240229", label: "Claude 3 Sonnet" },
        { value: "claude-3-haiku-20240307", label: "Claude 3 Haiku" },
      ],
      [Provider.OPENROUTER]: [
        { value: "openai/chatgpt-4o-latest", label: "GPT-4o" },
        { value: "openai/gpt-4o-mini", label: "GPT-4o-mini" },
        { value: "openai/o1-preview", label: "o1-preview" },
        { value: "openai/o1-mini", label: "o1-mini" },
        { value: "openai/gpt-4-turbo", label: "GPT-4 Turbo" },
        {
          value: "anthropic/claude-3.5-sonnet",
          label: "Claude 3.5 Sonnet",
        },
        { value: "anthropic/claude-3-opus", label: "Claude 3 Opus" },
        { value: "anthropic/claude-3-sonnet", label: "Claude 3 Sonnet" },
        { value: "anthropic/claude-3-haiku", label: "Claude 3 Haiku" },
      ],
      [Provider.GEMINI]: [
        {
          value: "gemini-1.5-flash",
          label: "Gemini 1.5 Flash",
        },
        { value: "gemini-1.5-flash-8b", label: "Gemini 1.5 Flash-8b" },
        { value: "gemini-1.5-pro", label: "Gemini 1.5 Pro" },
        { value: "gemini-1.0-pro", label: "Gemini 1.0 Pro" },
      ],
    };

    const options = modelOptions[provider] || [];

    const inputs = llmFunction.arg_types
      ? Object.keys(llmFunction.arg_types)
      : [];

    const renderMaxTokens = () => {
      let field = "max_tokens";
      if (provider === Provider.GEMINI) {
        field = "max_output_tokens";
      }
      return (
        <FormSlider<CallArgsCreate>
          key={`editor-${field}`}
          {...{
            control,
            name: `call_params.${field}`,
            label: "Max Tokens",
            sliderProps: {
              name: field,
              min: 1,
              max: 4095,
              step: 1,
            },
            showInput: true,
            inputProps: { step: 1, className: "w-[100px] h-[1.5rem]" },
          }}
        />
      );
    };
    const renderResponseFormat = () => {
      const responseFormatTypes: ResponseFormat["type"][] = [
        "text",
        "json_object",
        "json_schema",
      ];
      return (
        <div key='editor-response-format' className='form-group'>
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
      );
    };
    const renderTemperature = () => {
      return (
        <FormSlider<CallArgsCreate>
          key='editor-temperature'
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
      );
    };

    const renderTopP = (optional?: boolean) => {
      const field = "top_p";
      return (
        <FormSlider<CallArgsCreate>
          key={`editor-${field}`}
          {...{
            control,
            name: `call_params.${field}`,
            label: "Top P",
            ...(optional && { switchName: `isOptional.${field}`, optional }),
            sliderProps: {
              name: field,
              min: 0,
              max: 1,
              step: 0.01,
            },
            showInput: true,
            inputProps: { step: 0.01, className: "w-[100px] h-[1.5rem]" },
          }}
        />
      );
    };
    const renderTopK = (optional?: boolean) => {
      const field = "top_k";
      return (
        <FormSlider<CallArgsCreate>
          key={`editor-${field}`}
          {...{
            control,
            name: `call_params.${field}`,
            label: "Top K",
            ...(optional && { switchName: `isOptional.${field}`, optional }),
            sliderProps: {
              name: field,
              min: 0,
              max: 40,
              step: 1,
            },
            showInput: true,
            inputProps: { step: 0.01, className: "w-[100px] h-[1.5rem]" },
          }}
        />
      );
    };
    const renderStopSequences = (optional?: boolean) => {
      return (
        <div key='editor-stop-sequences' className='form-group'>
          <Label htmlFor='stop-sequences' className='flex items-center gap-2'>
            Stop Sequences
            {optional && (
              <>
                <Controller
                  name={"isOptional.stop_sequences"}
                  control={control}
                  render={({ field }) => (
                    <>
                      <Switch
                        checked={field.value}
                        onCheckedChange={field.onChange}
                      />
                      <p className='text-xs'>
                        {field.value ? "Active" : "Not set"}
                      </p>
                    </>
                  )}
                />
              </>
            )}
          </Label>
          <FormCombobox<CallArgsCreate>
            items={(getValues("call_params.stop_sequences") || []).map(
              (str) => ({ value: str, label: str })
            )}
            control={control}
            name='call_params.stop_sequences'
            popoverText='Add stop sequences...'
            helperText='Enter a stop sequence'
            disabled={!isOptionalStopSequences}
          />
        </div>
      );
    };
    const renderFrequencyPenalty = () => {
      return (
        <FormSlider<CallArgsCreate>
          key='editor-frequency-penalty'
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
      );
    };
    const renderPresencePenalty = () => {
      return (
        <FormSlider<CallArgsCreate>
          key='editor-presence-penalty'
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
      );
    };
    const renderResponseMimeType = () => {
      return (
        <div key='editor-response-mime-type' className='form-group'>
          <Label htmlFor='response-mime-type'>Response Mime Type</Label>
          <Controller
            name='call_params.response_mime_type'
            control={control}
            render={({ field }) => (
              <Input {...field} placeholder='Enter value' />
            )}
          />
        </div>
      );
    };
    const openaiParams = [
      renderMaxTokens(),
      renderResponseFormat(),
      renderTemperature(),
      renderTopP(),
      renderFrequencyPenalty(),
      renderPresencePenalty(),
    ];
    const anthropicParams = [
      renderMaxTokens(),
      renderTemperature(),
      renderStopSequences(true),
      renderTopP(true),
      renderTopK(true),
    ];
    const geminiParams = [
      renderMaxTokens(),
      renderTemperature(),
      renderTopP(),
      renderTopK(),
      renderResponseMimeType(),
      renderFrequencyPenalty(),
      renderPresencePenalty(),
    ];
    return (
      <div className='flex flex-col gap-2'>
        <FormProvider {...methods}>
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
                      <Select
                        value={field.value}
                        onValueChange={field.onChange}
                      >
                        <SelectTrigger className='w-full'>
                          <SelectValue placeholder='Select a provider' />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value='openai'>OpenAI</SelectItem>
                          <SelectItem value='anthropic'>Anthropic</SelectItem>
                          <SelectItem value='gemini'>Gemini</SelectItem>
                          <SelectItem value='openrouter'>OpenRouter</SelectItem>
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
                {provider === Provider.OPENAI ||
                provider === Provider.OPENROUTER
                  ? openaiParams
                  : provider === Provider.ANTHROPIC
                    ? anthropicParams
                    : provider === Provider.GEMINI
                      ? geminiParams
                      : null}
              </div>
            </div>
            <div className='button-group'>
              <Button type='submit' name='create-version'>
                Create version
              </Button>
              {formButtons && formButtons.map((button) => button)}
            </div>
          </form>
        </FormProvider>
      </div>
    );
  }
);
