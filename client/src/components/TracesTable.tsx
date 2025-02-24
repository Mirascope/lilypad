import CardSkeleton from "@/components/CardSkeleton";
import { DataTable } from "@/components/DataTable";
import LilypadDialog from "@/components/LilypadDialog";
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
import { CreateAnnotationDialog } from "@/ee/components/AnnotationForm";
import { QueueDialog, QueueForm } from "@/ee/components/QueueForm";
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
  Users,
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
  const virtualizerRef = useRef<HTMLDivElement>(null);
  const [open, setOpen] = useState(false);
  const columns: ColumnDef<SpanPublic>[] = [
    {
      id: "select",
      header: ({ table }) => {
        const topLevelRows = table
          .getFilteredRowModel()
          .rows.filter((row) => row.getValue("scope") === Scope.LILYPAD);
        const allTopLevelSelected = topLevelRows.every((row) =>
          row.getIsSelected()
        );
        const someTopLevelSelected = topLevelRows.some((row) =>
          row.getIsSelected()
        );

        return (
          <Checkbox
            checked={
              (topLevelRows.length > 0 && allTopLevelSelected) ||
              (someTopLevelSelected && "indeterminate")
            }
            onCheckedChange={(value) => {
              topLevelRows.forEach((row) => row.toggleSelected(!!value));
            }}
            aria-label='Select all top level rows'
          />
        );
      },
      cell: ({ row }) => {
        const shouldShowCheckbox = row.getValue("scope") == Scope.LILYPAD;

        if (!shouldShowCheckbox) return null;
        return (
          <div onClick={(e) => e.stopPropagation()}>
            <Checkbox
              checked={row.getIsSelected()}
              onCheckedChange={(value) => row.toggleSelected(!!value)}
              aria-label='Select row'
            />
          </div>
        );
      },
      enableSorting: false,
      enableHiding: false,
    },
    {
      accessorKey: "display_name",
      header: "Name",
      enableHiding: false,
      filterFn: onlyParentFilter,
      cell: ({ row }) => {
        const depth = row.depth;
        const hasSubRows = row.subRows.length > 0;
        return (
          <div
            className='flex items-center gap-2'
            style={{ marginLeft: `${depth * 1}rem` }}
          >
            <div className='flex items-center gap-2'>
              {hasSubRows && (
                <ChevronRight
                  onClick={(event) => {
                    row.toggleExpanded();
                    event.stopPropagation();
                  }}
                  className={`h-4 w-4 transition-transform ${
                    row.getIsExpanded() ? "rotate-90" : ""
                  }`}
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
        return <div>{formatDate(row.getValue("timestamp"))}</div>;
      },
    },
    {
      id: "actions",
      enableHiding: false,
      cell: ({ row }) => {
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
              {row.getValue("scope") === Scope.LILYPAD && (
                <>
                  <div onClick={(e) => e.stopPropagation()}>
                    <Suspense fallback={<div>Loading ...</div>}>
                      <CreateAnnotationDialog spanUuid={row.original.uuid} />
                    </Suspense>
                  </div>
                  <div onClick={(e) => e.stopPropagation()}>
                    <QueueDialog spans={[row.original]} />
                  </div>
                </>
              )}
              {/* {row.original.scope === Scope.LILYPAD && (
                <DropdownMenuItem
                  onClick={() => {
                    const { project_uuid, version_uuid, version } =
                      row.original;
                    const name = version?.function_name;
                    if (!name) return;
                    navigate({
                      to: `/projects/${project_uuid}/functions/${name}/versions/${version_uuid}`,
                    });
                  }}
                >
                  Open Playground
                </DropdownMenuItem>
              )} */}
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

  const DetailPanel = ({ data }: { data: SpanPublic }) => {
    useEffect(() => {
      navigate({
        to: path,
        replace: true,
        params: { _splat: data.uuid },
      });
      return () => {
        navigate({
          to: path,
          replace: true,
          params: { _splat: undefined },
        });
      };
    }, [data]);
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
  const renderCustomControls = (rows: Row<SpanPublic>[]) => {
    const spans = rows.map((row) => row.original);
    return (
      <LilypadDialog
        open={open}
        onOpenChange={setOpen}
        icon={<Users />}
        title={"Annotate selected traces"}
        description={`${rows.length} trace(s) selected.`}
        buttonProps={{
          disabled: rows.every((row) => !row.getIsSelected()),
        }}
        tooltipContent={"Add selected traces to your annotation queue."}
      >
        <QueueForm spans={spans} setOpen={setOpen} />
      </LilypadDialog>
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
      customControls={renderCustomControls}
    />
  );
};
