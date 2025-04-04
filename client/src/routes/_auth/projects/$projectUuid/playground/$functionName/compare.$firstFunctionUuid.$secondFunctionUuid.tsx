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
import {Suspense, useState } from "react";
import {Card, CardContent, CardHeader, CardTitle} from "@/components/ui/card.tsx";
import CardSkeleton from "@/components/CardSkeleton.tsx";
import {LilypadPanel} from "@/components/LilypadPanel.tsx";


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
  const [firstSpanUuid, setFirstSpanUuid] = useState<string | null>(null);
  const [secondSpanUuid, setSecondSpanUuid] = useState<string | null>(null);
  const [firstError, setFirstError] = useState<PlaygroundErrorDetail | null>(null);
  const [secondError, setSecondError] = useState<PlaygroundErrorDetail | null>(null);
  const [isRunning, setIsRunning] = useState(false);
  // Set up hooks for both functions
  const firstPlayground = usePlaygroundContainer({
    version: firstFunction,
  });
  const secondPlayground = usePlaygroundContainer({
    version: secondFunction,
  });

  const runMutation = useRunPlaygroundMutation();

  // Check if either playground has missing API keys
  const canRun =
    firstPlayground.doesProviderExist && secondPlayground.doesProviderExist;

  const runBothFunctions = async () => {
    setIsRunning(true);
    setFirstSpanUuid(null);
    setSecondSpanUuid(null);
    setFirstError(null);
    setSecondError(null);

    try {
      // Run both functions in parallel
      await Promise.all([
        runFunction(
          firstPlayground,
          firstFunction.uuid,
          (spanUuid) => setFirstSpanUuid(spanUuid),
          (error) => setFirstError(error)
        ),
        runFunction(
          secondPlayground,
          secondFunction.uuid,
          (spanUuid) => setSecondSpanUuid(spanUuid),
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
    setSpanUuid: (spanUuid: string) => void,
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

          // Handle the response
          if (result.success && result.data.trace_context?.span_uuid) {
            setSpanUuid(result.data.trace_context.span_uuid);
          } else if (!result.success) {
            setError(result.error.error);
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
    <div className="flex flex-col h-full">
      <div className="flex justify-end mb-4">
        <Tooltip>
          <TooltipTrigger asChild>
            <span>
              <Button
                name="run"
                loading={isRunning}
                disabled={!canRun || isRunning}
                onClick={runBothFunctions}
                className="hover:bg-green-700 text-white font-medium"
              >
                Run Both Playgrounds
              </Button>
            </span>
          </TooltipTrigger>
          <TooltipContent className="bg-gray-700 text-white">
            <p className="max-w-xs break-words">
              {canRun
                ? "Run both playgrounds simultaneously and compare outputs."
                : "You need to add API keys to run the playgrounds."}
            </p>
          </TooltipContent>
        </Tooltip>
      </div>

      <div className="flex mb-4" style={{ gap: '16px' }}>
        <div style={{ width: '50%' }}>
          <div className="playground-container">
            <Playground
            version={firstFunction}
            error={firstError}
            isCompare={true}
            playgroundContainer={firstPlayground}
          />
          </div>
        </div>
        <div style={{ width: '50%' }}>
          <div className="playground-container">
            <Playground
            version={secondFunction}
            error={secondError}
            isCompare={true}
            playgroundContainer={secondPlayground}
          />
          </div>
        </div>
      </div>

      {(firstSpanUuid ?? secondSpanUuid) && (
        <div className="flex mt-4" style={{ gap: '16px' }}>
          <div style={{ width: '50%' }}>
            <Card className="h-full">
              <CardHeader>
                <CardTitle>Function 1 Result</CardTitle>
              </CardHeader>
              <CardContent>
                {firstSpanUuid ? (
                  <Suspense fallback={<CardSkeleton items={5} className="flex flex-col" />}>
                    <LilypadPanel spanUuid={firstSpanUuid} />
                  </Suspense>
                ) : firstError ? (
                  <div className="text-red-500">
                    {firstError.reason || "An error occurred"}
                  </div>
                ) : (
                  <div className="text-gray-500">No result yet</div>
                )}
              </CardContent>
            </Card>
          </div>
          <div style={{ width: '50%' }}>
            <Card className="h-full">
              <CardHeader>
                <CardTitle>Function 2 Result</CardTitle>
              </CardHeader>
              <CardContent>
                {secondSpanUuid ? (
                  <Suspense fallback={<CardSkeleton items={5} className="flex flex-col" />}>
                    <LilypadPanel spanUuid={secondSpanUuid} />
                  </Suspense>
                ) : secondError ? (
                  <div className="text-red-500">
                    {secondError.reason || "An error occurred"}
                  </div>
                ) : (
                  <div className="text-gray-500">No result yet</div>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      )}
    </div>
  );
};

const ComparePlaygroundsRoute = () => { /* ... remains the same ... */
  const { projectUuid, functionName, firstFunctionUuid, secondFunctionUuid } = useParams({ from: "/_auth/projects/$projectUuid/playground/$functionName/compare/$firstFunctionUuid/$secondFunctionUuid", });
  const { data: functions } = useSuspenseQuery( functionsByNameQueryOptions(functionName, projectUuid));
  const features = useFeatureAccess();
  const firstFunction = functions.find((f) => f.uuid === firstFunctionUuid);
  const secondFunction = functions.find((f) => f.uuid === secondFunctionUuid);
  if (!firstFunction || !secondFunction) { return <div>Selected functions not found or invalid comparison link.</div>; }
  const canCompare = features.playground && firstFunction.is_versioned && secondFunction.is_versioned;
  return ( <div className='p-4 flex flex-col gap-6 flex-1 h-full'> <div className='text-left flex flex-col flex-1 h-full'> <Label className='text-lg font-semibold mb-4'>Compare Functions</Label> {canCompare ? ( <ComparePlaygrounds firstFunction={firstFunction} secondFunction={secondFunction} /> ) : ( <div>Comparison requires versioned functions and playground access.</div> )} </div> </div> );
};