import { CompareTracesTable } from "@/components/CompareTracesTable";
import { FunctionOverviewUI } from "@/components/functions/FunctionOverviewUI";
import { SelectFunction } from "@/components/functions/SelectFunction";
import { LilypadLoading } from "@/components/LilypadLoading";
import { NotFound } from "@/components/NotFound";
import { Tab, TabGroup } from "@/components/TabGroup";
import TableSkeleton from "@/components/TableSkeleton";
import { Button } from "@/components/ui/button";
import { Typography } from "@/components/ui/typography";
import { useFeatureAccess } from "@/hooks/use-featureaccess";
import { FunctionTab } from "@/types/functions";
import { functionsByNameQueryOptions } from "@/utils/functions";
import { useSuspenseQuery } from "@tanstack/react-query";
import { createFileRoute, useNavigate, useParams } from "@tanstack/react-router";
import { ArrowLeft, GitCompare, MoveLeft, SquareTerminal } from "lucide-react";
import { Suspense, useState } from "react";
import { toast } from "sonner";

export const Route = createFileRoute(
  "/_auth/projects/$projectUuid/functions/$functionName/_workbench/compare/$firstFunctionUuid/$secondFunctionUuid/$tab"
)({
  component: () => (
    <Suspense fallback={<LilypadLoading />}>
      <CompareWorkbench />
    </Suspense>
  ),
});

const CompareWorkbench = () => {
  const { projectUuid, functionName, firstFunctionUuid, secondFunctionUuid, tab } = useParams({
    from: Route.id,
  });
  const { data: functions } = useSuspenseQuery(
    functionsByNameQueryOptions(functionName, projectUuid)
  );
  const [compareMode, setCompareMode] = useState<boolean>(true);
  const features = useFeatureAccess();
  const navigate = useNavigate();
  const firstFunction = functions.find((f) => f.uuid === firstFunctionUuid);
  const secondFunction = functions.find((f) => f.uuid === secondFunctionUuid);

  const tabs: Tab[] = [
    {
      label: "Overview",
      value: FunctionTab.OVERVIEW,
      isDisabled: !features.functions,
      component: <CompareOverview />,
    },
    {
      label: "Traces",
      value: FunctionTab.TRACES,
      isDisabled: !features.traces,
      component:
        firstFunction && secondFunction ? (
          <Suspense fallback={<TableSkeleton />}>
            <CompareTracesTable
              projectUuid={projectUuid}
              firstFunctionUuid={firstFunctionUuid}
              secondFunctionUuid={secondFunctionUuid}
            />
          </Suspense>
        ) : null,
    },
    {
      label: "Annotations",
      value: FunctionTab.ANNOTATIONS,
      isDisabled: !features.annotations,
      component: (
        <div className="flex h-full w-full items-center justify-center">
          <Typography variant="h4">Under construction...</Typography>
        </div>
      ),
    },
  ];

  const handleTabChange = (newTab: string) => {
    navigate({
      to: `/projects/${projectUuid}/functions/${functionName}/compare/${firstFunctionUuid}/${secondFunctionUuid}/${newTab}`,
    }).catch(() => toast.error("Failed to navigate"));
  };

  const handlePlaygroundButtonClick = () => {
    navigate({
      to: `/projects/${projectUuid}/playground/${functionName}/compare/${firstFunctionUuid}/${secondFunctionUuid}`,
    }).catch(() => toast.error("Failed to navigate to playground"));
  };

  const handleBackButton = () => {
    navigate({
      to: `/projects/${projectUuid}/functions`,
    }).catch(() => toast.error("Failed to navigate to functions"));
  };

  const handleCompareToggle = () => {
    navigate({
      to: `/projects/${projectUuid}/functions/${functionName}/${firstFunctionUuid}/${tab}`,
    }).catch(() => toast.error("Failed to navigate to function page"));
    setCompareMode(false);
  };

  if (!firstFunction || !secondFunction) {
    return <NotFound />;
  }

  return (
    <div className="flex h-screen flex-col gap-2 px-4 pt-4 pb-1">
      <div className="shrink-0">
        <Button variant="ghost" onClick={handleBackButton}>
          <MoveLeft className="size-4" />
          Back to Functions
        </Button>
      </div>
      <div className="flex shrink-0 justify-between">
        <div className="flex items-center gap-2">
          <Typography variant="h3">{functionName}</Typography>
          <SelectFunction
            compareMode={compareMode}
            isFirstFunction={true}
            firstFunctionUuid={firstFunctionUuid}
            secondFunctionUuid={secondFunctionUuid}
            functionName={functionName}
            projectUuid={projectUuid}
            tab={tab as FunctionTab}
          />
          <ArrowLeft className="size-4" />
          <SelectFunction
            compareMode={compareMode}
            isFirstFunction={false}
            firstFunctionUuid={firstFunctionUuid}
            secondFunctionUuid={secondFunctionUuid}
            functionName={functionName}
            projectUuid={projectUuid}
            tab={tab as FunctionTab}
          />
        </div>
        <div className="flex gap-2">
          <Button variant="secondary" onClick={handleCompareToggle}>
            <GitCompare /> Compare
          </Button>
          <Button variant="outline" onClick={handlePlaygroundButtonClick}>
            <SquareTerminal className="size-4" />
            Go to playground
          </Button>
        </div>
      </div>
      <div className="min-h-0 flex-1">
        <TabGroup tabs={tabs} tab={tab} handleTabChange={handleTabChange} />
      </div>
    </div>
  );
};

const CompareOverview = () => {
  const { projectUuid, functionName, firstFunctionUuid, secondFunctionUuid } = useParams({
    from: Route.id,
  });
  const { data: functions } = useSuspenseQuery(
    functionsByNameQueryOptions(functionName, projectUuid)
  );
  const firstFunction = functions.find((f) => f.uuid === firstFunctionUuid);
  const secondFunction = functions.find((f) => f.uuid === secondFunctionUuid);

  if (!firstFunction || !secondFunction) {
    return <div>Please select two functions to compare.</div>;
  }

  return (
    <FunctionOverviewUI
      projectUuid={projectUuid}
      firstFunction={firstFunction}
      secondFunction={secondFunction}
      isCompare={true}
    />
  );
};
