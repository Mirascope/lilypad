import { CodeSnippet } from "@/components/CodeSnippet";
import { Label } from "@/components/ui/label";
import { generationsByNameQueryOptions } from "@/utils/generations";
import { useSuspenseQuery } from "@tanstack/react-query";
import { createFileRoute, useParams } from "@tanstack/react-router";

import CardSkeleton from "@/components/CardSkeleton";
import { MetricCharts } from "@/components/MetricsCharts";
import { NotFound } from "@/components/NotFound";
import { Playground } from "@/ee/components/Playground";
import { useFeatureAccess } from "@/hooks/use-featureaccess";
import { Suspense } from "react";

export const Route = createFileRoute(
  "/_auth/projects/$projectUuid/generations/$generationName/_workbench/$generationUuid/$tab"
)({
  component: () => (
    <Suspense fallback={<div>Loading...</div>}>
      <Generation />
    </Suspense>
  ),
});

const Generation = () => {
  const { projectUuid, generationName, generationUuid } = useParams({
    from: Route.id,
  });
  const { data: generations } = useSuspenseQuery(
    generationsByNameQueryOptions(generationName, projectUuid)
  );

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
          <MetricCharts
            generationUuid={generation.uuid}
            projectUuid={projectUuid}
          />
        </Suspense>
        <div className='text-left'>
          <Label>Code</Label>
          <CodeSnippet code={generation.code} />
        </div>

        {features.managedGenerations && generation.is_managed && (
          <div className='text-left'>
            <Label>Prompt Template</Label>
            <Playground version={generation} />
          </div>
        )}
      </div>
    );
  }
};
