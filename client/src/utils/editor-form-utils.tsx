import { FormCombobox } from "@/components/FormCombobox";
import { FormSlider } from "@/components/FormSlider";
import {
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ModelCombobox } from "@/components/ui/model-combobox";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import {
  PromptCreate,
  AnthropicCallParams,
  OpenAICallParams,
  GeminiCallParams,
  ResponseFormat,
  VersionPublic,
} from "@/types/types";
import { Provider } from "@/types/enums";
import { useEffect } from "react";
import {
  Control,
  Controller,
  Path,
  UseFormReturn,
  useForm,
  DefaultValues,
} from "react-hook-form";
export type OptionalField<T> = {
  enabled: boolean;
  value: T;
};

export type WithOptionalFields<T> = {
  [K in keyof T]: T[K] extends object
    ? WithOptionalFields<T[K]>
    : undefined extends T[K]
      ? {
          enabled: boolean;
          value: NonNullable<T[K]>;
        }
      : T[K];
};

export type EditorFormValues = PromptCreate & {
  openaiCallParams: WithOptionalFields<OpenAICallParams>;
  anthropicCallParams: WithOptionalFields<AnthropicCallParams>;
  geminiCallParams: WithOptionalFields<GeminiCallParams>;
};

function getDefaultValueForType(value: unknown): unknown {
  if (typeof value === "string") return "";
  if (typeof value === "number") return 0;
  if (typeof value === "boolean") return false;
  if (Array.isArray(value)) return [];
  if (typeof value === "object") return {};
  return null;
}

export function apiToFormValues<T extends object>(
  apiData: T
): WithOptionalFields<T> {
  const result = {} as WithOptionalFields<T>;

  for (const key in apiData) {
    const currentKey = key as keyof T;
    const value = apiData[currentKey];

    // Check if the value can be null/undefined
    if (value === null || value === undefined) {
      result[currentKey] = {
        enabled: false,
        value: getDefaultValueForType(value),
      } as WithOptionalFields<T>[keyof T];
    } else {
      result[currentKey] = value as WithOptionalFields<T>[keyof T];
    }
  }

  return result;
}

interface SliderConfig {
  label: string;
  sliderProps: {
    name: string;
    min: number;
    max: number;
    step: number;
  };
  inputProps?: {
    step?: number;
    className?: string;
  };
}

export const SLIDER_CONFIGS: Record<string, SliderConfig> = {
  maxTokens: {
    label: "Max Tokens",
    sliderProps: {
      name: "maxTokens",
      min: 1,
      max: 4095,
      step: 1,
    },
    inputProps: {
      step: 1,
      className: "w-[100px] h-[1.5rem]",
    },
  },
  temperature: {
    label: "Temperature",
    sliderProps: {
      name: "temperature",
      min: 0,
      max: 2,
      step: 0.01,
    },
    inputProps: {
      step: 0.01,
      className: "w-[100px] h-[1.5rem]",
    },
  },
  topK: {
    label: "Top K",
    sliderProps: {
      name: "topK",
      min: 0,
      max: 100,
      step: 1,
    },
    inputProps: {
      step: 1,
      className: "w-[100px] h-[1.5rem]",
    },
  },
  topP: {
    label: "Top P",
    sliderProps: {
      name: "topP",
      min: 0,
      max: 1,
      step: 0.01,
    },
    inputProps: {
      step: 0.01,
      className: "w-[100px] h-[1.5rem]",
    },
  },
  frequencyPenalty: {
    label: "Frequency Penalty",
    sliderProps: {
      name: "frequencyPenalty",
      min: 0,
      max: 2,
      step: 0.01,
    },
    inputProps: {
      step: 0.01,
      className: "w-[100px] h-[1.5rem]",
    },
  },
  presencePenalty: {
    label: "Presence Penalty",
    sliderProps: {
      name: "presencePenalty",
      min: 0,
      max: 2,
      step: 0.01,
    },
    inputProps: {
      step: 0.01,
      className: "w-[100px] h-[1.5rem]",
    },
  },
} as const;

export function createFormSlider<T extends object>(
  control: Control<T>,
  sliderKey: keyof typeof SLIDER_CONFIGS
) {
  return function renderSlider(name: Path<T>, enabled?: Path<T>) {
    const config = SLIDER_CONFIGS[sliderKey];
    const isOptional = !!enabled;
    return (
      <FormSlider<T>
        key={`editor-${sliderKey}`}
        control={control}
        name={name}
        label={config.label}
        sliderProps={config.sliderProps}
        showInput={true}
        inputProps={config.inputProps}
        {...(isOptional && {
          switchName: enabled,
          optional: true,
        })}
      />
    );
  };
}

export const anthropicCallParamsDefault: WithOptionalFields<AnthropicCallParams> =
  {
    max_tokens: 1024,
    temperature: 1.0,
    stop_sequences: {
      enabled: false,
      value: [],
    },
    top_k: {
      enabled: false,
      value: 0,
    },
    top_p: {
      enabled: false,
      value: 0,
    },
  };
export const openaiCallParamsDefault: WithOptionalFields<OpenAICallParams> = {
  response_format: {
    type: "text",
  },
  temperature: 1,
  max_tokens: 2048,
  top_p: 1,
  frequency_penalty: {
    enabled: false,
    value: 0,
  },
  presence_penalty: {
    enabled: false,
    value: 0,
  },
};
export const geminiCallParamsDefault: WithOptionalFields<GeminiCallParams> = {
  response_mime_type: "text/plain",
  max_output_tokens: {
    enabled: false,
    value: 1024,
  },
  temperature: {
    enabled: false,
    value: 0,
  },
  top_p: {
    enabled: false,
    value: 0,
  },
  top_k: {
    enabled: false,
    value: 0,
  },
  frequency_penalty: {
    enabled: false,
    value: 0,
  },
  presence_penalty: {
    enabled: false,
    value: 0,
  },
  response_schema: {
    enabled: false,
    value: {},
  },
};

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
export const getModelOptions = (provider: Provider) => {
  return modelOptions[provider] || [];
};

export const geminiResponseMimeType = (control: Control<EditorFormValues>) => {
  return (
    <FormField
      key='editor-response-mime-type'
      name='geminiCallParams.response_mime_type'
      control={control}
      render={({ field }) => (
        <FormItem>
          <FormLabel>Response Mime Type</FormLabel>
          <FormControl>
            <Input {...field} placeholder='Enter value' />
          </FormControl>
          <FormMessage />
        </FormItem>
      )}
    />
  );
};

export const openaiResponseFormat = (control: Control<EditorFormValues>) => {
  const responseFormatTypes: ResponseFormat["type"][] = [
    "text",
    "json_object",
    "json_schema",
  ];
  return (
    <div key='editor-response-format' className='form-group'>
      <Label htmlFor='response-format'>Response Format</Label>
      <Controller
        name={"openaiCallParams.response_format.type"}
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
export const renderStopSequences = (
  method: UseFormReturn<EditorFormValues, any, undefined>,
  name: Path<EditorFormValues>,
  enabled?: Path<EditorFormValues>,
  maxItems: number = 5
) => {
  const isOptional = !!enabled;
  let stopSequences: string[] = [];
  const value = method.watch(name);
  if (Array.isArray(value)) {
    stopSequences = value;
  }

  return (
    <FormField
      key='editor-stop-sequences'
      control={method.control}
      name={name}
      render={() => (
        <FormItem>
          <FormLabel className='flex items-center gap-2'>
            Stop Sequences
            {isOptional && (
              <Controller
                name={enabled}
                control={method.control}
                render={({ field: switchField }) => (
                  <div className='flex items-center gap-2'>
                    <FormControl>
                      <Switch
                        checked={!!switchField.value}
                        onCheckedChange={switchField.onChange}
                      />
                    </FormControl>
                    <span className='text-xs'>
                      {switchField.value ? "Active" : "Not set"}
                    </span>
                  </div>
                )}
              />
            )}
          </FormLabel>
          <FormControl>
            <FormCombobox<EditorFormValues>
              items={stopSequences.map((str) => ({
                value: str,
                label: str,
              }))}
              control={method.control}
              name={name}
              popoverText='Add stop sequences...'
              helperText='Enter a stop sequence'
              disabled={enabled && !method.watch(enabled)}
            />
          </FormControl>
          <FormDescription>
            {`Add stop sequences to control where the model stops generating (max: ${maxItems})`}
          </FormDescription>
        </FormItem>
      )}
    />
  );
};

export const useBaseEditorForm = <T extends EditorFormValues>({
  latestVersion,
  additionalDefaults = {},
}: {
  latestVersion?: VersionPublic | null;
  additionalDefaults?: Partial<T>;
}) => {
  const methods = useForm<T>({
    defaultValues: {
      ...getDefaultValues<T>(latestVersion),
      ...additionalDefaults,
    },
  });

  const { reset } = methods;

  useEffect(() => {
    const newValues = {
      ...getDefaultValues<T>(latestVersion),
      ...additionalDefaults,
    };
    reset(newValues);
  }, [latestVersion, reset]);

  return methods;
};

const getDefaultValues = <T extends EditorFormValues>(
  latestVersion?: VersionPublic | null
): DefaultValues<T> => {
  if (!latestVersion) {
    return {
      provider: Provider.OPENAI,
      model: "gpt-4o",
      openaiCallParams: openaiCallParamsDefault,
      geminiCallParams: geminiCallParamsDefault,
      anthropicCallParams: anthropicCallParamsDefault,
    } as DefaultValues<T>;
  }

  return {
    ...latestVersion.prompt,
    openaiCallParams:
      latestVersion.prompt?.provider === Provider.OPENAI ||
      latestVersion.prompt?.provider === Provider.OPENROUTER
        ? apiToFormValues(latestVersion.prompt.call_params as OpenAICallParams)
        : openaiCallParamsDefault,
    anthropicCallParams:
      latestVersion.prompt?.provider === Provider.ANTHROPIC
        ? apiToFormValues(
            latestVersion.prompt.call_params as AnthropicCallParams
          )
        : anthropicCallParamsDefault,
    geminiCallParams:
      latestVersion.prompt?.provider === Provider.GEMINI
        ? apiToFormValues(latestVersion.prompt.call_params as GeminiCallParams)
        : geminiCallParamsDefault,
  } as DefaultValues<T>;
};

export const BaseEditorFormFields = ({
  methods,
}: {
  methods: UseFormReturn<EditorFormValues, any, undefined>;
}) => {
  const { control, getValues, resetField, watch } = methods;

  const provider = watch("provider");
  useEffect(() => {
    let model = "gpt-4o";
    if (provider === Provider.ANTHROPIC) {
      model = "claude-3-5-sonnet-latest";
    } else if (provider === Provider.GEMINI) {
      model = "gemini-1.5-flash";
    } else if (provider === Provider.OPENROUTER) {
      model = "openai/chatgpt-4o-latest";
    }

    resetField("model", { defaultValue: model });
  }, [provider, methods.resetField]);

  const renderSliders = {
    maxTokens: createFormSlider(control, "maxTokens"),
    temperature: createFormSlider(control, "temperature"),
    topK: createFormSlider(control, "topK"),
    topP: createFormSlider(control, "topP"),
    frequencyPenalty: createFormSlider(control, "frequencyPenalty"),
    presencePenalty: createFormSlider(control, "presencePenalty"),
  };

  const openaiParams = [
    renderSliders.maxTokens("openaiCallParams.max_tokens"),
    openaiResponseFormat(control),
    renderSliders.temperature("openaiCallParams.temperature"),
    renderSliders.topP("openaiCallParams.top_p"),
    renderSliders.frequencyPenalty("openaiCallParams.frequency_penalty"),
    renderSliders.presencePenalty("openaiCallParams.presence_penalty"),
    renderStopSequences(
      methods,
      "openaiCallParams.stop.value",
      "openaiCallParams.stop.enabled",
      4
    ),
  ];
  const anthropicParams = [
    renderSliders.maxTokens("anthropicCallParams.max_tokens"),
    renderSliders.temperature("anthropicCallParams.temperature"),
    renderSliders.topP(
      "anthropicCallParams.top_p.value",
      "anthropicCallParams.top_p.enabled"
    ),
    renderSliders.topK(
      "anthropicCallParams.top_k.value",
      "anthropicCallParams.top_k.enabled"
    ),
    renderStopSequences(
      methods,
      "anthropicCallParams.stop_sequences.value",
      "anthropicCallParams.stop_sequences.enabled",
      5
    ),
  ];
  const geminiParams = [
    renderSliders.maxTokens(
      "geminiCallParams.max_output_tokens.value",
      "geminiCallParams.max_output_tokens.enabled"
    ),
    geminiResponseMimeType(control),
    renderSliders.temperature(
      "geminiCallParams.temperature.value",
      "geminiCallParams.temperature.enabled"
    ),
    renderSliders.topP(
      "geminiCallParams.top_p.value",
      "geminiCallParams.top_p.enabled"
    ),
    renderSliders.topK(
      "geminiCallParams.top_k.value",
      "geminiCallParams.top_k.enabled"
    ),
    renderSliders.frequencyPenalty("geminiCallParams.frequency_penalty.value"),
    renderSliders.presencePenalty("geminiCallParams.presence_penalty.enabled"),
  ];
  return (
    <div className='w-full max-w-sm flex flex-col gap-3'>
      <FormField
        key='editor-response-mime-type'
        control={methods.control}
        name='provider'
        render={({ field }) => (
          <FormItem>
            <FormLabel>Provider</FormLabel>
            <FormControl>
              <Select value={field.value} onValueChange={field.onChange}>
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
            </FormControl>
            <FormMessage />
          </FormItem>
        )}
      />
      <ModelCombobox<EditorFormValues, "model">
        control={control}
        name='model'
        label='Choose a Model'
        options={getModelOptions(provider)}
        defaultValue={getValues("model")}
      />
      {provider === Provider.OPENAI || provider === Provider.OPENROUTER
        ? openaiParams
        : provider === Provider.ANTHROPIC
          ? anthropicParams
          : provider === Provider.GEMINI
            ? geminiParams
            : null}
    </div>
  );
};

export const formValuesToApi = (obj) => {
  // For each property that has an 'enabled' field
  for (const key of Object.keys(obj)) {
    const param = obj[key];
    if (param && typeof param === "object" && "enabled" in param) {
      if (param.enabled) {
        // If enabled is true, replace the object with its value
        (obj as any)[key] = param.value;
      } else {
        // If enabled is false, delete the property
        delete (obj as any)[key];
      }
    }
  }

  return obj;
};
