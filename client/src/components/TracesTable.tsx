import CardSkeleton from "@/components/CardSkeleton";
import { DataTable } from "@/components/DataTable";
import { LilypadPanel } from "@/components/LilypadPanel";
import { LlmPanel } from "@/components/LlmPanel";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { AnnotationDialog } from "@/ee/components/AnnotationForm";
import { useFeatureAccess } from "@/hooks/use-featureaccess";
import { Scope, SpanPublic } from "@/types/types";
import { formatDate } from "@/utils/strings";
import { useNavigate } from "@tanstack/react-router";
import { ColumnDef, FilterFn, Row } from "@tanstack/react-table";
import {
  ArrowDown,
  ArrowUp,
  ArrowUpDown,
  ChevronRight,
  MoreHorizontal,
} from "lucide-react";
import { Suspense, useEffect, useRef } from "react";

// Custom filter function
const onlyParentFilter: FilterFn<SpanPublic> = (row, columnId, filterValue) => {
  const isParent =
    row.original.child_spans && row.original.child_spans.length > 0;

  if (isParent) {
    const cellValue = row.getValue(columnId);
    return String(cellValue)
      .toLowerCase()
      .includes(String(filterValue).toLowerCase());
  }

  // Always include child rows
  return true;
};
const findRowWithUuid = (
  rows: SpanPublic[],
  targetUuid: string | undefined
): SpanPublic | undefined => {
  if (!targetUuid) return undefined;
  for (const row of rows) {
    if (row.uuid === targetUuid) {
      return row;
    }

    if (row.child_spans?.length) {
      const found = findRowWithUuid(row.child_spans, targetUuid);
      if (found) return found;
    }
  }
  return undefined;
};

const Spacer = () => <div className='w-4 h-4' />;
const ExpandRowButton = ({ row }: { row: Row<SpanPublic> }) => {
  return (
    <ChevronRight
      onClick={(event) => {
        row.toggleExpanded();
        event.stopPropagation();
      }}
      className={`h-4 w-4 transition-transform ${
        row.getIsExpanded() ? "rotate-90" : ""
      }`}
    />
  );
};

export const TracesTable = ({
  data,
  traceUuid,
  path,
}: {
  data: SpanPublic[];
  traceUuid?: string;
  path?: string;
}) => {
  const selectRow = findRowWithUuid(data, traceUuid);
  const isSubRow = selectRow?.parent_span_id;
  const navigate = useNavigate();
  const features = useFeatureAccess();
  const virtualizerRef = useRef<HTMLDivElement>(null);
  const columns: ColumnDef<SpanPublic>[] = [
    {
      accessorKey: "display_name",
      enableHiding: false,
      filterFn: onlyParentFilter,
      header: "Name",
      cell: ({ row }) => {
        const depth = row.depth;
        const hasSubRows = row.subRows.length > 0;

        return (
          <div style={{ marginLeft: `${depth * 1.5}rem` }}>
            <div className='flex items-center gap-2'>
              {hasSubRows ? <ExpandRowButton row={row} /> : <Spacer />}
              <span className='truncate'>{row.getValue("display_name")}</span>
            </div>
          </div>
        );
      },
    },
    {
      accessorKey: "scope",
      header: "Scope",
    },
    {
      accessorKey: "version",
      id: "version",
      header: ({ column }) => {
        return (
          <Button
            className='p-0'
            variant='ghost'
            onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
          >
            Version
            {column.getIsSorted() ? (
              column.getIsSorted() === "asc" ? (
                <ArrowUp className='ml-2 h-4 w-4' />
              ) : (
                <ArrowDown className='ml-2 h-4 w-4' />
              )
            ) : (
              <ArrowUpDown className='ml-2 h-4 w-4' />
            )}
          </Button>
        );
      },
    },
    {
      accessorKey: "status",
      id: "status",
      header: "Status",
      cell: ({ row }) => {
        const status: string = row.getValue("status");
        if (status === "UNSET") return null;
        else if (status === "ERROR") {
          return (
            <Badge variant='destructive' size='sm'>
              {status}
            </Badge>
          );
        } else
          return (
            <Badge variant='destructive' size='sm'>
              {status}
            </Badge>
          );
      },
    },
    {
      accessorKey: "created_at",
      id: "timestamp",
      header: ({ column }) => {
        return (
          <Button
            className='p-0'
            variant='ghost'
            onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
          >
            Timestamp
            {column.getIsSorted() ? (
              column.getIsSorted() === "asc" ? (
                <ArrowUp className='ml-2 h-4 w-4' />
              ) : (
                <ArrowDown className='ml-2 h-4 w-4' />
              )
            ) : (
              <ArrowUpDown className='ml-2 h-4 w-4' />
            )}
          </Button>
        );
      },
      cell: ({ row }) => {
        return (
          <span className='truncate'>
            {formatDate(row.getValue("timestamp"))}
          </span>
        );
      },
    },
    {
      id: "actions",
      enableHiding: false,
      cell: ({ row }) => {
        const annotation = row.original.annotations[0];
        return (
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant='ghost' className='h-8 w-8 p-0'>
                <span className='sr-only'>Open menu</span>
                <MoreHorizontal className='h-4 w-4' />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align='end'>
              <DropdownMenuLabel>Actions</DropdownMenuLabel>
              {features.annotations &&
                row.getValue("scope") === Scope.LILYPAD && (
                  <div onClick={(e) => e.stopPropagation()}>
                    <Suspense fallback={<div>Loading ...</div>}>
                      <AnnotationDialog
                        spanUuid={row.original.uuid}
                        annotation={annotation}
                      />
                    </Suspense>
                  </div>
                )}
              {row.original.scope === Scope.LILYPAD &&
                row.original.generation &&
                row.original.generation.is_managed &&
                features.managedGenerations && (
                  <DropdownMenuItem
                    onClick={() => {
                      const { project_uuid, generation } = row.original;
                      if (!generation) return;
                      navigate({
                        to: `/projects/${project_uuid}/generations/${generation.name}/${generation.uuid}/overview`,
                      });
                    }}
                  >
                    Open Playground
                  </DropdownMenuItem>
                )}
              <DropdownMenuSeparator />
              <DropdownMenuItem>View more details</DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        );
      },
    },
  ];
  const getRowCanExpand = (row: SpanPublic) => row.child_spans.length > 0;
  const getSubRows = (row: SpanPublic) => row.child_spans || [];
  const handleDetailPanelClose = () => {
    if (path) {
      navigate({ to: path, replace: true, params: { _splat: undefined } });
    }
  };
  const DetailPanel = ({ data }: { data: SpanPublic }) => {
    useEffect(() => {
      if (path) {
        navigate({
          to: path,
          replace: true,
          params: { _splat: data.uuid },
        });
      }
    }, [data, path, navigate]);

    return (
      <div className='p-4 border rounded-md overflow-auto'>
        <h2 className='text-lg font-semibold mb-2'>Row Details</h2>
        <Suspense
          fallback={<CardSkeleton items={5} className='flex flex-col' />}
        >
          {data.scope === Scope.LILYPAD ? (
            <LilypadPanel spanUuid={data.uuid} />
          ) : (
            <LlmPanel spanUuid={data.uuid} />
          )}
        </Suspense>
      </div>
    );
  };
  return (
    <DataTable<SpanPublic>
      columns={columns}
      data={data}
      virtualizerRef={virtualizerRef}
      virtualizerOptions={{
        count: data.length,
        estimateSize: () => 45,
        overscan: 20,
      }}
      customExpanded={isSubRow ? { [isSubRow]: true } : undefined}
      customGetRowId={(row) => row.span_id}
      DetailPanel={DetailPanel}
      defaultPanelSize={50}
      filterColumn='display_name'
      selectRow={selectRow}
      getRowCanExpand={getRowCanExpand}
      getSubRows={getSubRows}
      defaultSorting={[{ id: "timestamp", desc: true }]}
      onDetailPanelClose={handleDetailPanelClose}
    />
  );
};
