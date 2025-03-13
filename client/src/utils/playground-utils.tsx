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
import { ModelCombobox } from "@/components/ui/model-combobox";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { PlaygroundParameters, Provider } from "@/ee/types/types";
import { CommonCallParams, GenerationPublic, UserPublic } from "@/types/types";
import { userQueryOptions } from "@/utils/users";
import { useSuspenseQuery } from "@tanstack/react-query";
import { useEffect } from "react";
import { DefaultValues, Path, useForm, useFormContext } from "react-hook-form";
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

export function createFormSlider(sliderKey: keyof typeof SLIDER_CONFIGS) {
  return function renderSlider<T extends object>(
    name: Path<T>,
    enabled?: Path<T>
  ) {
    const config = SLIDER_CONFIGS[sliderKey];
    const isOptional = !!enabled;

    return (
      <FormSlider<T>
        key={`editor-${sliderKey}`}
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

export const commonCallParamsDefault: CommonCallParams = {
  temperature: 1,
  max_tokens: 2048,
  top_p: 1,
  frequency_penalty: 0,
  presence_penalty: 0,
  seed: 0,
  stop: [],
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

export const renderStopSequences = (
  name: Path<PlaygroundParameters>,
  maxItems: number = 5
) => {
  const method = useFormContext<PlaygroundParameters>();
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
          </FormLabel>
          <FormControl>
            <FormCombobox<PlaygroundParameters>
              items={stopSequences.map((str) => ({
                value: str,
                label: str,
              }))}
              control={method.control}
              name={name}
              popoverText='Add stop sequences...'
              helperText='Enter a stop sequence'
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

export const useBaseEditorForm = <T extends PlaygroundParameters>({
  latestVersion,
  additionalDefaults = {},
}: {
  latestVersion?: GenerationPublic | null;
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

const getDefaultValues = <T extends PlaygroundParameters>(
  latestVersion?: GenerationPublic | null
): DefaultValues<T> => {
  if (!latestVersion) {
    return {
      provider: Provider.OPENAI,
      model: "gpt-4o",
      generation: {
        call_params: commonCallParamsDefault,
      },
    } as DefaultValues<T>;
  }
  if (
    !latestVersion.call_params ||
    Object.keys(latestVersion.call_params).length === 0
  ) {
    latestVersion.call_params = commonCallParamsDefault;
  }
  return {
    provider: Provider.OPENAI,
    model: "gpt-4o",
    generation: latestVersion,
  } as DefaultValues<T>;
};

const renderSeed = () => {
  const method = useFormContext<PlaygroundParameters>();
  return (
    <FormField
      key='editor-seed'
      control={method.control}
      name={"generation.call_params.seed"}
      render={({ field }) => (
        <FormItem>
          <FormLabel>Seed</FormLabel>
          <FormControl>
            <Input {...field} type='number' value={field.value ?? ""} />
          </FormControl>
        </FormItem>
      )}
    />
  );
};

export const getAvailableProviders = (user: UserPublic | null) => {
  if (!user) return [];
  const keys = user?.keys || {};
  const availableProviders: Record<string, string>[] = [];
  const providerKeys = {
    [Provider.OPENAI]: "OpenAI",
    [Provider.ANTHROPIC]: "Anthropic",
    [Provider.GEMINI]: "Gemini",
    [Provider.OPENROUTER]: "OpenRouter",
  };
  for (const key in keys) {
    if (key in providerKeys && keys[key]) {
      availableProviders.push({
        key: key,
        value: providerKeys[key as Provider],
      });
    }
  }
  return availableProviders;
};
export const BaseEditorFormFields = () => {
  const methods = useFormContext<PlaygroundParameters>();
  const { data: user } = useSuspenseQuery(userQueryOptions());
  const provider = methods.watch("provider");
  const selectItems = getAvailableProviders(user);

  useEffect(() => {
    let model = "gpt-4o";
    if (provider === Provider.ANTHROPIC) {
      model = "claude-3-5-sonnet-latest";
    } else if (provider === Provider.GEMINI) {
      model = "gemini-1.5-flash";
    } else if (provider === Provider.OPENROUTER) {
      model = "openai/chatgpt-4o-latest";
    }

    methods.resetField("model", { defaultValue: model });
  }, [provider, methods.resetField]);

  const renderSliders = {
    maxTokens: createFormSlider("maxTokens"),
    temperature: createFormSlider("temperature"),
    topK: createFormSlider("topK"),
    topP: createFormSlider("topP"),
    frequencyPenalty: createFormSlider("frequencyPenalty"),
    presencePenalty: createFormSlider("presencePenalty"),
  };

  const commonParams = [
    renderSliders.temperature("generation.call_params.temperature"),
    renderSliders.maxTokens("generation.call_params.max_tokens"),
    renderSliders.topP("generation.call_params.top_p"),
    renderSliders.frequencyPenalty("generation.call_params.frequency_penalty"),
    renderSliders.presencePenalty("generation.call_params.presence_penalty"),
    renderSeed(),
    renderStopSequences("generation.call_params.stop", 4),
  ];
  return (
    <div className='w-full max-w-sm flex flex-col gap-3'>
      {selectItems.length > 0 && (
        <>
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
                      {selectItems.map((item) => (
                        <SelectItem key={item.key} value={item.key}>
                          {item.value}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          <ModelCombobox<PlaygroundParameters, "model">
            control={methods.control}
            name='model'
            label='Choose a Model'
            options={getModelOptions(provider)}
            defaultValue={methods.getValues("model")}
          />
        </>
      )}
      {commonParams}
    </div>
  );
};

export const formValuesToApi = (obj: { [key: string]: unknown }) => {
  // For each property that has an 'enabled' field and a 'value' field, we want to
  // replace the object with the 'value' field if 'enabled' is true, and delete the
  // property if 'enabled' is false.
  for (const key of Object.keys(obj)) {
    const param = obj[key];
    if (
      param &&
      typeof param === "object" &&
      "enabled" in param &&
      "value" in param
    ) {
      if (param.enabled) {
        obj[key] = param.value;
      } else {
        delete (obj as any)[key];
      }
    }
  }

  return obj;
};
