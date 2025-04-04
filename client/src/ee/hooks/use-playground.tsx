import { PLAYGROUND_TRANSFORMERS } from "@/ee/components/lexical/markdown-transformers";
import { $findErrorTemplateNodes } from "@/ee/components/lexical/template-node";
import { useRunPlaygroundMutation } from "@/ee/utils/functions";
import { FormItemValue, simplifyFormItem } from "@/ee/utils/input-utils";
import { useToast } from "@/hooks/use-toast";
import {
  FunctionCreate,
  FunctionPublic,
  PlaygroundParameters,
  PlaygroundErrorDetail
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
import { $getRoot, $isParagraphNode, LexicalEditor } from "lexical"; // Import Lexical node types if needed
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
  isCompare = false,
}: {
  version: FunctionPublic | null;
  isCompare?: boolean;
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
  // Initialize form with base editor form
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

  // Watch inputs for changes
  const inputs = methods.watch("inputs");

  // Process input values
  const inputValues = inputs.reduce(
    (acc, input) => {
      if (input.type === "list" || input.type === "dict") {
        try {
          // Type narrowing happens here
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
  // Editor state
  const [editorErrors, setEditorErrors] = useState<string[]>([]);
  const [openInputDrawer, setOpenInputDrawer] = useState<boolean>(false);
  const [result, setResult] = useState<string | null>(null);
  const [error, setError] = useState<PlaygroundErrorDetail | null>(null);
  const editorRef = useRef<LexicalEditor>(null);
  const doesProviderExist = getAvailableProviders(user).length > 0;

  // Handler for form submission
  const onSubmit = async (
    data: EditorParameters,
    event?: BaseSyntheticEvent
  ) => {
    event?.preventDefault();
    methods.clearErrors();
    setEditorErrors([]);
    setResult(null);
    setError(null);

    if (!editorRef?.current || !projectUuid || !functionName) return;
    // Determine which button was clicked
    let buttonName = "";
    if (
      (event?.nativeEvent as unknown as { submitter: HTMLButtonElement })
        ?.submitter
    ) {
      buttonName = (
        event?.nativeEvent as unknown as { submitter: HTMLButtonElement }
      ).submitter.name;
    } else if (event?.target && "name" in event.target) {
      buttonName = (event.target as { name: string }).name;
    }

    const templateErrors = $findErrorTemplateNodes(editorRef.current);
    if (templateErrors.length > 0) {
      setEditorErrors(
        templateErrors.map(
          (node) => `'${node.getValue()}' is not a valid function argument.` // Corrected message
        )
      );
      return; // Stop submission if template errors exist
    }
    // Read editor state
    const editorState = editorRef.current.getEditorState();

    return new Promise<void>((resolve) => {
      void editorState.read(async () => {
        // Convert editor content to markdown
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
        // Create function object
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

        // Validate form
        const isValid = await methods.trigger();
        if (!isValid) {
          resolve();
          return;
        }

        if (buttonName !== "run") {
           resolve();
           return;
        }

        // Validate custom inputs (args and their values)
        if (!validateInputs(methods, data.inputs)) {
          setOpenInputDrawer(true);
          resolve();
          return;
        }

        try {
          // Create a new version of the function
           // It includes the prompt_template, call_params, arg_types etc.
          const newVersion = await createVersionedFunction.mutateAsync({
            projectUuid,
            functionCreate, // Pass the prepared function data
          });

          // Process input values specifically for the run execution
          const runInputValues = inputs.reduce(
            (acc, input) => {
               if (input.key && input.key.trim().length > 0) {
                  if (input.type === "list" || input.type === "dict") {
                    try {
                      const simplifiedValue = simplifyFormItem(
                        input as FormItemValue // Cast needed due to complexity
                      );
                      acc[input.key] = simplifiedValue;
                    } catch (parseError) {
                       console.warn(`Could not parse input '${input.key}':`, parseError);
                      acc[input.key] = input.value; // Fallback to raw value
                    }
                  } else {
                    acc[input.key] = input.value;
                  }
              }
              return acc;
            },
            {} as Record<string, any>
          );
          // TODO: Update this to only pass in arg_values
          const playgroundParameters: PlaygroundParameters = {
            arg_values: runInputValues,
            provider: data.provider,
            model: data.model,
            arg_types: argTypes,
            call_params: data?.call_params,
            prompt_template: markdown,
          };

          // Execute the function run via the API
          const response = await runMutation.mutateAsync({
            projectUuid,
            functionUuid: newVersion.uuid,
            playgroundParameters,
          });

          if (response.success) {
            setResult(response.data.result);
            setError(null);
          } else {
             // Handle specific error from the run endpoint
            setError(response.error);
            setResult(null);
            toast({
              title: "Error Running Playground", // More specific title
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
           setResult(null);
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

  // Handle setting function as default
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
    setResult(null);
    setError(null);
    setEditorErrors([]);
    if (editorRef.current) {
    }
  };

  const { fields, append, remove } = useFieldArray<EditorParameters>({
    control: methods.control,
    name: "inputs",
  });

  const addInput = () => {
    append({ key: "", type: "str", value: "" });
  };

  return {
    // Form state
    methods,
    editorRef,
    inputs,
    inputValues,
    editorErrors,

    // UI state
    openInputDrawer,
    setOpenInputDrawer,
    doesProviderExist,

    // Loading states
    isRunLoading: runMutation.isPending,
    isCreateLoading: createVersionedFunction.isPending,
    isPatchLoading: patchFunction.isPending,

    // Event handlers
    onSubmit, // Form submission handler
    handleSetDefault, // Handler for setting version as default
    handleReset, // Handler for resetting the form

    // Input field array management
    fields, // Array of input fields from useFieldArray
    addInput, // Function to add a new input field
    removeInput: remove, // Function to remove an input field (renamed for clarity)

    // Route parameters
    projectUuid,
    functionName,

    isDisabled: isCompare,

    // Execution result and error
    result,
    error,
    setError,
  };
};