import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { functionsByNameQueryOptions } from "@/utils/functions";
import { useSuspenseQuery } from "@tanstack/react-query";
import { createFileRoute, useParams } from "@tanstack/react-router";

import { LilypadLoading } from "@/components/LilypadLoading";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { PLAYGROUND_TRANSFORMERS } from "@/ee/components/lexical/markdown-transformers";
import { Playground } from "@/ee/components/Playground";
import { usePlaygroundContainer } from "@/ee/hooks/use-playground";
import { useRunPlaygroundMutation } from "@/ee/utils/functions";
import { FormItemValue, simplifyFormItem } from "@/ee/utils/input-utils";
import { useFeatureAccess } from "@/hooks/use-featureaccess";
import { useToast } from "@/hooks/use-toast";
import { FunctionPublic, PlaygroundParameters, PlaygroundErrorDetail } from "@/types/types";
import { $convertToMarkdownString } from "@lexical/markdown";
import { Suspense, useState } from "react";
export const Route = createFileRoute(
  "/_auth/projects/$projectUuid/playground/$functionName/compare/$firstFunctionUuid/$secondFunctionUuid"
)({
  component: () => (
    <Suspense fallback={<LilypadLoading />}>
      <ComparePlaygroundsRoute />
    </Suspense>
  ),
});

// Component to handle both playgrounds with a shared run button
const ComparePlaygrounds = ({
  firstFunction,
  secondFunction,
}: {
  firstFunction: FunctionPublic;
  secondFunction: FunctionPublic;
}) => {
  const { toast } = useToast();
  const [firstResponse, setFirstResponse] = useState<string>("");
  const [secondResponse, setSecondResponse] = useState<string>("");
  const [firstError, setFirstError] = useState<PlaygroundErrorDetail | null>(null);
  const [secondError, setSecondError] = useState<PlaygroundErrorDetail | null>(null);
  const [isRunning, setIsRunning] = useState(false);
  // Set up hooks for both functions
  const firstPlayground = usePlaygroundContainer({
    version: firstFunction,
    isCompare: true,
  });
  const secondPlayground = usePlaygroundContainer({
    version: secondFunction,
    isCompare: true,
  });

  const runMutation = useRunPlaygroundMutation();

  // Check if either playground has missing API keys
  const canRun =
    firstPlayground.doesProviderExist && secondPlayground.doesProviderExist;

  const runBothFunctions = async () => {
    setIsRunning(true);
    setFirstResponse("");
    setSecondResponse("");
    setFirstError(null);
    setSecondError(null);

    try {
      // Run both functions in parallel
      await Promise.all([
        runFunction(
          firstPlayground,
          firstFunction.uuid,
          (response) => setFirstResponse(response),
          (error) => setFirstError(error)
        ),
        runFunction(
          secondPlayground,
          secondFunction.uuid,
          (response) => setSecondResponse(response),
          (error) => setSecondError(error)
        ),
      ]);
    } catch (error) {
      console.error("Error running functions:", error);
      toast({
        title: "Error",
        description: "Failed to run one or both functions",
        variant: "destructive",
      });
    } finally {
      setIsRunning(false);
    }
  };

  // Helper function to run a single function
  const runFunction = (
    playground: ReturnType<typeof usePlaygroundContainer>,
    functionUuid: string,
    setResponse: (response: string) => void,
    setError: (error: PlaygroundErrorDetail) => void
  ) => {
    const { methods, inputs, projectUuid } = playground;
    if (!projectUuid) return Promise.resolve();

    // Get data from the form
    const data = methods.getValues();
    const editorState = playground?.editorRef?.current?.getEditorState();
    if (!editorState) return Promise.resolve();

    return editorState
      .read(async () => {
        // Convert editor content to markdown
        const markdown = $convertToMarkdownString(PLAYGROUND_TRANSFORMERS);
        try {
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

          // Set up playground values
          const playgroundParameters: PlaygroundParameters = {
            arg_values: inputValues,
            provider: data.provider,
            model: data.model,
            arg_types: data.arg_types,
            call_params: data?.call_params,
            prompt_template: markdown,
          };

          // Run function
          const result = await runMutation.mutateAsync({
            projectUuid,
            functionUuid,
            playgroundParameters,
          });

          // Handle the typed response
          if (result.success) {
            // Set successful response
            // If result.data.result is a string, use it directly
            if (typeof result.data.result === 'string') {
              setResponse(result.data.result);
            } else {
              // Otherwise, stringify it for display
              setResponse(JSON.stringify(result.data.result, null, 2));
            }
          } else {
            setError(result.error);
            console.error("Function error:", result.error);
          }
        } catch (error) {
          console.error(error);
          toast({
            title: "Error running function",
            description: error instanceof Error ? error.message : String(error),
            variant: "destructive",
          });
        }
      })
      .catch((error) => {
        console.error("Editor error:", error);
        toast({
          title: "Failed to run function",
          description: "Could not read editor state",
          variant: "destructive",
        });
      });
  };

  return (
    <div className='flex flex-col gap-4'>
      <div className='flex justify-end'>
        <Tooltip>
          <TooltipTrigger asChild>
            <span>
              <Button
                name='run'
                loading={isRunning}
                disabled={!canRun}
                onClick={runBothFunctions}
                className='hover:bg-green-700 text-white font-medium'
              >
                Run Both Playgrounds
              </Button>
            </span>
          </TooltipTrigger>
          <TooltipContent className='bg-gray-700 text-white'>
            <p className='max-w-xs break-words'>
              {canRun
                ? "Run both playgrounds simultaneously and compare outputs."
                : "You need to add API keys to run the playgrounds."}
            </p>
          </TooltipContent>
        </Tooltip>
      </div>

      <div className='flex w-full justify-between gap-4 overflow-auto'>
        <div className='flex-1'>
          <Playground
            version={firstFunction}
            response={firstResponse}
            error={firstError}
            isCompare={true}
            playgroundContainer={firstPlayground}
          />
        </div>

        <div className='flex-1'>
          <Playground
            version={secondFunction}
            response={secondResponse}
            error={secondError}
            isCompare={true}
            playgroundContainer={secondPlayground}
          />
        </div>
      </div>
    </div>
  );
};

const ComparePlaygroundsRoute = () => {
  const { projectUuid, functionName, functionUuid, secondFunctionUuid } =
    useParams({
      from: Route.id,
    });
  const { data: functions } = useSuspenseQuery(
    functionsByNameQueryOptions(functionName, projectUuid)
  );
  const features = useFeatureAccess();
  const firstFunction = functions.find((f) => f.uuid === functionUuid);
  const secondFunction = functions.find((f) => f.uuid === secondFunctionUuid);

  if (!firstFunction || !secondFunction) {
    return <div>Please select two functions to compare.</div>;
  } else {
    return (
      <div className='p-4 flex flex-col gap-6'>
        {features.playground &&
          firstFunction.is_versioned &&
          secondFunction.is_versioned && (
            <div className='text-left'>
              <Label className='text-lg font-semibold'>Compare Functions</Label>
              <ComparePlaygrounds
                firstFunction={firstFunction}
                secondFunction={secondFunction}
              />
            </div>
          )}
      </div>
    );
  }
};
