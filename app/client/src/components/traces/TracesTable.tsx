import { DataTable } from "@/src/components/DataTable";
import LilypadDialog from "@/src/components/LilypadDialog";
import { Badge } from "@/src/components/ui/badge";
import { Button } from "@/src/components/ui/button";
import { Checkbox } from "@/src/components/ui/checkbox";
import { DialogFooter } from "@/src/components/ui/dialog";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/src/components/ui/dropdown-menu";
import { EmojiPicker, EmojiPickerContent } from "@/src/components/ui/emoji-picker";
import { Input } from "@/src/components/ui/input";
import { Popover, PopoverContent, PopoverTrigger } from "@/src/components/ui/popover";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/src/components/ui/tooltip";
import { Typography } from "@/src/components/ui/typography";
import { useFeatureAccess } from "@/src/hooks/use-featureaccess";
import { AnnotationPublic, Scope, SpanPublic, TagPublic } from "@/src/types/types";
import { fetchCommentsBySpan } from "@/src/utils/comments";
import { fetchSpan, useDeleteSpanMutation } from "@/src/utils/spans";
import { formatDate } from "@/src/utils/strings";
import { useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "@tanstack/react-router";
import { ColumnDef, FilterFn, Row } from "@tanstack/react-table";
import {
  ArrowDown,
  ArrowUp,
  ArrowUpDown,
  ChevronRight,
  Filter,
  MoreHorizontal,
  NotebookPen,
  SmileIcon,
} from "lucide-react";
import { Dispatch, SetStateAction, useEffect, useRef, useState } from "react";
import { toast } from "sonner";

// Constants for better maintainability
const ROW_HEIGHT = 45; // Must match virtualizerOptions.estimateSize
const EXPANSION_ANIMATION_DELAY_MS = 200; // Wait for expand animation to complete
const PREFETCH_STALE_TIME_MS = 60000; // 1 minute cache for prefetched data

const tagFilter = (row: Row<SpanPublic>, columnId: string, filterValue: string): boolean => {
  const tags: TagPublic[] = row.getValue(columnId);

  if (!filterValue || filterValue.trim() === "") {
    return true;
  }
  if (!Array.isArray(tags) || tags.length === 0) {
    return false;
  }

  // Convert filter value to lowercase for case-insensitive comparison
  const filterLower = filterValue.toLowerCase();

  // Check if any tag name includes the filter value
  return tags.some((tag) => tag.name.toLowerCase().includes(filterLower));
};

// Custom filter function
const onlyParentFilter: FilterFn<SpanPublic> = (row, columnId, filterValue) => {
  const isParent = row.original.child_spans && row.original.child_spans.length > 0;

  if (isParent) {
    const cellValue = row.getValue(columnId);
    return String(cellValue).toLowerCase().includes(String(filterValue).toLowerCase());
  }

  // Always include child rows
  return true;
};

const Spacer = () => <div className="h-4 w-4" />;
const ExpandRowButton = ({ row }: { row: Row<SpanPublic> }) => {
  return (
    <ChevronRight
      onClick={(event) => {
        row.toggleExpanded();
        event.stopPropagation();
      }}
      className={`h-4 w-4 transition-transform ${row.getIsExpanded() ? "rotate-90" : ""}`}
    />
  );
};

interface TracesTableProps {
  data?: SpanPublic[];
  traceUuid?: string;
  projectUuid: string;
  /** true while useInfiniteQuery is fetching next page */
  isFetchingNextPage?: boolean;
  isSearch: boolean;
  order: "asc" | "desc";
  onOrderChange: (o: "asc" | "desc", order_by_column: "version" | "created_at") => void;
  fetchNextPage?: () => void;
  filterColumn?: string;
  /** Optional prop to access compare view state */
  onCompareViewToggle?: (isComparing: boolean) => void;
  className?: string;
}

export const TracesTable = ({
  data = [],
  traceUuid,
  projectUuid,
  isFetchingNextPage = false,
  isSearch = false,
  order,
  onOrderChange,
  fetchNextPage,
  filterColumn,
  className,
}: TracesTableProps) => {
  const navigate = useNavigate();
  const features = useFeatureAccess();
  const queryClient = useQueryClient();
  const virtualizerRef = useRef<HTMLDivElement>(null);
  const [deleteSpan, setDeleteSpan] = useState<string | null>(null);
  const [tagFilterOpen, setTagFilterOpen] = useState<boolean>(false);

  const findRow = (rows: SpanPublic[], uuid?: string) =>
    rows.find((r) => r.uuid === uuid) ??
    rows.flatMap((r) => r.child_spans ?? []).find((r) => r.uuid === uuid);
  const selectRow = findRow(data, traceUuid);

  // Scroll to highlighted row only on initial load or when traceUuid changes
  const [hasScrolledToRow, setHasScrolledToRow] = useState(false);

  useEffect(() => {
    if (traceUuid && virtualizerRef.current && data.length > 0 && !hasScrolledToRow) {
      // Find the index of the row to scroll to
      const findRowIndex = (rows: SpanPublic[], uuid: string): number => {
        let currentIndex = 0;

        for (const row of rows) {
          if (row.uuid === uuid) {
            return currentIndex;
          }
          currentIndex++;

          // Check child spans if parent is expanded
          const childSpans = row.child_spans || [];
          if (childSpans.length > 0) {
            for (const childSpan of childSpans) {
              if (childSpan.uuid === uuid) {
                return currentIndex;
              }
              currentIndex++;
            }
          }
        }
        return -1;
      };

      const rowIndex = findRowIndex(data, traceUuid);
      if (rowIndex !== -1) {
        // Delay to ensure the table is rendered and expanded
        setTimeout(() => {
          const scrollContainer = virtualizerRef.current;
          if (scrollContainer) {
            // Calculate the position to scroll to
            const targetPosition = rowIndex * ROW_HEIGHT;
            const containerHeight = scrollContainer.clientHeight;
            const scrollTo = Math.max(0, targetPosition - containerHeight / 2 + ROW_HEIGHT / 2);

            scrollContainer.scrollTo({
              top: scrollTo,
              behavior: "smooth",
            });

            // Mark that we've scrolled to prevent future auto-scrolls
            setHasScrolledToRow(true);
          }
        }, EXPANSION_ANIMATION_DELAY_MS);
      }
    }
  }, [traceUuid, data, hasScrolledToRow]);

  // Reset scroll flag when traceUuid changes
  useEffect(() => {
    setHasScrolledToRow(false);
  }, [traceUuid]);

  const prefetch = (row: SpanPublic) => {
    queryClient
      .prefetchQuery({
        queryKey: ["spans", row.uuid],
        queryFn: () => fetchSpan(row.uuid),
        staleTime: PREFETCH_STALE_TIME_MS,
      })
      .catch(() => toast.error("Failed to prefetch"));
    queryClient
      .prefetchQuery({
        queryKey: ["spans", row.uuid, "comments"],
        queryFn: () => fetchCommentsBySpan(row.uuid),
        staleTime: PREFETCH_STALE_TIME_MS,
      })
      .catch(() => toast.error("Failed to prefetch"));
  };

  const columns: ColumnDef<SpanPublic>[] = [
    {
      accessorKey: "display_name",
      enableHiding: false,
      filterFn: onlyParentFilter,
      size: 250,
      header: ({ table }) => {
        return (
          <div className="flex items-center gap-2">
            <Spacer />
            <Checkbox
              checked={
                table.getIsAllPageRowsSelected() ||
                (table.getIsSomePageRowsSelected() && "indeterminate")
              }
              onCheckedChange={(value) => table.toggleAllPageRowsSelected(!!value)}
              aria-label="Select all"
              className="mr-2"
            />
            Name
          </div>
        );
      },
      cell: ({ row }) => {
        const depth = row.depth;
        const hasSubRows = row.subRows.length > 0;
        const isSelected = row.getIsSelected();
        const displayName: string = row.getValue("display_name");
        return (
          <div style={{ marginLeft: `${depth * 1.5}rem` }} className="w-full">
            <div className="flex items-center gap-2">
              {hasSubRows ? <ExpandRowButton row={row} /> : <Spacer />}
              <Checkbox
                onClick={(e) => e.stopPropagation()}
                checked={isSelected}
                onCheckedChange={(checked) =>
                  row.toggleSelected(!!checked, {
                    selectChildren: false,
                  })
                }
                aria-label={`Select ${displayName}`}
                className="mr-2"
              />
              <span className="truncate">{displayName}</span>
            </div>
          </div>
        );
      },
    },
    ...(isSearch
      ? ([
          {
            accessorKey: "score",
            id: "score",
            size: 100,
            header: ({ column }) => {
              return (
                <Button
                  className="p-0"
                  variant="ghost"
                  onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
                >
                  Score
                  {column.getIsSorted() ? (
                    column.getIsSorted() === "asc" ? (
                      <ArrowUp className="ml-2 h-4 w-4" />
                    ) : (
                      <ArrowDown className="ml-2 h-4 w-4" />
                    )
                  ) : (
                    <ArrowUpDown className="ml-2 h-4 w-4" />
                  )}
                </Button>
              );
            },
            cell: ({ row }) => {
              const score: number = row.getValue("score");
              return (
                <Typography variant="span" affects="xs" className="truncate">
                  {score?.toFixed(2)}
                </Typography>
              );
            },
          },
        ] as ColumnDef<SpanPublic>[])
      : []),
    {
      accessorKey: "scope",
      header: "Scope",
      size: 100,
    },
    {
      accessorKey: "tags",
      header: ({ table }) => {
        return (
          <div className="flex items-center gap-1">
            <Popover open={tagFilterOpen} onOpenChange={setTagFilterOpen}>
              <PopoverTrigger asChild>
                <Button variant="ghost" size="sm" className="ml-1 h-8 p-0" title="Filter tags">
                  Tags
                  <Filter
                    className={`h-4 w-4 ${
                      table.getColumn("tags")?.getFilterValue()
                        ? "text-primary"
                        : "text-muted-foreground"
                    }`}
                  />
                </Button>
              </PopoverTrigger>
              <PopoverContent className="w-80 p-2">
                <div className="space-y-2">
                  <div className="relative">
                    <Input
                      placeholder="Filter tags..."
                      value={(table.getColumn("tags")?.getFilterValue() as string) ?? ""}
                      onChange={(event) => {
                        table.getColumn("tags")?.setFilterValue(event.target.value);
                      }}
                      className="pr-10"
                    />
                    <Popover>
                      <PopoverTrigger asChild>
                        <SmileIcon className="absolute top-1/2 right-3 h-5 w-5 -translate-y-1/2 cursor-pointer opacity-70 hover:opacity-100" />
                      </PopoverTrigger>
                      <PopoverContent className="w-fit p-0">
                        <EmojiPicker
                          className="h-[342px]"
                          onEmojiSelect={(emojiData) => {
                            const currFilter =
                              (table.getColumn("tags")?.getFilterValue() as string) ?? "";
                            table.getColumn("tags")?.setFilterValue(currFilter + emojiData.emoji);
                          }}
                        >
                          <EmojiPickerContent />
                        </EmojiPicker>
                      </PopoverContent>
                    </Popover>
                  </div>
                </div>
              </PopoverContent>
            </Popover>
          </div>
        );
      },
      id: "tags",
      size: 150,
      filterFn: tagFilter,
      cell: ({ row }) => {
        const tags: TagPublic[] = row.getValue("tags");

        if (!Array.isArray(tags) || tags.length === 0) {
          return null;
        }

        return (
          <div className="flex items-center gap-1">
            <Badge variant="neutral" size="sm" key={tags[0].uuid}>
              {tags[0].name}
            </Badge>
            {tags.length > 1 && (
              <Badge variant="neutral" size="sm" className="px-1.5">
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
      size: 100,
      meta: { sortUndefined: -1 },
      header: ({ table }) => {
        const isAsc = order === "asc";
        return (
          <Button
            className="p-0"
            variant="ghost"
            onClick={() => {
              const next = isAsc ? "desc" : "asc";
              onOrderChange(next, "version");
              table.setSorting([{ id: "version", desc: next === "desc" }]);
            }}
          >
            Version
            {isAsc ? <ArrowUp className="ml-2 h-4 w-4" /> : <ArrowDown className="ml-2 h-4 w-4" />}
          </Button>
        );
      },
    },
    {
      accessorKey: "status",
      id: "status",
      header: "Status",
      size: 100,
      cell: ({ row }) => {
        const status: string = row.getValue("status");
        if (status === "UNSET") return null;
        else if (status === "ERROR") {
          return (
            <Badge variant="destructive" size="sm">
              {status}
            </Badge>
          );
        } else return <Badge size="sm">{status}</Badge>;
      },
    },
    {
      accessorKey: "created_at",
      id: "timestamp",
      size: 200,
      header: ({ table }) => {
        const isAsc = order === "asc";
        return (
          <Button
            className="p-0"
            variant="ghost"
            onClick={() => {
              const next = isAsc ? "desc" : "asc";
              onOrderChange(next, "created_at");
              table.setSorting([{ id: "timestamp", desc: next === "desc" }]);
            }}
          >
            Timestamp
            {isAsc ? <ArrowUp className="ml-2 h-4 w-4" /> : <ArrowDown className="ml-2 h-4 w-4" />}
          </Button>
        );
      },
      cell: ({ row }) => {
        return (
          <Typography variant="span" affects="xs" className="truncate">
            {formatDate(row.getValue("timestamp"))}
          </Typography>
        );
      },
    },
    {
      accessorKey: "annotations",
      size: 100,
      header: ({ table }) => {
        const isFiltered = !!table.getColumn("annotations")?.getFilterValue();

        return (
          <div className="flex items-center">
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-8 p-0"
                  onClick={() => {
                    table.getColumn("annotations")?.setFilterValue(isFiltered ? undefined : true);
                  }}
                  title={isFiltered ? "Show all rows" : "Show only annotated rows"}
                >
                  <NotebookPen
                    className={`mr-2 h-4 w-4 ${isFiltered ? "text-primary" : "text-muted-foreground"}`}
                  />
                </Button>
              </TooltipTrigger>
              <TooltipContent>Annotations</TooltipContent>
            </Tooltip>
          </div>
        );
      },
      cell: ({ row }) => {
        const annotations: AnnotationPublic[] = row.getValue("annotations") ?? [];
        const filteredAnnotations = annotations.filter((annotation) => annotation.label);
        if (filteredAnnotations.length > 0) {
          return <NotebookPen className="h-4 w-4" />;
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
      size: 50,
      enableHiding: false,
      cell: ({ row }) => {
        return (
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" className="h-8 w-8 p-0">
                <span className="sr-only">Open menu</span>
                <MoreHorizontal className="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
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
              <DropdownMenuSeparator />
              <DropdownMenuItem>View more details</DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        );
      },
    },
  ];

  const getRowCanExpand = (row: SpanPublic) =>
    Array.isArray(row.child_spans) && row.child_spans.length > 0;
  const getSubRows = (row: SpanPublic) => row.child_spans || [];

  return (
    <>
      <DataTable<SpanPublic>
        className={className}
        columns={columns}
        data={data}
        virtualizerRef={virtualizerRef}
        virtualizerOptions={{
          count: data.length,
          estimateSize: () => ROW_HEIGHT,
          overscan: 20,
        }}
        onRowHover={prefetch}
        customExpanded={(() => {
          // If we're selecting a child row, expand all parent rows in the hierarchy
          if (selectRow?.parent_span_id) {
            const expandedRows: Record<string, boolean> = {};

            // Helper to find all parent span IDs in the hierarchy
            const findAllParents = (span: SpanPublic | undefined): void => {
              if (!span?.parent_span_id) return;

              // Find the parent row
              const parentRow = data.find((r) => r.span_id === span.parent_span_id);
              if (parentRow) {
                expandedRows[parentRow.span_id] = true;
                // Recursively find grandparents
                findAllParents(parentRow);
              }
            };

            findAllParents(selectRow);
            return Object.keys(expandedRows).length > 0 ? expandedRows : undefined;
          }
          return undefined;
        })()}
        customGetRowId={(row) => row.span_id}
        filterColumn={filterColumn}
        getRowCanExpand={getRowCanExpand}
        getSubRows={getSubRows}
        defaultSorting={
          isSearch ? [{ id: "score", desc: true }] : [{ id: "timestamp", desc: true }]
        }
        isFetching={isFetchingNextPage}
        fetchNextPage={fetchNextPage}
        columnVisibilityStateKey="tracesTableVisibilityState"
      />
      {deleteSpan && (
        <DeleteSpanDialog setOpen={setDeleteSpan} spanUuid={deleteSpan} projectUuid={projectUuid} />
      )}
    </>
  );
};

interface DeleteSpanDialogProps {
  projectUuid: string;
  spanUuid: string;
  setOpen: Dispatch<SetStateAction<string | null>>;
}

const DeleteSpanDialog = ({ projectUuid, spanUuid, setOpen }: DeleteSpanDialogProps) => {
  const deleteSpanMutation = useDeleteSpanMutation();
  const handleSpanDelete = async () => {
    await deleteSpanMutation
      .mutateAsync({
        projectUuid,
        spanUuid,
      })
      .catch(() => toast.error("Failed to delete span"));
    toast.success("Span deleted successfully");
    setOpen(null);
  };
  return (
    <LilypadDialog
      open={Boolean(spanUuid)}
      onOpenChange={() => setOpen(null)}
      noTrigger
      title={"Delete Span"}
      description={"Are you sure you want to delete this span?"}
    >
      <DialogFooter>
        <Button key="submit" onClick={handleSpanDelete} className="w-full">
          Delete Span
        </Button>
      </DialogFooter>
    </LilypadDialog>
  );
};
