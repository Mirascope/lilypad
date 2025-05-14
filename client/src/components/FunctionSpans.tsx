import CardSkeleton from "@/components/CardSkeleton";
import LilypadDialog from "@/components/LilypadDialog";
import { LilypadLoading } from "@/components/LilypadLoading";
import { SearchBar } from "@/components/SearchBar";
import TableSkeleton from "@/components/TableSkeleton";
import { ResizablePanels } from "@/components/traces/ResizablePanels";
import { SpanFullDetail } from "@/components/traces/SpanFullDetail";
import { SpanMoreDetail } from "@/components/traces/SpanMoreDetail";
import { TracesTable } from "@/components/traces/TracesTable";
import { Typography } from "@/components/ui/typography";
import { QueueForm } from "@/ee/components/QueueForm";
import { useFeatureAccess } from "@/hooks/use-featureaccess";
import { usePaginatedSpansByFunction } from "@/hooks/use-paginated-query.tsx";
import { TableProvider, useTable } from "@/hooks/use-table";
import { Route } from "@/routes/_auth/projects/$projectUuid/functions/$functionName/_workbench/$functionUuid.$tab.$.tsx";
import { FunctionTab } from "@/types/functions";
import { SpanPublic } from "@/types/types";
import { formatRelativeTime } from "@/utils/strings";
import { useNavigate, useParams } from "@tanstack/react-router";
import { Users } from "lucide-react";
import { Suspense, useEffect, useState } from "react";
import { toast } from "sonner";
export const FunctionSpansContainer = ({
  functionUuid,
}: {
  functionUuid: string;
}) => {
  const navigate = useNavigate();
  const { functionName, projectUuid } = useParams({ from: Route.id });
  const handleDetailPanelOpen = (trace: SpanPublic) => {
    navigate({
      to: Route.fullPath,
      replace: true,
      params: {
        projectUuid,
        functionName,
        functionUuid,
        tab: FunctionTab.TRACES,
        _splat: trace.uuid,
      },
    }).catch(() => {
      toast.error("Failed to navigate");
    });
  };
  const handleDetailPanelClose = () => {
    navigate({
      to: Route.fullPath,
      replace: true,
      params: {
        projectUuid,
        functionName,
        functionUuid,
        tab: FunctionTab.TRACES,
      },
    }).catch(() => {
      toast.error("Failed to navigate");
    });
  };
  return (
    <TableProvider<SpanPublic>
      onPanelClose={handleDetailPanelClose}
      onPanelOpen={handleDetailPanelOpen}
    >
      <FunctionSpans functionUuid={functionUuid} />
    </TableProvider>
  );
};
export const FunctionSpans = ({ functionUuid }: { functionUuid: string }) => {
  const { projectUuid, _splat: traceUuid } = useParams({ from: Route.id });
  const [order, setOrder] = useState<"asc" | "desc">("desc");
  const [fullView, setFullView] = useState<boolean>(false);
  const { selectedRows, detailRow, setDetailRow } = useTable<SpanPublic>();
  const {
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    isLoading,
    defaultData,
    dataUpdatedAt,
  } = usePaginatedSpansByFunction(projectUuid, order, functionUuid);
  const features = useFeatureAccess();
  const [displayData, setDisplayData] = useState<SpanPublic[] | null>(null);

  useEffect(() => {
    if (traceUuid) {
      const trace = defaultData.find((row) => row.uuid === traceUuid);
      if (trace) {
        setDetailRow(trace);
      } else {
        setDetailRow(null);
      }
    } else {
      setDetailRow(null);
    }
  }, [defaultData]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <LilypadLoading />
      </div>
    );
  }

  const primaryContent = (
    <>
      <div className="flex justify-between items-center ">
        <Typography variant="span" affects="muted">
          Last updated: {formatRelativeTime(new Date(dataUpdatedAt))}
        </Typography>
        <div className="flex items-center gap-2">
          {features.annotations && (
            <LilypadDialog
              icon={<Users />}
              text={"Assign"}
              title={"Annotate selected traces"}
              description={`${selectedRows.length} trace(s) selected.`}
              buttonProps={{
                disabled: selectedRows.length === 0,
              }}
              tooltipContent={"Add selected traces to your annotation queue."}
            >
              <QueueForm spans={selectedRows} />
            </LilypadDialog>
          )}
        </div>
      </div>

      <div className="flex-1 overflow-auto">
        <div className="flex flex-col h-full">
          <div className="shrink-0 py-4">
            <SearchBar
              projectUuid={projectUuid}
              onDataChange={setDisplayData}
              filterFunction={(data) =>
                data.filter((item) => item.function_uuid === functionUuid)
              }
            />
          </div>
          <div className="flex-1 min-h-0 overflow-auto">
            {isLoading ? (
              <div className="flex items-center justify-center h-full">
                <LilypadLoading />
              </div>
            ) : (
              <TracesTable
                data={displayData ?? defaultData}
                traceUuid={traceUuid}
                projectUuid={projectUuid}
                fetchNextPage={() => {
                  if (hasNextPage && !isFetchingNextPage) {
                    void fetchNextPage();
                  }
                }}
                isFetchingNextPage={isFetchingNextPage}
                isSearch={Boolean(displayData)}
                order={order}
                onOrderChange={setOrder}
              />
            )}
          </div>
        </div>
      </div>
    </>
  );
  const detailContent = detailRow && (
    <Suspense fallback={<CardSkeleton items={5} className="flex flex-col" />}>
      <SpanMoreDetail
        data={detailRow}
        handleFullView={() => setFullView(true)}
      />
    </Suspense>
  );

  return (
    <div className="h-full flex flex-col gap-4">
      {fullView && traceUuid ? (
        <div className="container h-full w-full p-2 max-w-screen-2xl overflow-hidden">
          <SpanFullDetail
            projectUuid={projectUuid}
            spanUuid={traceUuid}
            handleBackToTraces={() => setFullView(false)}
          />
        </div>
      ) : (
        <Suspense fallback={<TableSkeleton />}>
          <ResizablePanels
            className="p-2"
            primaryContent={primaryContent}
            detailContent={detailContent}
            defaultPrimarySize={60}
            defaultDetailSize={40}
          />
        </Suspense>
      )}
    </div>
  );
};
