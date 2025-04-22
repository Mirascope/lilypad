import CardSkeleton from "@/components/CardSkeleton";
import { AddComment, CommentCards } from "@/components/Comment";
import { DataTable } from "@/components/DataTable";
import LilypadDialog from "@/components/LilypadDialog";
import { LilypadPanel } from "@/components/LilypadPanel";
import { LlmPanel } from "@/components/LlmPanel";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { DataTableHandle } from "@/components/DataTable";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { EmojiPicker, EmojiPickerContent } from "@/components/ui/emoji-picker";
import { Input } from "@/components/ui/input";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { Separator } from "@/components/ui/separator";
import { Typography } from "@/components/ui/typography";
import { AnnotationsTable } from "@/ee/components/AnnotationsTable";
import { QueueForm } from "@/ee/components/QueueForm";
import { useFeatureAccess } from "@/hooks/use-featureaccess";
import { AnnotationPublic, Scope, SpanPublic, TagPublic } from "@/types/types";
import {
  commentsBySpanQueryOptions,
  fetchCommentsBySpan,
} from "@/utils/comments";
import { fetchSpan } from "@/utils/spans";
import { formatDate } from "@/utils/strings";
import { useQueryClient, useSuspenseQuery } from "@tanstack/react-query";
import { useNavigate } from "@tanstack/react-router";
import { ColumnDef, FilterFn, Row, Table } from "@tanstack/react-table";
import {
  ArrowDown,
  ArrowUp,
  ArrowUpDown,
  ChevronRight,
  Loader2,
  MessageSquareMore,
  MoreHorizontal,
  NotebookPen,
  SmileIcon,
  Users,
} from "lucide-react";
import { Suspense, useCallback, useEffect, useLayoutEffect, useRef, useState } from "react";
import { toast } from "sonner";

const ROW_HEIGHT = 45;
const MIN_PAGE = 20;

function calcPageSize(viewportEl: HTMLDivElement | null) {
  const vh = viewportEl?.clientHeight ?? window.innerHeight;
  return Math.max(MIN_PAGE, Math.ceil((vh / ROW_HEIGHT) * 2));
}

const tagFilter = (
  row: Row<SpanPublic>,
  columnId: string,
  filterValue: string
): boolean => {
  const tags: TagPublic[] = row.getValue(columnId);
  
  // If there's no filter value, return true (show all rows)
  if (!filterValue || filterValue.trim() === "") {
    return true;
  }
  
  // If there are no tags or tags is not an array, return false
  if (!Array.isArray(tags) || tags.length === 0) {
    return false;
  }
  
  // Convert filter value to lowercase for case-insensitive comparison
  const filterLower = filterValue.toLowerCase();
  
  // Check if any tag name includes the filter value
  return tags.some((tag) => tag.name.toLowerCase().includes(filterLower));
};

// Custom filter function
const onlyParentFilter: FilterFn<SpanPublic> = (row, columnId, value) => {
  const query = String(value).trim().toLowerCase();
  if (!query) return true;
  
  if (row.depth > 0) return true;
  
  const hit = (span: SpanPublic): boolean =>
    span.display_name.toLowerCase().includes(query) ||
    (span.child_spans ?? []).some(hit);
  
  return hit(row.original);
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

const Spacer = () => <div className='w-4 h-4'/>;
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

const DetailPanel = ({ data, path }: { data: SpanPublic; path?: string }) => {
  const navigate = useNavigate();
  const [showComments, setShowComments] = useState(false);
  const [showAnnotations, setShowAnnotations] = useState<boolean>(false);
  const { data: spanComments } = useSuspenseQuery(
    commentsBySpanQueryOptions(data.uuid)
  );
  useEffect(() => {
    if (path) {
      navigate({
        to: path,
        replace: true,
        params: { _splat: data.uuid },
      }).catch(() => {
        toast.error("Failed to navigate");
      });
    }
  }, [data, path]);
  
  const filteredAnnotations = data.annotations.filter(
    (annotation) => annotation.label
  );
  return (
    <div className='flex flex-col h-full max-h-screen overflow-hidden'>
      {/* Controls remain at top */}
      <div className='flex justify-end gap-2 p-2 flex-shrink-0'>
        <Button
          size='icon'
          className='h-8 w-8 relative'
          variant='outline'
          onClick={() => setShowComments(!showComments)}
        >
          <MessageSquareMore/>
          {spanComments.length > 0 && (
            <div
              className='absolute -top-2 -right-2 bg-primary text-primary-foreground text-xs rounded-full h-5 w-5 flex items-center justify-center font-medium'>
              {spanComments.length > 9 ? "9+" : spanComments.length}
            </div>
          )}
        </Button>
        <Button
          size='icon'
          className='h-8 w-8 relative'
          variant='outline'
          onClick={() => setShowAnnotations(!showAnnotations)}
        >
          <NotebookPen/>
          {filteredAnnotations.length > 0 && (
            <div
              className='absolute -top-2 -right-2 bg-primary text-primary-foreground text-xs rounded-full h-5 w-5 flex items-center justify-center font-medium'>
              {filteredAnnotations.length > 9
                ? "9+"
                : filteredAnnotations.length}
            </div>
          )}
        </Button>
      </div>
      
      {/* Scrollable content area */}
      <div className='flex-1 overflow-auto pb-4'>
        {/* Comments section with max height and scrolling */}
        {showComments && (
          <div className='mb-4'>
            <div className='max-h-64 overflow-y-auto mb-4'>
              <CommentCards spanUuid={data.uuid}/>
            </div>
            <Separator/>
            <div className='mt-4'>
              <AddComment spanUuid={data.uuid}/>
            </div>
          </div>
        )}
        
        {/* Annotations section with max height and scrolling */}
        {showAnnotations && (
          <div className='mb-4 max-h-64 overflow-y-auto'>
            <AnnotationsTable data={filteredAnnotations}/>
          </div>
        )}
        
        {/* Row details panel */}
        <div className='p-4 border overflow-auto rounded-md mt-4'>
          <h2 className='text-lg font-semibold mb-2'>Row Details</h2>
          {data.scope === Scope.LILYPAD ? (
            <LilypadPanel spanUuid={data.uuid}/>
          ) : (
            <LlmPanel spanUuid={data.uuid}/>
          )}
        </div>
      </div>
    </div>
  );
};

interface TracesTableProps {
  data: SpanPublic[];
  traceUuid?: string;
  path?: string;
  hideCompare?: boolean;
  
  /** infinite‑scroll sentinel callback */
  onReachEnd?: () => void;
  /** explicit refresh (Load newer) */
  onLoadNewer?: () => Promise<void> | void;
  /** true while onLoadNewer runs */
  isLoadingNewer?: boolean;
  /** true while useInfiniteQuery is fetching next page */
  isFetchingNextPage?: boolean;
}


export const TracesTable = ({
  data,
  traceUuid,
  path,
  hideCompare = false,
  onReachEnd,
  onLoadNewer,
  isLoadingNewer = false,
  isFetchingNextPage = false,
}: TracesTableProps) => {
  const navigate = useNavigate();
  const features = useFeatureAccess();
  const queryClient = useQueryClient();
  const virtualizerRef = useRef<HTMLDivElement>(null);
  const tableRef = useRef<DataTableHandle>(null);
  
  const [nameFilter, setName] = useState("");
  
  useEffect(() => {
    tableRef.current?.scrollTop();
  }, [nameFilter]);
  
  // State to track selected rows
  const [selectedRows, setSelectedRows] = useState<SpanPublic[]>([]);
  const [toggleCompareMode, setToggleCompareMode] = useState<boolean>(false);
  
  // Function to handle checkbox changes
  const handleCheckboxChange = (row: SpanPublic, checked: boolean) => {
    if (checked) {
      setSelectedRows([...selectedRows, row]);
    } else {
      setSelectedRows(
        selectedRows.filter((item) => item.span_id !== row.span_id)
      );
    }
  };
  
  const sentinelRef = useRef<HTMLTableRowElement>(null);
  const prevLenRef = useRef<number>(data.length);
  useLayoutEffect(() => {
    if (data.length < prevLenRef.current) {
      virtualizerRef?.current?.scrollTo({ top: 0, behavior: "auto" });
    }
    prevLenRef.current = data.length;
  }, [data.length])
  
  const findRow = (rows: SpanPublic[], uuid?: string) =>
    rows.find((r) => r.uuid === uuid) ??
    rows.flatMap((r) => r.child_spans ?? []).find((r) => r.uuid === uuid);
  
  const selectRow = findRow(data, traceUuid);
  const isSubRow = selectRow?.parent_span_id;
  
  const prefetch = (row: SpanPublic) => {
    queryClient
      .prefetchQuery({
        queryKey: ["spans", row.uuid],
        queryFn: () => fetchSpan(row.uuid),
        staleTime: 60000,
      })
      .catch(() => toast.error("Failed to prefetch"));
    // queryClient
    //   .prefetchQuery({
    //     queryKey: ["spans", row.uuid, "comments"],
    //     queryFn: () => fetchCommentsBySpan(row.uuid),
    //     staleTime: 60000,
    //   })
    //   .catch(() => toast.error("Failed to prefetch"));
  };
  const columns: ColumnDef<SpanPublic>[] = [
    {
      accessorKey: "display_name",
      enableHiding: false,
      filterFn: onlyParentFilter,
      header: () => {
        return hideCompare ? (
          "Name"
        ) : (
          <>
            <Checkbox
              checked={
                selectedRows.length > 0 && selectedRows.length < data.length
                  ? "indeterminate"
                  : selectedRows.length > 0
              }
              onCheckedChange={() => {
                if (selectedRows.length > 0) {
                  setSelectedRows([]);
                } else {
                  setSelectedRows(
                    data.filter((row) => row.scope === Scope.LILYPAD)
                  );
                }
              }}
              aria-label='Select all'
              className='mr-2'
            />
            Name
          </>
        );
      },
      cell: ({ row }) => {
        const depth = row.depth;
        const hasSubRows = row.subRows.length > 0;
        const isSelected = selectedRows.some(
          (item) => item.span_id === row.original.span_id
        );
        const displayName: string = row.getValue("display_name");
        const scope = row.original.scope;
        const isLilypad = scope === Scope.LILYPAD;
        return (
          <div style={{ marginLeft: `${depth * 1.5}rem` }}>
            <div className='flex items-center gap-2'>
              {hasSubRows ? <ExpandRowButton row={row}/> : <Spacer/>}
              {!hideCompare && isLilypad && (
                <Checkbox
                  onClick={(e) => e.stopPropagation()}
                  checked={isSelected}
                  onCheckedChange={(checked) => {
                    handleCheckboxChange(row.original, checked === true);
                  }}
                  aria-label={`Select ${displayName}`}
                  className='mr-2'
                />
              )}
              <span className='truncate'>{displayName}</span>
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
      accessorKey: "tags",
      header: "Tags",
      id: "tags",
      filterFn: tagFilter,
      cell: ({ row }) => {
        const tags: TagPublic[] = row.getValue("tags");
        
        if (!Array.isArray(tags) || tags.length === 0) {
          return null;
        }
        
        return (
          <div className='flex items-center gap-1'>
            <Badge pill variant='outline' size='sm' key={tags[0].uuid}>
              {tags[0].name}
            </Badge>
            {tags.length > 1 && (
              <Badge pill variant='secondary' size='sm' className='px-1.5'>
                +{tags.length - 1}
              </Badge>
            )}
          </div>
        );
      },
    },
    {
      accessorFn: (row) => row.function?.version_num ?? null,
      id: "version",
      meta: { sortUndefined: -1 },
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
                <ArrowUp className='ml-2 h-4 w-4'/>
              ) : (
                <ArrowDown className='ml-2 h-4 w-4'/>
              )
            ) : (
              <ArrowUpDown className='ml-2 h-4 w-4'/>
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
                <ArrowUp className='ml-2 h-4 w-4'/>
              ) : (
                <ArrowDown className='ml-2 h-4 w-4'/>
              )
            ) : (
              <ArrowUpDown className='ml-2 h-4 w-4'/>
            )}
          </Button>
        );
      },
      cell: ({ row }) => {
        return (
          <Typography variant='span' affects='xs' className='truncate'>
            {formatDate(row.getValue("timestamp"))}
          </Typography>
        );
      },
    },
    {
      accessorKey: "annotations",
      header: ({ table }) => {
        const isFiltered = !!table.getColumn("annotations")?.getFilterValue();
        
        return (
          <div className='flex items-center'>
            <Button
              variant='ghost'
              size='sm'
              className='p-0 h-8'
              onClick={() => {
                table
                  .getColumn("annotations")
                  ?.setFilterValue(isFiltered ? undefined : true);
              }}
              title={isFiltered ? "Show all rows" : "Show only annotated rows"}
            >
              <NotebookPen
                className={`w-4 h-4 mr-2 ${isFiltered ? "text-primary" : "text-muted-foreground"}`}
              />
              Annotated
            </Button>
          </div>
        );
      },
      cell: ({ row }) => {
        const annotations: AnnotationPublic[] =
          row.getValue("annotations") ?? [];
        const filteredAnnotations = annotations.filter(
          (annotation) => annotation.label
        );
        if (filteredAnnotations.length > 0) {
          return <NotebookPen className='w-4 h-4'/>;
        }
        return null;
      },
      filterFn: (row, id, filterValue) => {
        // If no filter value is set, show all rows
        if (filterValue === undefined) return true;
        
        // If filter is applied, only show rows with annotations
        const annotations: AnnotationPublic[] = row.getValue(id);
        return annotations.length > 0;
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
                <MoreHorizontal className='h-4 w-4'/>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align='end'>
              <DropdownMenuLabel>Actions</DropdownMenuLabel>
              {row.original.scope === Scope.LILYPAD &&
                row.original.function?.is_versioned &&
                features.playground && (
                  <DropdownMenuItem
                    onClick={() => {
                      const { project_uuid, function: fn } = row.original;
                      if (!fn) return;
                      navigate({
                        to: `/projects/${project_uuid}/functions/${fn.name}/${fn.uuid}/overview`,
                      }).catch(() => {
                        toast.error("Failed to navigate");
                      });
                    }}
                  >
                    Open Playground
                  </DropdownMenuItem>
                )}
              <DropdownMenuSeparator/>
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
      navigate({
        to: path,
        replace: true,
        params: { _splat: undefined },
      }).catch(() => {
        toast.error("Failed to navigate");
      });
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
              fallback={<CardSkeleton items={5} className='flex flex-col'/>}
            >
              {selectedRows[0].scope === Scope.LILYPAD ? (
                <LilypadPanel spanUuid={selectedRows[0].uuid}/>
              ) : (
                <LlmPanel spanUuid={selectedRows[0].uuid}/>
              )}
            </Suspense>
          </div>
          <div className='w-1/2'>
            <h3 className='text-lg font-semibold'>Row 2</h3>
            <Suspense
              fallback={<CardSkeleton items={5} className='flex flex-col'/>}
            >
              {selectedRows[1].scope === Scope.LILYPAD ? (
                <LilypadPanel spanUuid={selectedRows[1].uuid}/>
              ) : (
                <LlmPanel spanUuid={selectedRows[1].uuid}/>
              )}
            </Suspense>
          </div>
        </div>
      </div>
    );
  };
  const customControls = (table: Table<SpanPublic>) => (
    <div className="flex flex-col gap-2 sticky top-0 bg-background z-20 pt-2">
      <div className="flex items-center gap-2">
        <Input
          placeholder="Filter names…"
          value={nameFilter}
          onChange={(e) => {
            const v = e.target.value;
            setName(v);
            table.getColumn("display_name")?.setFilterValue(v);
          }}
          className="max-w-[200px]"
        />
        <div className="relative flex items-center">
          <Input
            key={`tags-input`}
            placeholder='Filter tags...'
            value={(table.getColumn("tags")?.getFilterValue() as string) ?? ""}
            onChange={(event) => {
              table.getColumn("tags")?.setFilterValue(event.target.value);
            }}
            className="pr-10 max-w-[200px]"
          />
          <Popover>
            <PopoverTrigger asChild>
              <SmileIcon
                className='absolute right-3 top-1/2 -translate-y-1/2 cursor-pointer h-5 w-5 opacity-70 hover:opacity-100'/>
            </PopoverTrigger>
            <PopoverContent className='w-fit p-0'>
              <EmojiPicker
                className='h-[342px]'
                onEmojiSelect={(emojiData) => {
                  const currFilter =
                    (table.getColumn("tags")?.getFilterValue() as string) ?? "";
                  table
                    .getColumn("tags")
                    ?.setFilterValue(currFilter + emojiData.emoji);
                }}
              >
                <EmojiPickerContent/>
              </EmojiPicker>
            </PopoverContent>
          </Popover>
        </div>
        <LilypadDialog
          icon={<Users/>}
          title={"Annotate selected traces"}
          description={`${selectedRows.length} trace(s) selected.`}
          buttonProps={{
            disabled: selectedRows.length === 0,
          }}
          tooltipContent={"Add selected traces to your annotation queue."}
        >
          <QueueForm spans={selectedRows}/>
        </LilypadDialog>
        {!hideCompare && (
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
              disabled={selectedRows.length !== 2}
            >
              Compare
            </Button>
          </>
        )}
        {onLoadNewer && (
          <Button
            size="sm"
            variant="secondary"
            onClick={() => {
              void onLoadNewer();
            }}
            disabled={isLoadingNewer}
            className="flex items-center gap-1 ml-4"
          >
            {isLoadingNewer ? (
              <Loader2 className="h-4 w-4 animate-spin"/>
            ) : (
              <ArrowUp className="h-4 w-4"/>
            )}
            Load newer
          </Button>
        )}
      </div>
    </div>
  );
  
  if (toggleCompareMode) {
    return <CompareDetailPanel/>;
  }
  
  return (
    <DataTable<SpanPublic>
      columns={columns}
      data={data}
      virtualizerRef={virtualizerRef}
      ref={tableRef}
      virtualizerOptions={{
        count: data.length,
        estimateSize: () => 45,
        overscan: 20,
      }}
      onRowHover={prefetch}
      customExpanded={isSubRow ? { [isSubRow]: true } : undefined}
      customGetRowId={(row) => row.span_id}
      DetailPanel={DetailPanel}
      defaultPanelSize={50}
      filterColumn={hideCompare ? "display_name" : undefined}
      selectRow={selectRow}
      getRowCanExpand={getRowCanExpand}
      getSubRows={getSubRows}
      customControls={customControls}
      defaultSorting={[{ id: "timestamp", desc: true }]}
      endRef={sentinelRef}
      onReachEnd={onReachEnd}
      isFetchingNextPage={isFetchingNextPage}
      onDetailPanelClose={handleDetailPanelClose}
      path={path}
    />
  );
};
