import { useQuery, useSuspenseQuery } from "@tanstack/react-query";
import { z } from "zod";

import CardSkeleton from "@/src/components/CardSkeleton";
import { ComparePanel } from "@/src/components/ComparePanel";
import LilypadDialog from "@/src/components/LilypadDialog";
import { LilypadLoading } from "@/src/components/LilypadLoading";
import { SearchBar } from "@/src/components/SearchBar";
import TableSkeleton from "@/src/components/TableSkeleton";
import { ResizablePanels } from "@/src/components/traces/ResizablePanels";
import { SpanMoreDetail } from "@/src/components/traces/SpanMoreDetail";
import { TracesTable } from "@/src/components/traces/TracesTable";
import { Button } from "@/src/components/ui/button";
import { Typography } from "@/src/components/ui/typography";
import { QueueForm } from "@/src/ee/components/QueueForm";
import { useFeatureAccess } from "@/src/hooks/use-featureaccess";
import { useInfiniteTraces } from "@/src/hooks/use-infinite-traces";
import { TableProvider, useTable } from "@/src/hooks/use-table";
import { SpanMoreDetails, SpanPublic } from "@/src/types/types";
import { projectQueryOptions } from "@/src/utils/projects";
import { formatRelativeTime } from "@/src/utils/strings";
import { spansByTraceIdQueryOptions } from "@/src/utils/traces";
import { createFileRoute, useNavigate, useParams } from "@tanstack/react-router";
import { GitCompare, RefreshCcw, Users, Pause, Play } from "lucide-react";
import { Suspense, useEffect, useState } from "react";
import { toast } from "sonner";

const INIT_LIMIT = 80;

export const Route = createFileRoute("/_auth/projects/$projectUuid/traces/$")({
  validateSearch: z.object({}).optional(),
  component: () => <TraceContainer />,
});

const TraceContainer = () => {
  const navigate = useNavigate();
  const { projectUuid } = useParams({ from: Route.id });
  const handleDetailPanelOpen = (trace: SpanPublic) => {
    navigate({
      to: Route.fullPath,
      replace: true,
      params: { projectUuid, _splat: trace.uuid },
    }).catch(() => {
      toast.error("Failed to navigate");
    });
  };
  const handleDetailPanelClose = () => {
    navigate({
      to: Route.fullPath,
      replace: true,
      params: { projectUuid, _splat: undefined },
    }).catch(() => {
      toast.error("Failed to navigate");
    });
  };
  return (
    <Suspense fallback={<LilypadLoading />}>
      <TableProvider<SpanPublic>
        onPanelClose={handleDetailPanelClose}
        onPanelOpen={handleDetailPanelOpen}
      >
        <Trace />
      </TableProvider>
    </Suspense>
  );
};

const Trace = () => {
  const { projectUuid, _splat: urlParam } = useParams({ from: Route.id });
  const { data: project } = useSuspenseQuery(projectQueryOptions(projectUuid));
  const { selectedRows, detailRow, setDetailRow, setSelectedRows } = useTable<SpanPublic>();
  const [isComparing, setIsComparing] = useState(false);
  const features = useFeatureAccess();
  const [pageSize] = useState(INIT_LIMIT);
  const [searchData, setSearchData] = useState<SpanPublic[] | null>(null);
  const [order, setOrder] = useState<"asc" | "desc">("desc");
  const [isPolling, setIsPolling] = useState(false);
  const navigate = useNavigate();
  const {
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    defaultData,
    isLoading,
    dataUpdatedAt,
    refetch,
  } = useInfiniteTraces(projectUuid, pageSize, order, isPolling);

  // Check if urlParam looks like a trace ID (not a UUID)
  const isTraceId = urlParam && !urlParam.includes('-');
  
  // Query to get spans by trace ID if needed
  const { data: spansByTraceId } = useQuery({
    ...spansByTraceIdQueryOptions(projectUuid, urlParam || ''),
    enabled: !!isTraceId && !!urlParam,
  });

  useEffect(() => {
    if (urlParam) {
      if (isTraceId && spansByTraceId && spansByTraceId.length > 0) {
        // Find the root span (parent_span_id is null)
        const rootSpan = spansByTraceId.find(span => !span.parent_span_id) || spansByTraceId[0];
        // Navigate to the span's UUID
        navigate({
          to: Route.fullPath,
          replace: true,
          params: { projectUuid, _splat: rootSpan.uuid },
        }).catch(() => {
          toast.error("Failed to navigate to trace");
        });
      } else if (!isTraceId && defaultData.length > 0) {
        // It's a UUID, handle normally
        // Helper function to find a span in nested structure
        const findSpanInData = (data: SpanPublic[], uuid: string): SpanPublic | undefined => {
          for (const span of data) {
            if (span.uuid === uuid) {
              return span;
            }
            if (span.child_spans && span.child_spans.length > 0) {
              const found = findSpanInData(span.child_spans, uuid);
              if (found) return found;
            }
          }
          return undefined;
        };
        
        const trace = findSpanInData(defaultData, urlParam);
        if (trace) {
          setDetailRow(trace);
          // If it's a child span, we might need to wait for the parent to expand
          if (trace.parent_span_id) {
            // Force a re-render after parent expansion
            setTimeout(() => {
              setDetailRow(trace);
            }, 300);
          }
        } else {
          // If not found in current data, it might be on a different page
          // We could fetch more data here if needed
          setDetailRow(null);
        }
      }
    } else {
      setDetailRow(null);
    }
  }, [urlParam, defaultData, spansByTraceId, isTraceId, navigate, projectUuid, setDetailRow]);

  // Toggle polling
  const togglePolling = () => {
    if (isPolling) {
      setIsPolling(false);
      toast.success("Real-time updates paused");
    } else {
      // Clear selections when starting auto-updates to ensure smooth scrolling
      if (selectedRows.length > 0) {
        toast.info("Clearing selections for optimal real-time updates", {
          description: "This prevents conflicts with auto-scrolling"
        });
        setSelectedRows([]);
      }
      setIsPolling(true);
      toast.success("Real-time updates started");
    }
  };

  const handleReachEnd = async () => {
    if (!hasNextPage || isFetchingNextPage) return;
    await fetchNextPage();
  };

  const handleFullView = (span: SpanMoreDetails) => {
    if (!span.project_uuid) {
      toast.error("This span is not part of a project");
      return;
    }
    navigate({
      to: "/projects/$projectUuid/traces/detail/$spanUuid",
      params: {
        projectUuid: span.project_uuid,
        spanUuid: span.uuid,
      },
    }).catch(() => toast.error("Failed to navigate"));
  };
  if (isComparing) {
    return (
      <div className="flex h-screen flex-col gap-4 p-4">
        <Button
          variant="outline"
          size="sm"
          onClick={() => setIsComparing(false)}
          className="mb-4 w-fit shrink-0"
        >
          ← Back to Traces
        </Button>
        <ComparePanel rows={selectedRows} />
      </div>
    );
  }

  const primaryContent = (
    <>
      <div className="flex flex-col gap-1">
        <div className="flex items-center justify-between">
          <Typography variant="h3">{project.name}</Typography>
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
            <Button
              variant="secondary"
              size="sm"
              onClick={() => setIsComparing(true)}
              disabled={selectedRows.length !== 2}
              className="whitespace-nowrap"
            >
              <GitCompare />
              Compare
            </Button>
          </div>
        </div>
        <Typography variant="span" affects="muted" className="flex items-center gap-2">
          Last updated: {formatRelativeTime(new Date(dataUpdatedAt))}
          <Button
            variant="outline"
            size="icon"
            loading={isLoading}
            onClick={() => {
              refetch();
              toast.success("Refreshed traces");
            }}
            className="group relative size-8 overflow-hidden transition-all hover:bg-gray-100"
          >
            <RefreshCcw className="h-4 w-4" />
          </Button>
          <Button
            variant={isPolling ? "secondary" : "outline"}
            size="icon"
            onClick={togglePolling}
            className="group relative size-8 overflow-hidden transition-all"
            title={isPolling ? "Pause real-time updates" : "Start real-time updates"}
          >
            {isPolling ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
          </Button>
          {isPolling && !isLoading && (
            <span className="text-xs text-muted-foreground animate-pulse">
              Live updating...
            </span>
          )}
        </Typography>
      </div>
      <div className="flex-1 overflow-auto">
        <div className="flex h-full flex-col">
          <div className="shrink-0 py-4">
            <SearchBar projectUuid={projectUuid} onDataChange={setSearchData} />
          </div>
          {isLoading ? (
            <div className="flex h-full items-center justify-center">
              <LilypadLoading />
            </div>
          ) : (
            <TracesTable
              className="min-h-0 flex-1 overflow-hidden"
              data={searchData ?? defaultData}
              traceUuid={urlParam}
              isSearch={Boolean(searchData)}
              fetchNextPage={handleReachEnd}
              isFetchingNextPage={isFetchingNextPage}
              projectUuid={projectUuid}
              order={order}
              onOrderChange={setOrder}
            />
          )}
        </div>
      </div>
    </>
  );
  const detailContent = detailRow && (
    <Suspense fallback={<CardSkeleton items={5} className="flex flex-col" />}>
      <SpanMoreDetail data={detailRow} handleFullView={handleFullView} />
    </Suspense>
  );

  return (
    <div className="flex h-screen flex-col gap-4 p-4">
      <Suspense fallback={<TableSkeleton />}>
        <ResizablePanels
          primaryContent={primaryContent}
          detailContent={detailContent}
          defaultPrimarySize={60}
          defaultDetailSize={40}
        />
      </Suspense>
    </div>
  );
};
