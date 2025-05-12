import CardSkeleton from "@/components/CardSkeleton";
import {
  ResizableHandle,
  ResizablePanel,
  ResizablePanelGroup,
} from "@/components/ui/resizable";
import { TableContextType, useTable } from "@/hooks/use-table";
import { cn } from "@/lib/utils";
import { ReactNode, Suspense } from "react";

type DetailContentRenderer<T> = (data: T) => ReactNode;

interface ResizablePanelsProps<T> {
  /**
   * Primary content to display in the left panel
   */
  primaryContent: ReactNode;

  /**
   * Detail content to display in the right panel when a row is selected
   * This is now optional - if not provided, detailContentRenderer will be used
   */
  detailContent?: ReactNode;

  /**
   * Alternative way to render detail content based on the selected row
   * This is used to explicitly reference T and avoid the TypeScript warning
   */
  detailContentRenderer?: DetailContentRenderer<T>;

  /**
   * Default size of the primary panel when detail panel is visible
   */
  defaultPrimarySize?: number;

  /**
   * Default size of the detail panel when visible
   */
  defaultDetailSize?: number;

  /**
   * Minimum size of the detail panel
   */
  minDetailSize?: number;

  /**
   * CSS class to apply to the container
   */
  className?: string;

  /**
   * CSS class to apply to the primary panel
   */
  primaryClassName?: string;

  /**
   * CSS class to apply to the detail panel
   */
  detailClassName?: string;
}

/**
 * A component that displays content in resizable panels
 */
export function ResizablePanels<T>({
  primaryContent,
  detailContent,
  detailContentRenderer,
  defaultPrimarySize = 50,
  defaultDetailSize = 50,
  minDetailSize = 12,
  className,
  primaryClassName,
  detailClassName,
}: ResizablePanelsProps<T>) {
  // This explicitly references T in the component body, preventing the TypeScript warning
  const context: TableContextType<T> = useTable<T>();
  const { detailRow, onDetailPanelClose } = context;

  const handleCollapsePanel = () => {
    onDetailPanelClose();
  };

  // Determine content to display in detail panel
  let renderDetailContent: ReactNode = null;

  if (detailContent) {
    renderDetailContent = detailContent;
  } else if (detailContentRenderer && detailRow) {
    renderDetailContent = detailContentRenderer(detailRow);
  }

  const showDetailPanel =
    !!detailRow && (!!renderDetailContent || !!detailContent);

  return (
    <ResizablePanelGroup
      direction="horizontal"
      className={cn("flex-1 rounded-lg w-full h-full flex gap-4", className)}
    >
      <ResizablePanel
        id="primary-panel"
        defaultSize={showDetailPanel ? defaultPrimarySize : 100}
        order={1}
        className={cn("flex flex-col gap-2 h-full", primaryClassName)}
      >
        {primaryContent}
      </ResizablePanel>

      {showDetailPanel && (
        <>
          <ResizableHandle withHandle />
          <ResizablePanel
            id="detail-panel"
            defaultSize={defaultDetailSize}
            order={2}
            className={cn("flex flex-col h-full", detailClassName)}
            collapsible={true}
            minSize={minDetailSize}
            onCollapse={handleCollapsePanel}
          >
            <Suspense
              fallback={<CardSkeleton items={5} className="flex flex-col" />}
            >
              {renderDetailContent}
            </Suspense>
          </ResizablePanel>
        </>
      )}
    </ResizablePanelGroup>
  );
}
