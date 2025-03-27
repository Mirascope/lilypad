import { Label } from "@/components/ui/label";
import { functionsByNameQueryOptions } from "@/utils/functions";
import { useSuspenseQuery } from "@tanstack/react-query";
import {
  createFileRoute,
  useNavigate,
  useParams,
} from "@tanstack/react-router";

import CardSkeleton from "@/components/CardSkeleton";
import { CompareTracesTable } from "@/components/CompareTracesTable";
import { LilypadLoading } from "@/components/LilypadLoading";
import { MetricCharts } from "@/components/MetricsCharts";
import { Button } from "@/components/ui/button";
import { DiffTool } from "@/ee/components/DiffTool";
import { useToast } from "@/hooks/use-toast";
import { Route as FunctionRoute } from "@/routes/_auth/projects/$projectUuid/functions/$functionName/_workbench/route";
import { FunctionTab } from "@/types/functions";
import { Construction, SquareTerminal } from "lucide-react";
import { Suspense } from "react";
export const Route = createFileRoute(
  "/_auth/projects/$projectUuid/functions/$functionName/_workbench/compare/$firstFunctionUuid/$secondFunctionUuid/$tab"
)({
  component: () => (
    <Suspense fallback={<LilypadLoading />}>
      <Function />
    </Suspense>
  ),
});

const Function = () => {
  const { projectUuid, functionUuid, secondFunctionUuid, tab } = useParams({
    from: FunctionRoute.id,
  });
  if (tab === FunctionTab.OVERVIEW) {
    return <FunctionOverview />;
  } else if (tab === FunctionTab.TRACES) {
    return (
      <CompareTracesTable
        projectUuid={projectUuid}
        firstFunctionUuid={functionUuid}
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
  const firstFunction = functions.find((f) => f.uuid === functionUuid);
  const secondFunction = functions.find((f) => f.uuid === secondFunctionUuid);
  const navigate = useNavigate();
  const { toast } = useToast();
  const handleComparePlaygroundButtonClick = () => {
    navigate({
      to: `/projects/${projectUuid}/playground/${functionName}/compare/${functionUuid}/${secondFunctionUuid}`,
    }).catch(() =>
      toast({
        title: "Failed to navigate",
      })
    );
  };
  if (!firstFunction || !secondFunction) {
    return <div>Please select two functions to compare.</div>;
  } else {
    return (
      <div className='p-4 flex flex-col gap-6'>
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
        <div>
          <Button
            variant='outline'
            onClick={handleComparePlaygroundButtonClick}
          >
            <SquareTerminal className='w-4 h-4 mr-2' />
            Go to playground
          </Button>
        </div>
      </div>
    );
  }
};
