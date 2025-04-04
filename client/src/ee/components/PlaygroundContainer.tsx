import {
  ResizableHandle,
  ResizablePanel,
  ResizablePanelGroup,
} from "@/components/ui/resizable";
import { Playground } from "@/ee/components/Playground";
import { usePlaygroundContainer } from "@/ee/hooks/use-playground";
import { FunctionPublic } from "@/types/types";
import { useState, Suspense } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { LilypadPanel } from "@/components/LilypadPanel";
import CardSkeleton from "@/components/CardSkeleton";

interface PlaygroundContainerProps {
  version: FunctionPublic | null;
  isCompare: boolean;
}

export const PlaygroundContainer = ({
  version,
}: PlaygroundContainerProps) => {
  const playgroundContainer = usePlaygroundContainer({
    version,
  });

  const [isPanelCollapsed, setIsPanelCollapsed] = useState(false);

  const handleCollapse = () => {
    setIsPanelCollapsed(true);
  };

  return (
    <ResizablePanelGroup direction='horizontal'>
      <ResizablePanel
        order={1}
        className='p-2 flex flex-col gap-2 min-w-[500px]'
      >
        <Playground
          version={version}
          playgroundContainer={playgroundContainer}
        />
      </ResizablePanel>
      {playgroundContainer.executedSpanUuid && !isPanelCollapsed && (
        <>
          <ResizableHandle />
          <ResizablePanel
            order={2}
            style={{ overflowY: "auto" }}
            collapsible={true}
            minSize={12}
            onCollapse={handleCollapse}
            className='relative'
          >
            <Card>
              <CardHeader>
                <CardTitle>{"Execution Result"}</CardTitle>
              </CardHeader>
              <CardContent>
                <Suspense fallback={<CardSkeleton items={5} className='flex flex-col' />}>
                  <LilypadPanel spanUuid={playgroundContainer.executedSpanUuid} />
                </Suspense>
              </CardContent>
            </Card>
          </ResizablePanel>
        </>
      )}
    </ResizablePanelGroup>
  );
};