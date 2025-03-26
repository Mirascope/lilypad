import CardSkeleton from "@/components/CardSkeleton";
import { DataTable } from "@/components/DataTable";
import { LilypadPanel } from "@/components/LilypadPanel";
import { LlmPanel } from "@/components/LlmPanel";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
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
import { Suspense, useEffect, useRef, useState } from "react";

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
  hideCompare = false,
}: {
  data: SpanPublic[];
  traceUuid?: string;
  path?: string;
  hideCompare?: boolean;
}) => {
  const selectRow = findRowWithUuid(data, traceUuid);
  const isSubRow = selectRow?.parent_span_id;
  const navigate = useNavigate();
  const features = useFeatureAccess();
  const virtualizerRef = useRef<HTMLDivElement>(null);

  // State to track selected rows
  const [selectedRows, setSelectedRows] = useState<SpanPublic[]>([]);
  const [toggleCompareMode, setToggleCompareMode] = useState<boolean>(false);

  // Function to handle checkbox changes
  const handleCheckboxChange = (row: SpanPublic, checked: boolean) => {
    if (checked) {
      // If already have 2 selected rows and trying to add another, prevent it
      if (selectedRows.length >= 2) {
        return;
      }
      setSelectedRows([...selectedRows, row]);
    } else {
      setSelectedRows(
        selectedRows.filter((item) => item.span_id !== row.span_id)
      );
    }
  };

  const columns: ColumnDef<SpanPublic>[] = [
    {
      accessorKey: "display_name",
      enableHiding: false,
      filterFn: onlyParentFilter,
      header: "Name",
      cell: ({ row }) => {
        const depth = row.depth;
        const hasSubRows = row.subRows.length > 0;
        const isSelected = selectedRows.some(
          (item) => item.span_id === row.original.span_id
        );

        return (
          <div style={{ marginLeft: `${depth * 1.5}rem` }}>
            <div className='flex items-center gap-2'>
              {hasSubRows ? <ExpandRowButton row={row} /> : <Spacer />}
              {!hideCompare && (
                <Checkbox
                  onClick={(e) => e.stopPropagation()}
                  checked={isSelected}
                  onCheckedChange={(checked) => {
                    handleCheckboxChange(row.original, checked === true);
                  }}
                  aria-label={`Select ${row.getValue("display_name")}`}
                  className='mr-2'
                />
              )}
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
                row.original.function?.is_versioned &&
                features.playground && (
                  <DropdownMenuItem
                    onClick={() => {
                      const { project_uuid, function: fn } = row.original;
                      if (!fn) return;
                      navigate({
                        to: `/projects/${project_uuid}/functions/${fn.name}/${fn.uuid}/overview`,
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
  const CompareDetailPanel = () => {
    return (
      <div className='p-4 border rounded-md overflow-auto'>
        {selectedRows.length === 2 && (
          <Button
            variant='outline'
            size='sm'
            onClick={() =>
              setToggleCompareMode(
                (prevToggleCompareMode) => !prevToggleCompareMode
              )
            }
          >
            Go back
          </Button>
        )}
        <h2 className='text-lg font-semibold mb-2'>Compare Details</h2>
        <div className='flex gap-4'>
          <div className='w-1/2'>
            <h3 className='text-lg font-semibold'>Row 1</h3>
            <Suspense
              fallback={<CardSkeleton items={5} className='flex flex-col' />}
            >
              {selectedRows[0].scope === Scope.LILYPAD ? (
                <LilypadPanel spanUuid={selectedRows[0].uuid} />
              ) : (
                <LlmPanel spanUuid={selectedRows[0].uuid} />
              )}
            </Suspense>
          </div>
          <div className='w-1/2'>
            <h3 className='text-lg font-semibold'>Row 2</h3>
            <Suspense
              fallback={<CardSkeleton items={5} className='flex flex-col' />}
            >
              {selectedRows[1].scope === Scope.LILYPAD ? (
                <LilypadPanel spanUuid={selectedRows[1].uuid} />
              ) : (
                <LlmPanel spanUuid={selectedRows[1].uuid} />
              )}
            </Suspense>
          </div>
        </div>
      </div>
    );
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
  const customControls = () => {
    return (
      <>
        <Button
          variant='outline'
          size='sm'
          onClick={() =>
            setToggleCompareMode(
              (prevToggleCompareMode) => !prevToggleCompareMode
            )
          }
          className='whitespace-nowrap'
          disabled={selectedRows.length === 0}
        >
          Compare
        </Button>
        <Button
          variant='outline'
          size='sm'
          onClick={() => setSelectedRows([])}
          className='whitespace-nowrap'
          disabled={selectedRows.length === 0}
        >
          Clear Selection ({selectedRows.length}/2)
        </Button>
      </>
    );
  };
  if (toggleCompareMode) {
    return <CompareDetailPanel />;
  }
  return (
    <div>
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
        filterColumn={!hideCompare ? undefined : "display_name"}
        selectRow={selectRow}
        getRowCanExpand={getRowCanExpand}
        getSubRows={getSubRows}
        customControls={!hideCompare ? customControls : undefined}
        defaultSorting={[{ id: "timestamp", desc: true }]}
        onDetailPanelClose={handleDetailPanelClose}
      />
    </div>
  );
};
