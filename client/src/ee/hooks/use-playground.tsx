import { PLAYGROUND_TRANSFORMERS } from "@/ee/components/lexical/markdown-transformers";
import { $findErrorTemplateNodes } from "@/ee/components/lexical/template-node";
import {
  useCreateManagedGeneration,
  useRunMutation,
} from "@/ee/utils/generations";
import { FormItemValue, simplifyFormItem } from "@/ee/utils/input-utils";
import {
  GenerationCreate,
  GenerationPublic,
  PlaygroundParameters,
} from "@/types/types";
import { usePatchGenerationMutation } from "@/utils/generations";
import {
  getAvailableProviders,
  useBaseEditorForm,
  validateInputs,
} from "@/utils/playground-utils";
import { userQueryOptions } from "@/utils/users";
import { $convertToMarkdownString } from "@lexical/markdown";
import { useSuspenseQuery } from "@tanstack/react-query";
import { useNavigate, useParams } from "@tanstack/react-router";
import { LexicalEditor } from "lexical";
import { BaseSyntheticEvent, useRef, useState } from "react";
import { useFieldArray } from "react-hook-form";

// Define the form values type
export type FormValues = {
  inputs: Record<string, any>[];
};

// Define the editor parameters type
export type EditorParameters = PlaygroundParameters & FormValues;

/**
 * Custom hook that encapsulates all the business logic for the Playground component
 */
export const usePlaygroundContainer = ({
  version,
  isCompare = false,
}: {
  version: GenerationPublic | null;
  isCompare?: boolean;
}) => {
  const { projectUuid, generationName } = useParams({
    strict: false,
  });
  const { data: user } = useSuspenseQuery(userQueryOptions());
  const navigate = useNavigate();
  const createGenerationMutation = useCreateManagedGeneration();
  const runMutation = useRunMutation();
  const patchGeneration = usePatchGenerationMutation();
  // Initialize form with base editor form
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

  // Watch inputs for changes
  const inputs = methods.watch("inputs");

  // Process input values
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

  // Editor state
  const [editorErrors, setEditorErrors] = useState<string[]>([]);
  const [openInputDrawer, setOpenInputDrawer] = useState<boolean>(false);
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

    if (!editorRef?.current || !projectUuid || !generationName) return;

    // Determine which button was clicked
    let buttonName = "";
    if (
      (event?.nativeEvent as unknown as { submitter: HTMLButtonElement })
        ?.submitter
    ) {
      buttonName = (
        event?.nativeEvent as unknown as { submitter: HTMLButtonElement }
      ).submitter.name;
    } else if (event?.target?.name) {
      buttonName = event.target.name;
    }

    // Check for errors in editor
    const editorErrors = $findErrorTemplateNodes(editorRef.current);
    if (editorErrors.length > 0) {
      setEditorErrors(
        editorErrors.map(
          (node) => `'${node.getValue()}' is not a function argument.`
        )
      );
      return;
    }

    // Read editor state
    const editorState = editorRef.current.getEditorState();

    return new Promise<void>((resolve) => {
      editorState.read(async () => {
        // Convert editor content to markdown
        const markdown = $convertToMarkdownString(PLAYGROUND_TRANSFORMERS);

        // Create generation object
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

        // Handle run button
        if (buttonName === "run") {
          // Validate inputs
          if (!validateInputs(methods, data.inputs)) {
            setOpenInputDrawer(true);
            resolve();
            return;
          }

          try {
            // Create new version
            const newVersion = await createGenerationMutation.mutateAsync({
              projectUuid,
              generationCreate,
            });

            // Process input values for the run
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

            // TODO: Update this to only pass in arg_values
            const playgroundValues: PlaygroundParameters = {
              arg_values: inputValues,
              provider: data.provider,
              model: data.model,
            };

            // Run generation
            const res = await runMutation.mutateAsync({
              projectUuid,
              generationUuid: newVersion.uuid,
              playgroundValues,
            });

            navigate({
              to: `/projects/${projectUuid}/generations/${newVersion.name}/${newVersion.uuid}/overview`,
              replace: true,
              state: {
                result: res,
              },
            });
          } catch (error) {
            console.error(error);
          }
        } else {
          try {
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

        resolve();
      });
    });
  };

  // Handle setting generation as default
  const handleSetDefault = (e: React.MouseEvent<HTMLButtonElement>) => {
    e.preventDefault();
    if (version && projectUuid) {
      patchGeneration.mutate({
        projectUuid,
        generationUuid: version.uuid,
        generationUpdate: { is_default: true },
      });
    }
  };

  const handleReset = () => {
    methods.reset();
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
    isCreateLoading: createGenerationMutation.isPending,
    isPatchLoading: patchGeneration.isPending,

    // Handlers
    onSubmit,
    handleSetDefault,
    handleReset,
    fields,
    addInput,
    removeInput: remove,

    // Navigation
    projectUuid,
    generationName,

    isDisabled: isCompare,
  };
};
