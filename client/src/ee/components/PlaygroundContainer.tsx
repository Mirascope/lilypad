import {
  ResizableHandle,
  ResizablePanel,
  ResizablePanelGroup,
} from "@/components/ui/resizable";
import { Playground } from "@/ee/components/Playground";
import { usePlaygroundContainer } from "@/ee/hooks/use-playground";
import { FunctionPublic, PlaygroundErrorDetail } from "@/types/types";
import { useRef, useEffect, Suspense } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { LilypadPanel } from "@/components/LilypadPanel";
import CardSkeleton from "@/components/CardSkeleton";
import { AlertTriangle } from "lucide-react";
import { ImperativePanelHandle } from "react-resizable-panels";

const SimpleErrorDisplay = ({ error }: { error: PlaygroundErrorDetail }) => {
  return (
    <div className="bg-red-50 border border-red-200 rounded-md p-3">
      <div className="flex items-start">
        <div className="flex-shrink-0">
          <AlertTriangle className="h-4 w-4 text-red-500" />
        </div>
        <div className="ml-2">
          <p className="text-sm text-red-700">{error.reason || "An unknown error occurred"}</p>
          {error.details && (
            <details className="mt-2">
              <summary className="cursor-pointer text-xs font-medium">Technical details</summary>
              <pre className="mt-2 text-xs p-2 bg-red-100 rounded overflow-auto whitespace-pre-wrap break-all">
                {typeof error.details === 'object' ? JSON.stringify(error.details, null, 2) : error.details}
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

export const PlaygroundContainer = ({
  version,
  isCompare = false,
}: PlaygroundContainerProps) => {
  const playgroundContainer = usePlaygroundContainer({
    version,
  });

  const {
    executedSpanUuid,
    error,
    isRunLoading
  } = playgroundContainer;

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
    <ResizablePanelGroup direction="horizontal" className="border rounded-lg overflow-hidden">
      <ResizablePanel
        defaultSize={showRightPanel ? 50 : 100}
        minSize={30}
        className="p-4 overflow-y-auto"
      >
        <Playground
          version={version}
          isCompare={isCompare}
          playgroundContainer={playgroundContainer}
        />
      </ResizablePanel>

      {showRightPanel && (
        <>
          <ResizableHandle className="w-2 bg-gray-100 hover:bg-gray-200 border-x" />
          <ResizablePanel
            ref={rightPanelRef}
            defaultSize={50}
            minSize={25}
            collapsible={true}
          >
            <div className="p-4 h-full overflow-y-auto">
              <Card className="h-full">
                <CardHeader>
                  <CardTitle>Execution Result</CardTitle>
                </CardHeader>
                <CardContent>
                  {isRunLoading && (
                    <div className="text-gray-500">Running...</div>
                  )}
                  {!isRunLoading && error && (
                    <SimpleErrorDisplay error={error} />
                  )}
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