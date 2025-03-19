import { CodeSnippet } from "@/components/CodeSnippet";
import { Label } from "@/components/ui/label";
import { generationsByNameQueryOptions } from "@/utils/generations";
import { useSuspenseQuery } from "@tanstack/react-query";
import {
  createFileRoute,
  useParams,
  useRouterState,
} from "@tanstack/react-router";

import CardSkeleton from "@/components/CardSkeleton";
import { GenerationSpans } from "@/components/GenerationSpans";
import { LilypadLoading } from "@/components/LilypadLoading";
import { MetricCharts } from "@/components/MetricsCharts";
import { NotFound } from "@/components/NotFound";
import { GenerationAnnotations } from "@/ee/components/GenerationAnnotations";
import { Playground } from "@/ee/components/Playground";
import { useFeatureAccess } from "@/hooks/use-featureaccess";
import { GenerationTab } from "@/types/generations";
import { Suspense } from "react";

export const Route = createFileRoute(
  "/_auth/projects/$projectUuid/generations/$generationName/_workbench/$generationUuid/$tab"
)({
  component: () => (
    <Suspense fallback={<LilypadLoading />}>
      <Generation />
    </Suspense>
  ),
});

const Generation = () => {
  const { projectUuid, generationName, generationUuid, tab } = useParams({
    from: Route.id,
  });
  const { data: generations } = useSuspenseQuery(
    generationsByNameQueryOptions(generationName, projectUuid)
  );
  const generation = generations.find(
    (generation) => generation.uuid === generationUuid
  );
  if (tab === GenerationTab.OVERVIEW) {
    return <GenerationOverview />;
  } else if (tab === GenerationTab.TRACES) {
    return (
      <GenerationSpans
        projectUuid={projectUuid}
        generationUuid={generation?.uuid}
      />
    );
  } else if (tab === GenerationTab.ANNOTATIONS) {
    return (
      <GenerationAnnotations
        projectUuid={projectUuid}
        generationUuid={generation?.uuid}
      />
    );
  }
};

const GenerationOverview = () => {
  const { projectUuid, generationName, generationUuid } = useParams({
    from: Route.id,
  });
  const { data: generations } = useSuspenseQuery(
    generationsByNameQueryOptions(generationName, projectUuid)
  );
  const state = useRouterState({ select: (s) => s.location.state });
  const features = useFeatureAccess();
  const generation = generations.find(
    (generation) => generation.uuid === generationUuid
  );

  if (!generation) {
    return <NotFound />;
  } else {
    return (
      <div className='p-4 flex flex-col gap-2 max-w-4xl mx-auto'>
        <Suspense fallback={<CardSkeleton />}>
          <MetricCharts generation={generation} projectUuid={projectUuid} />
        </Suspense>
        <div className='text-left'>
          <Label>Code</Label>
          <CodeSnippet code={generation.code} />
        </div>

        {features.managedGenerations && generation.is_managed && (
          <div className='text-left'>
            <Label>Prompt Template</Label>
            <Playground version={generation} response={state.result} />
          </div>
        )}
      </div>
    );
  }
};
