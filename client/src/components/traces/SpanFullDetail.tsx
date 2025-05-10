import { useSuspenseQuery } from "@tanstack/react-query";
import { Minimize2 } from "lucide-react";
import { Suspense } from "react";

import CardSkeleton from "@/components/CardSkeleton";
import { LilypadMetrics, LilypadPanel } from "@/components/LilypadPanel";
import { FunctionTitle } from "@/components/traces/FunctionTitle";
import { TraceTree } from "@/components/traces/TraceTree";
import { Button } from "@/components/ui/button";
import {
  ResizableHandle,
  ResizablePanel,
  ResizablePanelGroup,
} from "@/components/ui/resizable";
import { Typography } from "@/components/ui/typography";
import { SpanComments } from "@/utils/panel-utils";
import { spanQueryOptions } from "@/utils/spans";
import { rootTraceQueryOptions } from "@/utils/traces";

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
  const { data: trace } = useSuspenseQuery(
    rootTraceQueryOptions(projectUuid, span.span_id)
  );

  return (
    <div className="container h-screen w-full pt-4 px-4 max-w-screen-2xl overflow-hidden">
      <ResizablePanelGroup direction="horizontal" className="h-full">
        <ResizablePanel defaultSize={25} minSize={15} className="flex flex-col">
          <Typography variant="h3" className="truncate max-w-md mb-4 shrink-0">
            Trace Hierarchy
          </Typography>
          <div className="overflow-y-auto flex-1 min-h-0">
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

        <ResizablePanel
          defaultSize={75}
          minSize={50}
          className="flex flex-col h-full"
        >
          <div className="flex justify-between items-center mb-4 shrink-0">
            <FunctionTitle span={span} />
            <div className="flex gap-2">
              <Button
                onClick={handleBackToTraces}
                variant="outline"
                size="sm"
                className="flex gap-2 items-center"
              >
                <Minimize2 className="h-4 w-4" />
                <span className="hidden sm:inline">Back to Traces</span>
              </Button>
            </div>
          </div>

          <ResizablePanelGroup
            direction="horizontal"
            className="flex-1 min-h-0 h-full overflow-hidden"
          >
            <ResizablePanel
              defaultSize={65}
              minSize={40}
              className="overflow-hidden"
            >
              <div className="h-full overflow-y-auto">
                <LilypadPanel spanUuid={spanUuid} showMetrics={false} />
              </div>
            </ResizablePanel>

            <ResizableHandle withHandle className="m-4" />

            <ResizablePanel
              defaultSize={35}
              minSize={25}
              className="flex flex-col overflow-hidden h-full gap-4"
            >
              <div className="shrink-0">
                <LilypadMetrics span={span} />
              </div>
              <div className="flex-1 min-h-0">
                <Suspense fallback={<CardSkeleton items={1} />}>
                  <SpanComments
                    projectUuid={projectUuid}
                    spanUuid={span.uuid}
                  />
                </Suspense>
              </div>
            </ResizablePanel>
          </ResizablePanelGroup>
        </ResizablePanel>
      </ResizablePanelGroup>
    </div>
  );
};
