import { FunctionOverview } from "@/components/functions/FunctionOverview";
import { SelectFunction } from "@/components/functions/SelectFunction";
import { FunctionSpansContainer } from "@/components/FunctionSpans";
import LilypadDialog from "@/components/LilypadDialog";
import { LilypadLoading } from "@/components/LilypadLoading";
import { NotFound } from "@/components/NotFound";
import { Tab, TabGroup } from "@/components/TabGroup";
import TableSkeleton from "@/components/TableSkeleton";
import { Button } from "@/components/ui/button";
import { Typography } from "@/components/ui/typography";
import { useFeatureAccess } from "@/hooks/use-featureaccess";
import { FunctionTab } from "@/types/functions";
import {
  functionsByNameQueryOptions,
  useArchiveFunctionMutation,
} from "@/utils/functions";
import { useSuspenseQuery } from "@tanstack/react-query";
import {
  createFileRoute,
  useNavigate,
  useParams,
} from "@tanstack/react-router";
import { GitCompare, MoveLeft, SquareTerminal, Trash } from "lucide-react";
import { Suspense, useState } from "react";
import { toast } from "sonner";

export const Route = createFileRoute(
  "/_auth/projects/$projectUuid/functions/$functionName/_workbench/$functionUuid/$tab/$"
)({
  component: () => (
    <Suspense fallback={<LilypadLoading />}>
      <FunctionWorkbench />
    </Suspense>
  ),
});

const FunctionWorkbench = () => {
  const { projectUuid, functionName, functionUuid, tab } = useParams({
    from: Route.id,
  });
  const { data: functions } = useSuspenseQuery(
    functionsByNameQueryOptions(functionName, projectUuid)
  );
  const isCompare = false;
  const [compareMode, setCompareMode] = useState<boolean>(false);
  const [secondFunctionUuid, setSecondFunctionUuid] = useState<string>("");
  const features = useFeatureAccess();
  const navigate = useNavigate();
  const fn = functions.find((f) => f.uuid === functionUuid);
  const archiveFunction = useArchiveFunctionMutation();
  const tabs: Tab[] = [
    {
      label: "Overview",
      value: FunctionTab.OVERVIEW,
      isDisabled: !features.functions,
      component: <FunctionOverview />,
    },
    {
      label: "Traces",
      value: FunctionTab.TRACES,
      isDisabled: !features.traces,
      component: fn ? (
        <Suspense fallback={<TableSkeleton />}>
          <FunctionSpansContainer functionUuid={fn.uuid} />
        </Suspense>
      ) : null,
    },
    {
      label: "Annotations",
      value: FunctionTab.ANNOTATIONS,
      isDisabled: !features.annotations,
    },
  ];
  const handleArchive = async () => {
    if (!fn) return;
    await archiveFunction.mutateAsync({
      projectUuid,
      functionUuid: fn.uuid,
      functionName,
    });
    navigate({ to: `/projects/${projectUuid}/functions` }).catch(() =>
      toast.error("Failed to navigate")
    );
  };

  const handleTabChange = (newTab: string) => {
    if (compareMode && secondFunctionUuid) {
      navigate({
        to: `/projects/${projectUuid}/functions/${functionName}/compare/${functionUuid}/${secondFunctionUuid}/${newTab}`,
      }).catch(() => toast.error("Failed to navigate"));
    } else {
      navigate({
        to: `/projects/${projectUuid}/functions/${functionName}/${functionUuid}/${newTab}`,
      }).catch(() => toast.error("Failed to navigate"));
    }
  };
  const handlePlaygroundButtonClick = () => {
    navigate({
      to: `/projects/${projectUuid}/playground/${functionName}/${functionUuid}`,
    }).catch(() => toast.error("Failed to navigate to playground"));
  };
  const handleBackButton = () => {
    navigate({
      to: `/projects/${projectUuid}/functions`,
    }).catch(() => toast.error("Failed to navigate to functions"));
  };
  if (!fn) {
    return <NotFound />;
  }
  return (
    <div className="pt-4 pb-1 h-screen flex flex-col px-4 gap-2">
      <div className="shrink-0">
        <Button variant="ghost" onClick={handleBackButton}>
          <MoveLeft className="size-4" />
          Back to Functions
        </Button>
      </div>
      <div className="flex justify-between shrink-0">
        <div className="flex items-center gap-1">
          <Typography variant="h3">{functionName}</Typography>
          <SelectFunction
            compareMode={compareMode}
            isFirstFunction={true}
            firstFunctionUuid={fn.uuid}
            functionName={functionName}
            projectUuid={projectUuid}
            tab={tab as FunctionTab}
          />
          {compareMode && (
            <>
              <Typography variant="span" affects="muted">
                vs
              </Typography>
              <SelectFunction
                compareMode={compareMode}
                isFirstFunction={false}
                firstFunctionUuid={functionUuid}
                secondFunctionUuid={secondFunctionUuid}
                functionName={functionName}
                projectUuid={projectUuid}
                tab={tab as FunctionTab}
                onSecondFunctionChange={(uuid) => {
                  setSecondFunctionUuid(uuid);
                  if (uuid) {
                    navigate({
                      to: `/projects/${projectUuid}/functions/${functionName}/compare/${functionUuid}/${uuid}/${tab}`,
                    }).catch(() =>
                      toast.error("Failed to navigate to compare page")
                    );
                  }
                }}
              />
            </>
          )}
        </div>
        <div>
          {fn && (
            <Button
              variant="outline"
              size="icon"
              onClick={() => {
                if (!compareMode) {
                  // Toggle on compare mode
                  setCompareMode(true);
                  // We don't navigate yet - user needs to select second function first
                } else if (compareMode && secondFunctionUuid) {
                  // Navigate back to single function view
                  navigate({
                    to: `/projects/${projectUuid}/functions/${functionName}/${functionUuid}/${tab}`,
                  }).catch(() =>
                    toast.error("Failed to navigate to function page")
                  );
                  setCompareMode(false);
                  setSecondFunctionUuid("");
                }
              }}
            >
              <GitCompare />
            </Button>
          )}
          {fn && !isCompare && (
            <LilypadDialog
              icon={<Trash />}
              title={`Delete ${fn.name} v${fn.version_num}`}
              description=""
              dialogContentProps={{
                className: "max-w-[600px]",
              }}
              buttonProps={{
                variant: "outlineDestructive",
                className: "w-9 h-9",
              }}
              dialogButtons={[
                <Button
                  key="delete-function"
                  type="button"
                  variant="destructive"
                  onClick={handleArchive}
                >
                  Delete
                </Button>,
                <Button
                  key="cancel-delete-button"
                  type="button"
                  variant="outline"
                >
                  Cancel
                </Button>,
              ]}
            >
              {`Are you sure you want to delete ${fn.name} v${fn.version_num}?`}
            </LilypadDialog>
          )}
          <Button variant="outline" onClick={handlePlaygroundButtonClick}>
            <SquareTerminal className="size-4" />
            Go to playground
          </Button>
        </div>
      </div>
      <div className="flex-1 min-h-0">
        <TabGroup tabs={tabs} tab={tab} handleTabChange={handleTabChange} />
      </div>
    </div>
  );
};
