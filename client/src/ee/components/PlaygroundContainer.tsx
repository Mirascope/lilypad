import {
  ResizableHandle,
  ResizablePanel,
  ResizablePanelGroup,
} from "@/components/ui/resizable";
import { Playground } from "@/ee/components/Playground";
import { usePlaygroundContainer } from "@/ee/hooks/use-playground";
import { FunctionPublic } from "@/types/types";
import { useState } from "react";
interface PlaygroundContainerProps {
  version: FunctionPublic | null;
  isCompare: boolean;
}

export const PlaygroundContainer = ({
  version,
  isCompare,
}: PlaygroundContainerProps) => {
  const playgroundContainer = usePlaygroundContainer({
    version,
    isCompare,
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
      {playgroundContainer.spanUuid && !isPanelCollapsed && (
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
            <div>This is a placeholder</div>
          </ResizablePanel>
        </>
      )}
    </ResizablePanelGroup>
  );
};
