import { CodeSnippet } from "@/components/CodeSnippet";
import { Label } from "@/components/ui/label";
import { functionsByNameQueryOptions } from "@/utils/functions";
import { useSuspenseQuery } from "@tanstack/react-query";
import {
  createFileRoute,
  useNavigate,
  useParams,
} from "@tanstack/react-router";

import CardSkeleton from "@/components/CardSkeleton";
import { FunctionSpans } from "@/components/FunctionSpans";
import { LilypadLoading } from "@/components/LilypadLoading";
import { MetricCharts } from "@/components/MetricsCharts";
import { NotFound } from "@/components/NotFound";
import TableSkeleton from "@/components/TableSkeleton";
import { Button } from "@/components/ui/button";
import { AnnotationMetrics } from "@/ee/components/AnnotationMetrics";
import { FunctionAnnotations } from "@/ee/components/FunctionAnnotations";
import { useFeatureAccess } from "@/hooks/use-featureaccess";
import { useToast } from "@/hooks/use-toast";
import { Route as FunctionRoute } from "@/routes/_auth/projects/$projectUuid/functions/$functionName/_workbench/route";
import { FunctionTab } from "@/types/functions";
import { SquareTerminal } from "lucide-react";
import { Suspense } from "react";

export const Route = createFileRoute(
  "/_auth/projects/$projectUuid/functions/$functionName/_workbench/$functionUuid/$tab/$"
)({
  component: () => (
    <Suspense fallback={<LilypadLoading />}>
      <Function />
    </Suspense>
  ),
});

const Function = () => {
  const {
    projectUuid,
    functionName,
    functionUuid,
    tab,
    _splat: traceUuid,
  } = useParams({
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
      <Suspense fallback={<TableSkeleton />}>
        <FunctionSpans
          projectUuid={projectUuid}
          functionUuid={fn.uuid}
          traceUuid={traceUuid}
        />
      </Suspense>
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
  const features = useFeatureAccess();
  const navigate = useNavigate();
  const { toast } = useToast();
  const fn = functions.find((f) => f.uuid === functionUuid);
  const handlePlaygroundButtonClick = () => {
    navigate({
      to: `/projects/${projectUuid}/playground/${functionName}/${functionUuid}`,
    }).catch(() =>
      toast({
        title: "Failed to navigate",
      })
    );
  };
  if (!fn) {
    return <NotFound />;
  } else {
    return (
      <div className="p-2 flex flex-1 flex-col gap-2 max-w-4xl mx-auto">
        {features.annotations && (
          <AnnotationMetrics
            projectUuid={projectUuid}
            functionUuid={functionUuid}
          />
        )}
        <Suspense fallback={<CardSkeleton />}>
          <MetricCharts firstFunction={fn} projectUuid={projectUuid} />
        </Suspense>
        <div>
          <Label>Code</Label>
          <CodeSnippet code={fn.code} />
        </div>
        <div>
          <Button variant="outline" onClick={handlePlaygroundButtonClick}>
            <SquareTerminal className="w-4 h-4 mr-2" />
            Go to playground
          </Button>
        </div>
      </div>
    );
  }
};
