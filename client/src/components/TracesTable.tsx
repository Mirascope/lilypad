import { AnnotationForm } from "@/components/AnnotationForm";
import CardSkeleton from "@/components/CardSkeleton";
import { DataTable } from "@/components/DataTable";
import IconDialog from "@/components/IconDialog";
import { LilypadPanel } from "@/components/LilypadPanel";
import { LlmPanel } from "@/components/LlmPanel";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Scope, SpanPublic } from "@/types/types";
import { useNavigate } from "@tanstack/react-router";
import { ColumnDef, FilterFn } from "@tanstack/react-table";
import {
  ArrowDown,
  ArrowUp,
  ArrowUpDown,
  ChevronRight,
  MessageSquareText,
  MoreHorizontal,
  Users,
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

export const TracesTable = ({
  data,
  traceUuid,
  path,
}: {
  data: SpanPublic[];
  traceUuid?: string;
  path?: string;
}) => {
  const defaultRowSelection = findRowWithUuid(data, traceUuid);
  const isSubRow = defaultRowSelection?.parent_span_id;
  const navigate = useNavigate();
  const virtualizerRef = useRef<HTMLDivElement>(null);

  const columns: ColumnDef<SpanPublic>[] = [
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
      cell: ({ row }) => (
        <div className='lowercase'>{row.getValue("timestamp")}</div>
      ),
    },
    {
      id: "annotations",
      cell: ({ row }) => {
        return (
          <div onClick={(e) => e.stopPropagation()}>
            <IconDialog
              icon={<MessageSquareText />}
              title='Annotations'
              description='Annotations'
              buttonProps={{
                variant: "ghost",
              }}
            >
              <AnnotationForm />
            </IconDialog>
          </div>
        );
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
              <div onClick={(e) => e.stopPropagation()}>
                <Dialog>
                  <DialogTrigger asChild>
                    <DropdownMenuItem
                      className='flex items-center gap-2'
                      onSelect={(e) => e.preventDefault()}
                    >
                      <MessageSquareText className='w-4 h-4' />
                      <span className='font-medium'>Annotate</span>
                    </DropdownMenuItem>
                  </DialogTrigger>
                  <DialogContent className={"max-w-[425px] overflow-x-auto"}>
                    <DialogTitle>{`Annotate`}</DialogTitle>
                    <DialogDescription>
                      {`Annotate this trace to add to your dataset.`}
                    </DialogDescription>
                    <AnnotationForm />
                  </DialogContent>
                </Dialog>
              </div>
              <div onClick={(e) => e.stopPropagation()}>
                <Dialog>
                  <DialogTrigger asChild>
                    <DropdownMenuItem
                      className='flex items-center gap-2'
                      onSelect={(e) => e.preventDefault()}
                    >
                      <Users className='w-4 h-4' />
                      <span className='font-medium'>
                        Add to annotation queue
                      </span>
                    </DropdownMenuItem>
                  </DialogTrigger>
                  <DialogContent className={"max-w-[425px] overflow-x-auto"}>
                    <DialogTitle>{`Annotate`}</DialogTitle>
                    <DialogDescription>
                      {`Annotate this trace to add to your dataset.`}
                    </DialogDescription>
                    <AnnotationForm />
                  </DialogContent>
                </Dialog>
              </div>
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
      defaultRowSelection={defaultRowSelection}
      DetailPanel={DetailPanel}
      defaultPanelSize={50}
      filterColumn='display_name'
      getRowCanExpand={getRowCanExpand}
      getSubRows={getSubRows}
      defaultSorting={[{ id: "timestamp", desc: true }]}
    />
  );
};
