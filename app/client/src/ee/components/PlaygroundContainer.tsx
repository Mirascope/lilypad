import CardSkeleton from "@/src/components/CardSkeleton";
import { LilypadPanel } from "@/src/components/traces/LilypadPanel";
import { Card, CardContent, CardHeader, CardTitle } from "@/src/components/ui/card";
import {
  ResizableHandle,
  ResizablePanel,
  ResizablePanelGroup,
} from "@/src/components/ui/resizable";
import { Playground } from "@/src/ee/components/Playground";
import { usePlaygroundContainer } from "@/src/ee/hooks/use-playground";
import { FunctionPublic, PlaygroundErrorDetail } from "@/src/types/types";
import { AlertTriangle } from "lucide-react";
import { Suspense, useEffect, useRef } from "react";
import { ImperativePanelHandle } from "react-resizable-panels";

const SimpleErrorDisplay = ({ error }: { error: PlaygroundErrorDetail }) => {
  return (
    <div className="rounded-md border border-red-200 bg-red-50 p-3">
      <div className="flex items-start">
        <div className="shrink-0">
          <AlertTriangle className="h-4 w-4 text-red-500" />
        </div>
        <div className="ml-2">
          <p className="text-sm text-red-700">{error.reason || "An unknown error occurred"}</p>
          {error.details && (
            <details className="mt-2">
              <summary className="cursor-pointer text-xs font-medium">Technical details</summary>
              <pre className="mt-2 overflow-auto rounded bg-red-100 p-2 text-xs break-all whitespace-pre-wrap">
                {typeof error.details === "object"
                  ? JSON.stringify(error.details, null, 2)
                  : error.details}
              </pre>
            </details>
          )}
        </div>
      </div>
    </div>
  );
};

interface PlaygroundContainerProps {
  version: FunctionPublic | null;
  isCompare: boolean;
}

export const PlaygroundContainer = ({ version, isCompare = false }: PlaygroundContainerProps) => {
  const playgroundContainer = usePlaygroundContainer({
    version,
  });

  const { executedSpanUuid, error, isRunLoading } = playgroundContainer;

  const rightPanelRef = useRef<ImperativePanelHandle>(null);
  const showRightPanel = Boolean(executedSpanUuid ?? error);

  // Auto-expand panel when results/errors are available
  useEffect(() => {
    if (showRightPanel && rightPanelRef.current) {
      if (rightPanelRef.current.isCollapsed()) {
        rightPanelRef.current.expand();
      }
    }
  }, [showRightPanel, executedSpanUuid, error]);

  return (
    <ResizablePanelGroup direction="horizontal" className="overflow-hidden rounded-lg border">
      <ResizablePanel
        defaultSize={showRightPanel ? 50 : 100}
        minSize={30}
        className="overflow-y-auto p-4"
      >
        <Playground
          version={version}
          isCompare={isCompare}
          playgroundContainer={playgroundContainer}
        />
      </ResizablePanel>

      {showRightPanel && (
        <>
          <ResizableHandle className="w-2 border-x bg-gray-100 hover:bg-gray-200" />
          <ResizablePanel ref={rightPanelRef} defaultSize={50} minSize={25} collapsible={true}>
            <div className="h-full overflow-y-auto p-4">
              <Card className="h-full">
                <CardHeader>
                  <CardTitle>Execution Result</CardTitle>
                </CardHeader>
                <CardContent>
                  {isRunLoading && <div className="text-gray-500">Running...</div>}
                  {!isRunLoading && error && <SimpleErrorDisplay error={error} />}
                  {!isRunLoading && !error && executedSpanUuid && (
                    <Suspense fallback={<CardSkeleton items={5} className="flex flex-col" />}>
                      <LilypadPanel spanUuid={executedSpanUuid} />
                    </Suspense>
                  )}
                  {!isRunLoading && !error && !executedSpanUuid && (
                    <div className="text-gray-500">No result yet</div>
                  )}
                </CardContent>
              </Card>
            </div>
          </ResizablePanel>
        </>
      )}
    </ResizablePanelGroup>
  );
};
