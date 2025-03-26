import { CodeSnippet } from "@/components/CodeSnippet";
import { Label } from "@/components/ui/label";
import { functionsByNameQueryOptions } from "@/utils/functions";
import { useSuspenseQuery } from "@tanstack/react-query";
import { createFileRoute, useParams } from "@tanstack/react-router";

import CardSkeleton from "@/components/CardSkeleton";
import { FunctionSpans } from "@/components/FunctionSpans";
import { LilypadLoading } from "@/components/LilypadLoading";
import { MetricCharts } from "@/components/MetricsCharts";
import { NotFound } from "@/components/NotFound";
import { FunctionAnnotations } from "@/ee/components/FunctionAnnotations";
import { Route as FunctionRoute } from "@/routes/_auth/projects/$projectUuid/functions/$functionName/_workbench/route";
import { FunctionTab } from "@/types/functions";
import { Suspense } from "react";

export const Route = createFileRoute(
  "/_auth/projects/$projectUuid/functions/$functionName/_workbench/$functionUuid/$tab"
)({
  component: () => (
    <Suspense fallback={<LilypadLoading />}>
      <Function />
    </Suspense>
  ),
});

const Function = () => {
  const { projectUuid, functionName, functionUuid, tab } = useParams({
    from: FunctionRoute.id,
  });
  const { data: functions } = useSuspenseQuery(
    functionsByNameQueryOptions(functionName, projectUuid)
  );
  const fn = functions.find((f) => f.uuid === functionUuid);
  if (tab === FunctionTab.OVERVIEW) {
    return <FunctionOverview />;
  } else if (tab === FunctionTab.TRACES) {
    return fn ? (
      <FunctionSpans projectUuid={projectUuid} functionUuid={fn.uuid} />
    ) : (
      <div>No function selected</div>
    );
  } else if (tab === FunctionTab.ANNOTATIONS) {
    return fn ? (
      <FunctionAnnotations projectUuid={projectUuid} functionUuid={fn.uuid} />
    ) : (
      <div>No function selected</div>
    );
  }
};

const FunctionOverview = () => {
  const { projectUuid, functionName, functionUuid } = useParams({
    from: Route.id,
  });
  const { data: functions } = useSuspenseQuery(
    functionsByNameQueryOptions(functionName, projectUuid)
  );
  const fn = functions.find((f) => f.uuid === functionUuid);

  if (!fn) {
    return <NotFound />;
  } else {
    return (
      <div className='p-4 flex flex-col gap-2 max-w-4xl mx-auto'>
        <Suspense fallback={<CardSkeleton />}>
          <MetricCharts firstFunction={fn} projectUuid={projectUuid} />
        </Suspense>
        <div className='text-left'>
          <Label>Code</Label>
          <CodeSnippet code={fn.code} />
        </div>
      </div>
    );
  }
};
