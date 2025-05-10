import { useSuspenseQuery } from "@tanstack/react-query";
import { z } from "zod";

import CardSkeleton from "@/components/CardSkeleton";
import { ComparePanel } from "@/components/ComparePanel";
import LilypadDialog from "@/components/LilypadDialog";
import { LilypadLoading } from "@/components/LilypadLoading";
import { SearchBar } from "@/components/SearchBar";
import TableSkeleton from "@/components/TableSkeleton";
import { ResizablePanels } from "@/components/traces/ResizablePanels";
import { SpanMoreDetail } from "@/components/traces/SpanMoreDetail";
import { TracesTable } from "@/components/traces/TracesTable";
import { Button } from "@/components/ui/button";
import { Typography } from "@/components/ui/typography";
import { QueueForm } from "@/ee/components/QueueForm";
import { useFeatureAccess } from "@/hooks/use-featureaccess";
import { useInfiniteTraces } from "@/hooks/use-infinite-traces";
import { TableProvider, useTable } from "@/hooks/use-table";
import { SpanMoreDetails, SpanPublic } from "@/types/types";
import { projectQueryOptions } from "@/utils/projects";
import { formatRelativeTime } from "@/utils/strings";
import {
  createFileRoute,
  useNavigate,
  useParams,
} from "@tanstack/react-router";
import { Users } from "lucide-react";
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
  const { projectUuid, _splat: traceUuid } = useParams({ from: Route.id });
  const { data: project } = useSuspenseQuery(projectQueryOptions(projectUuid));
  const { selectedRows, detailRow, setDetailRow } = useTable<SpanPublic>();
  const [isComparing, setIsComparing] = useState(false);
  const features = useFeatureAccess();
  const [pageSize] = useState(INIT_LIMIT);
  const [searchData, setSearchData] = useState<SpanPublic[] | null>(null);
  const [order, setOrder] = useState<"asc" | "desc">("desc");
  const navigate = useNavigate();
  const {
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    defaultData,
    isLoading,
    dataUpdatedAt,
  } = useInfiniteTraces(projectUuid, pageSize, order);

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
      <div className="h-screen flex flex-col gap-4 p-4">
        <Button
          variant="outline"
          size="sm"
          onClick={() => setIsComparing(false)}
          className="mb-4 w-fit"
        >
          ← Back to Traces
        </Button>
        <ComparePanel
          rows={selectedRows}
          onClose={() => setIsComparing(false)}
        />
      </div>
    );
  }

  const primaryContent = (
    <>
      <div className="flex flex-col gap-1">
        <div className="flex justify-between items-center">
          <Typography variant="h3">{project.name}</Typography>
          <div className="flex items-center gap-2">
            {features.annotations && (
              <LilypadDialog
                icon={<Users />}
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
              Compare
            </Button>
          </div>
        </div>
        <Typography variant="span" affects="muted">
          Last updated: {formatRelativeTime(new Date(dataUpdatedAt))}
        </Typography>
      </div>

      <div className="flex-1 overflow-auto">
        <div className="flex flex-col h-full">
          <div className="shrink-0 py-4">
            <SearchBar projectUuid={projectUuid} onDataChange={setSearchData} />
          </div>
          <div className="flex-1 min-h-0 overflow-auto">
            {isLoading ? (
              <div className="flex items-center justify-center h-full">
                <LilypadLoading />
              </div>
            ) : (
              <TracesTable
                data={searchData ?? defaultData}
                traceUuid={traceUuid}
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
      </div>
    </>
  );
  const detailContent = detailRow && (
    <Suspense fallback={<CardSkeleton items={5} className="flex flex-col" />}>
      <SpanMoreDetail data={detailRow} handleFullView={handleFullView} />
    </Suspense>
  );

  return (
    <div className="h-screen flex flex-col gap-4 p-4">
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
