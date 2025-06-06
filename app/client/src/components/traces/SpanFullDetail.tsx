import { useSuspenseQuery } from "@tanstack/react-query";
import { Minimize2, Users } from "lucide-react";
import { Suspense } from "react";

import CardSkeleton from "@/src/components/CardSkeleton";
import LilypadDialog from "@/src/components/LilypadDialog";
import { FunctionTitle } from "@/src/components/traces/FunctionTitle";
import { LilypadPanel } from "@/src/components/traces/LilypadPanel";
import { SpanMetrics } from "@/src/components/traces/SpanMetrics";
import { TraceTree } from "@/src/components/traces/TraceTree";
import { Button } from "@/src/components/ui/button";
import {
  ResizableHandle,
  ResizablePanel,
  ResizablePanelGroup,
} from "@/src/components/ui/resizable";
import { Typography } from "@/src/components/ui/typography";
import { QueueForm } from "@/src/ee/components/QueueForm";
import { useFeatureAccess } from "@/src/hooks/use-featureaccess";
import { SpanComments } from "@/src/utils/panel-utils";
import { spanQueryOptions } from "@/src/utils/spans";
import { rootTraceQueryOptions } from "@/src/utils/traces";

export const SpanFullDetail = ({
  projectUuid,
  spanUuid,
  handleBackToTraces,
}: {
  projectUuid: string;
  spanUuid: string;
  handleBackToTraces: () => void;
}) => {
  const { data: span } = useSuspenseQuery(spanQueryOptions(spanUuid));
  const { data: trace } = useSuspenseQuery(rootTraceQueryOptions(projectUuid, span.span_id));
  const features = useFeatureAccess();

  return (
    <ResizablePanelGroup direction="horizontal" className="h-full p-4">
      <ResizablePanel defaultSize={25} minSize={15} className="flex flex-col">
        <Typography variant="h3" className="mb-4 max-w-md shrink-0 truncate">
          Trace Hierarchy
        </Typography>
        <div className="min-h-0 flex-1 overflow-y-auto">
          <Suspense fallback={<CardSkeleton items={1} />}>
            <TraceTree
              span={trace}
              projectUuid={projectUuid}
              currentSpanUuid={spanUuid}
              level={0}
            />
          </Suspense>
        </div>
      </ResizablePanel>

      <ResizableHandle withHandle className="m-4" />

      <ResizablePanel defaultSize={75} minSize={50} className="flex h-full flex-col">
        <div className="mb-4 flex shrink-0 items-center justify-between">
          <FunctionTitle span={span} />
          <div className="flex gap-2">
            {features.annotations && (
              <LilypadDialog
                icon={<Users />}
                text={"Assign"}
                title={"Annotate selected traces"}
                description={`1 trace(s) selected.`}
                tooltipContent={"Add trace to your annotation queue."}
              >
                <QueueForm spans={[span]} />
              </LilypadDialog>
            )}
            <Button
              onClick={handleBackToTraces}
              variant="outline"
              size="sm"
              className="flex items-center gap-2"
            >
              <Minimize2 className="h-4 w-4" />
              <span className="hidden sm:inline">Back to Traces</span>
            </Button>
          </div>
        </div>

        <ResizablePanelGroup
          direction="horizontal"
          className="h-full min-h-0 flex-1 overflow-hidden"
        >
          <ResizablePanel defaultSize={65} minSize={40} className="overflow-hidden">
            <div className="h-full overflow-y-auto">
              <LilypadPanel spanUuid={spanUuid} showMetrics={false} />
            </div>
          </ResizablePanel>

          <ResizableHandle withHandle className="m-4" />

          <ResizablePanel
            defaultSize={35}
            minSize={25}
            className="flex h-full flex-col gap-4 overflow-hidden"
          >
            <div className="shrink-0">
              <SpanMetrics span={span} />
            </div>
            <div className="min-h-0 flex-1">
              <Suspense fallback={<CardSkeleton items={1} />}>
                <SpanComments projectUuid={projectUuid} spanUuid={span.uuid} />
              </Suspense>
            </div>
          </ResizablePanel>
        </ResizablePanelGroup>
      </ResizablePanel>
    </ResizablePanelGroup>
  );
};
