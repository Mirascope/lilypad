import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { functionsByNameQueryOptions } from "@/utils/functions";
import { useSuspenseQuery } from "@tanstack/react-query";
import { createFileRoute, useParams } from "@tanstack/react-router";

import CardSkeleton from "@/components/CardSkeleton";
import { CompareTracesTable } from "@/components/CompareTracesTable";
import { LilypadLoading } from "@/components/LilypadLoading";
import { MetricCharts } from "@/components/MetricsCharts";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { DiffTool } from "@/ee/components/DiffTool";
import { Playground } from "@/ee/components/Playground";
import { usePlaygroundContainer } from "@/ee/hooks/use-playground";
import { useRunPlaygroundMutation } from "@/ee/utils/functions";
import { FormItemValue, simplifyFormItem } from "@/ee/utils/input-utils";
import { useFeatureAccess } from "@/hooks/use-featureaccess";
import { FunctionTab } from "@/types/functions";
import { FunctionPublic, PlaygroundParameters } from "@/types/types";
import { Construction } from "lucide-react";
import { Suspense, useState } from "react";

export const Route = createFileRoute(
  "/_auth/projects/$projectUuid/functions/$functionName/_workbench/compare/$firstFunctionUuid/$secondFunctionUuid/$tab"
)({
  component: () => (
    <Suspense fallback={<LilypadLoading />}>
      <Function />
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
  const [firstResponse, setFirstResponse] = useState<string>("");
  const [secondResponse, setSecondResponse] = useState<string>("");
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

    try {
      // Run both functions in parallel
      await Promise.all([
        runFunction(firstPlayground, firstFunction.uuid, (response) =>
          setFirstResponse(response)
        ),
        runFunction(secondPlayground, secondFunction.uuid, (response) =>
          setSecondResponse(response)
        ),
      ]);
    } catch (error) {
      console.error("Error running functions:", error);
    } finally {
      setIsRunning(false);
    }
  };

  // Helper function to run a single function
  const runFunction = async (
    playground: ReturnType<typeof usePlaygroundContainer>,
    functionUuid: string,
    setResponse: (response: string) => void
  ) => {
    const { methods, inputs, projectUuid } = playground;
    if (!projectUuid) return;
    // Get data from the form
    const data = methods.getValues();

    return new Promise<void>(async (resolve) => {
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
        const playgroundValues: PlaygroundParameters = {
          arg_values: inputValues,
          provider: data.provider,
          model: data.model,
        };

        // Run function
        const result = await runMutation.mutateAsync({
          projectUuid,
          functionUuid,
          playgroundValues,
        });

        // Set the response in state
        setResponse(result);
      } catch (error) {
        console.error(error);
      }
      resolve();
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
            isCompare={true}
            playgroundContainer={firstPlayground}
          />
        </div>

        <div className='flex-1'>
          <Playground
            version={secondFunction}
            response={secondResponse}
            isCompare={true}
            playgroundContainer={secondPlayground}
          />
        </div>
      </div>
    </div>
  );
};

const Function = () => {
  const { projectUuid, firstFunctionUuid, secondFunctionUuid, tab } = useParams(
    {
      from: Route.id,
    }
  );
  if (tab === FunctionTab.OVERVIEW) {
    return <FunctionOverview />;
  } else if (tab === FunctionTab.TRACES) {
    return (
      <CompareTracesTable
        projectUuid={projectUuid}
        firstFunctionUuid={firstFunctionUuid}
        secondFunctionUuid={secondFunctionUuid}
      />
    );
  } else if (tab === FunctionTab.ANNOTATIONS) {
    return (
      <div className='flex justify-center items-center h-96'>
        <Construction color='orange' /> This page is under construction{" "}
        <Construction color='orange' />
      </div>
    );
  }
};
const FunctionOverview = () => {
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
      <div className='p-4 flex flex-col gap-6 max-w-6xl mx-auto'>
        <Suspense fallback={<CardSkeleton />}>
          <MetricCharts
            firstFunction={firstFunction}
            secondFunction={secondFunction}
            projectUuid={projectUuid}
          />
        </Suspense>
        <div className='text-left'>
          <Label className='text-lg font-semibold'>Code Comparison</Label>
          <DiffTool
            firstLexicalClosure={firstFunction.code}
            secondLexicalClosure={secondFunction.code}
          />
        </div>
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
