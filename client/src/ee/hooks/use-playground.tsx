import { PLAYGROUND_TRANSFORMERS } from "@/ee/components/lexical/markdown-transformers";
import { $findErrorTemplateNodes } from "@/ee/components/lexical/template-node";
import { useRunPlaygroundMutation } from "@/ee/utils/functions";
import { FormItemValue, simplifyFormItem } from "@/ee/utils/input-utils";
import { useToast } from "@/hooks/use-toast";
import {
  FunctionCreate,
  FunctionPublic,
  PlaygroundParameters,
  PlaygroundErrorDetail,
} from "@/types/types";
import {
  useCreateVersionedFunctionMutation,
  usePatchFunctionMutation,
} from "@/utils/functions";
import {
  getAvailableProviders,
  useBaseEditorForm,
  validateInputs,
} from "@/utils/playground-utils";
import { userQueryOptions } from "@/utils/users";
import { $convertToMarkdownString } from "@lexical/markdown";
import { $getRoot, $isParagraphNode, LexicalEditor } from "lexical";
import { useSuspenseQuery } from "@tanstack/react-query";
import { useNavigate, useParams } from "@tanstack/react-router";
import { BaseSyntheticEvent, useRef, useState } from "react";
import { useFieldArray } from "react-hook-form";

// Define the form values type
export interface FormValues {
  inputs: Record<string, any>[];
}

// Define the editor parameters type
export type EditorParameters = PlaygroundParameters & FormValues;

/**
 * Custom hook that encapsulates all the business logic for the Playground component
 */
export const usePlaygroundContainer = ({
  version,
}: {
  version: FunctionPublic | null;
}) => {
  const { projectUuid, functionName } = useParams({
    strict: false,
  });
  const { data: user } = useSuspenseQuery(userQueryOptions());
  const navigate = useNavigate();
  const createVersionedFunction = useCreateVersionedFunctionMutation();
  const runMutation = useRunPlaygroundMutation();
  const patchFunction = usePatchFunctionMutation();
  const { toast } = useToast();
  const methods = useBaseEditorForm<EditorParameters>({
    latestVersion: version,
    additionalDefaults: {
      inputs: version?.arg_types
        ? Object.keys(version.arg_types).map((key) => ({
            key,
            type: version.arg_types?.[key] ?? "str",
            value: "",
          }))
        : [],
    },
  });

  const inputs = methods.watch("inputs");

  const inputValues = inputs.reduce(
    (acc, input) => {
      if (input.type === "list" || input.type === "dict") {
        try {
          const simplifiedValue = simplifyFormItem(input as any);
          acc[input.key] = simplifiedValue;
        } catch {
          acc[input.key] = input.value;
        }
      } else {
        acc[input.key] = input.value;
      }
      return acc;
    },
    {} as Record<string, any>
  );

  const [editorErrors, setEditorErrors] = useState<string[]>([]);
  const [openInputDrawer, setOpenInputDrawer] = useState<boolean>(false);
  const [error, setError] = useState<PlaygroundErrorDetail | null>(null);
  const [executedSpanUuid, setExecutedSpanUuid] = useState<string | null>(null); // Add state for executed span UUID
  const editorRef = useRef<LexicalEditor>(null);
  const doesProviderExist = getAvailableProviders(user).length > 0;

  const onSubmit = async (
    data: EditorParameters,
    event?: BaseSyntheticEvent
  ) => {
    event?.preventDefault();
    methods.clearErrors();
    setEditorErrors([]);
    setError(null);
    setExecutedSpanUuid(null);

    if (!editorRef?.current || !projectUuid || !functionName) return;

    let buttonName = "";
    if ((event?.nativeEvent as unknown as { submitter: HTMLButtonElement })?.submitter) {
      buttonName = (event?.nativeEvent as unknown as { submitter: HTMLButtonElement }).submitter.name;
    } else if (event?.target && "name" in event.target) {
      buttonName = (event.target as { name: string }).name;
    }

    const templateErrors = $findErrorTemplateNodes(editorRef.current);
    if (templateErrors.length > 0) {
      setEditorErrors(
        templateErrors.map((node) => `'${node.getValue()}' is not a valid function argument.`)
      );
      return;
    }

    const editorState = editorRef.current.getEditorState();

    return new Promise<void>((resolve) => {
      void editorState.read(async () => {
        const markdown = $convertToMarkdownString(PLAYGROUND_TRANSFORMERS);

        let isEmpty = false;
        if (!markdown || markdown.trim().length === 0) {
          isEmpty = true;
        } else {
          const root = $getRoot();
          const firstChild = root.getFirstChild();
          if (root.getChildrenSize() === 1 && firstChild && $isParagraphNode(firstChild) && firstChild.getTextContent().trim() === '') {
            isEmpty = true;
          }
        }

        if (isEmpty) {
          toast({
            title: "Empty Prompt",
            description: "The prompt template cannot be empty. Please enter some text.",
            variant: "destructive",
          });
          resolve();
          return;
        }

        const argTypes = inputs.reduce(
          (acc, input) => {
            if (input.key && input.key.trim().length > 0) {
              acc[input.key] = input.type;
            }
            return acc;
          },
          {} as Record<string, string>
        );

        const functionCreate: FunctionCreate = {
          prompt_template: markdown,
          call_params: data.call_params ?? undefined,
          name: functionName,
          arg_types: argTypes,
          provider: data.provider,
          model: data.model,
          signature: "",
          hash: "",
          code: "",
        };

        const isValid = await methods.trigger();
        if (!isValid) {
          resolve();
          return;
        }

        if (buttonName !== "run") {
          resolve();
          return;
        }

        if (!validateInputs(methods, data.inputs)) {
          setOpenInputDrawer(true);
          resolve();
          return;
        }

        try {
          const newVersion = await createVersionedFunction.mutateAsync({
            projectUuid,
            functionCreate,
          });

          const runInputValues = inputs.reduce(
            (acc, input) => {
              if (input.key && input.key.trim().length > 0) {
                if (input.type === "list" || input.type === "dict") {
                  try {
                    const simplifiedValue = simplifyFormItem(input as FormItemValue);
                    acc[input.key] = simplifiedValue;
                  } catch (parseError) {
                    console.warn(`Could not parse input '${input.key}':`, parseError);
                    acc[input.key] = input.value;
                  }
                } else {
                  acc[input.key] = input.value;
                }
              }
              return acc;
            },
            {} as Record<string, any>
          );

          const playgroundParameters: PlaygroundParameters = {
            arg_values: runInputValues,
            provider: data.provider,
            model: data.model,
            arg_types: argTypes,
            call_params: data?.call_params,
            prompt_template: markdown,
          };

          const response = await runMutation.mutateAsync({
            projectUuid,
            functionUuid: newVersion.uuid,
            playgroundParameters,
          });

          if (response.success) {
            // setResult(response.data.result); // Remove setting result string
            setExecutedSpanUuid(response.data.trace_context?.span_uuid ?? null); // Set the executed span UUID
            setError(null);
          } else {
            setError(response.error);
            setExecutedSpanUuid(null);
            toast({
              title: "Error Running Playground",
              description: response.error.reason || "An unknown error occurred.",
              variant: "destructive",
            });
          }

          navigate({
            to: `/projects/${projectUuid}/playground/${newVersion.name}/${newVersion.uuid}`,
            replace: true,
          }).catch((navError) => {
            console.error("Navigation failed:", navError);
            toast({
              title: "Navigation Error",
              description: "Failed to update the URL after running the playground.",
              variant: "warning",
            });
          });
        } catch (apiError) {
          console.error("API Error during create/run:", apiError);
          const message = apiError instanceof Error ? apiError.message : "An unexpected API error occurred.";
          setError({
            type: 'ApiError',
            reason: 'Failed to create or run the function version via API.',
            details: message
          });
          setExecutedSpanUuid(null);
          toast({
            title: "API Error",
            description: message,
            variant: "destructive",
          });
        } finally {
          resolve();
        }
      });
    });
  };

  const handleSetDefault = (e: React.MouseEvent<HTMLButtonElement>) => {
    e.preventDefault();
    if (version && projectUuid) {
      patchFunction.mutate({
        projectUuid,
        functionUuid: version.uuid,
        functionUpdate: { is_default: true },
      });
    }
  };

  const handleReset = () => {
    methods.reset();
    // setResult(null); // Remove result clearing
    setError(null);
    setExecutedSpanUuid(null); // Clear span UUID on reset
    setEditorErrors([]);
    // Consider resetting Lexical editor state explicitly if needed
  };

  const { fields, append, remove } = useFieldArray<EditorParameters>({
    control: methods.control,
    name: "inputs",
  });

  const addInput = () => {
    append({ key: "", type: "str", value: "" });
  };

  return {
    methods,
    editorRef,
    inputs,
    inputValues,
    editorErrors,
    openInputDrawer,
    setOpenInputDrawer,
    doesProviderExist,
    isRunLoading: runMutation.isPending,
    isCreateLoading: createVersionedFunction.isPending,
    isPatchLoading: patchFunction.isPending,
    onSubmit,
    handleSetDefault,
    handleReset,
    fields,
    addInput,
    removeInput: remove,
    projectUuid,
    functionName,
    executedSpanUuid,
    error,
    setError,
  };
};