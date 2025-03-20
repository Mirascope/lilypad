import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { generationsByNameQueryOptions } from "@/utils/generations";
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
import { useRunMutation } from "@/ee/utils/generations";
import { FormItemValue, simplifyFormItem } from "@/ee/utils/input-utils";
import { useFeatureAccess } from "@/hooks/use-featureaccess";
import { GenerationTab } from "@/types/generations";
import { GenerationPublic, PlaygroundParameters } from "@/types/types";
import { Construction } from "lucide-react";
import { Suspense, useState } from "react";

export const Route = createFileRoute(
  "/_auth/projects/$projectUuid/generations/$generationName/_workbench/compare/$firstGenerationUuid/$secondGenerationUuid/$tab"
)({
  component: () => (
    <Suspense fallback={<LilypadLoading />}>
      <Generation />
    </Suspense>
  ),
});

// Component to handle both playgrounds with a shared run button
const ComparePlaygrounds = ({
  firstGeneration,
  secondGeneration,
}: {
  firstGeneration: GenerationPublic;
  secondGeneration: GenerationPublic;
}) => {
  const [firstResponse, setFirstResponse] = useState<string>("");
  const [secondResponse, setSecondResponse] = useState<string>("");
  const [isRunning, setIsRunning] = useState(false);
  // Set up hooks for both generations
  const firstPlayground = usePlaygroundContainer({
    version: firstGeneration,
    isCompare: true,
  });
  const secondPlayground = usePlaygroundContainer({
    version: secondGeneration,
    isCompare: true,
  });

  const runMutation = useRunMutation();

  // Check if either playground has missing API keys
  const canRun =
    firstPlayground.doesProviderExist && secondPlayground.doesProviderExist;

  const runBothGenerations = async () => {
    setIsRunning(true);

    try {
      // Run both generations in parallel
      await Promise.all([
        runGeneration(firstPlayground, firstGeneration.uuid, (response) =>
          setFirstResponse(response)
        ),
        runGeneration(secondPlayground, secondGeneration.uuid, (response) =>
          setSecondResponse(response)
        ),
      ]);
    } catch (error) {
      console.error("Error running generations:", error);
    } finally {
      setIsRunning(false);
    }
  };

  // Helper function to run a single generation
  const runGeneration = async (
    playground: ReturnType<typeof usePlaygroundContainer>,
    generationUuid: string,
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

        // Run generation
        const result = await runMutation.mutateAsync({
          projectUuid,
          generationUuid,
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
                onClick={runBothGenerations}
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
            version={firstGeneration}
            response={firstResponse}
            isCompare={true}
            playgroundContainer={firstPlayground}
          />
        </div>

        <div className='flex-1'>
          <Playground
            version={secondGeneration}
            response={secondResponse}
            isCompare={true}
            playgroundContainer={secondPlayground}
          />
        </div>
      </div>
    </div>
  );
};

const Generation = () => {
  const { projectUuid, firstGenerationUuid, secondGenerationUuid, tab } =
    useParams({
      from: Route.id,
    });
  if (tab === GenerationTab.OVERVIEW) {
    return <GenerationOverview />;
  } else if (tab === GenerationTab.TRACES) {
    return (
      <CompareTracesTable
        projectUuid={projectUuid}
        firstGenerationUuid={firstGenerationUuid}
        secondGenerationUuid={secondGenerationUuid}
      />
    );
  } else if (tab === GenerationTab.ANNOTATIONS) {
    return (
      <div className='flex justify-center items-center h-96'>
        <Construction color='orange' /> This page is under construction{" "}
        <Construction color='orange' />
      </div>
    );
  }
};
const GenerationOverview = () => {
  const { projectUuid, generationName, generationUuid, secondGenerationUuid } =
    useParams({
      from: Route.id,
    });
  const { data: generations } = useSuspenseQuery(
    generationsByNameQueryOptions(generationName, projectUuid)
  );
  const features = useFeatureAccess();
  const firstGeneration = generations.find(
    (generation) => generation.uuid === generationUuid
  );
  const secondGeneration = generations.find(
    (generation) => generation.uuid === secondGenerationUuid
  );

  if (!firstGeneration || !secondGeneration) {
    return <div>Please select two generations to compare.</div>;
  } else {
    return (
      <div className='p-4 flex flex-col gap-6 max-w-6xl mx-auto'>
        <Suspense fallback={<CardSkeleton />}>
          <MetricCharts
            generation={firstGeneration}
            secondGeneration={secondGeneration}
            projectUuid={projectUuid}
          />
        </Suspense>
        <div className='text-left'>
          <Label className='text-lg font-semibold'>Code Comparison</Label>
          <DiffTool
            firstLexicalClosure={firstGeneration.code}
            secondLexicalClosure={secondGeneration.code}
          />
        </div>
        {features.managedGenerations &&
          firstGeneration.is_managed &&
          secondGeneration.is_managed && (
            <div className='text-left'>
              <Label className='text-lg font-semibold'>
                Compare Generations
              </Label>
              <ComparePlaygrounds
                firstGeneration={firstGeneration}
                secondGeneration={secondGeneration}
              />
            </div>
          )}
      </div>
    );
  }
};
