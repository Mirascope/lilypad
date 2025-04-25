import CardSkeleton from "@/components/CardSkeleton";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuCheckboxItem,
  DropdownMenuContent,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Input } from "@/components/ui/input";
import {
  ResizableHandle,
  ResizablePanel,
  ResizablePanelGroup,
} from "@/components/ui/resizable";
import {
  Table,
  TableBody,
  TableCell,
  TableRow,
} from "@/components/ui/table";
import {
  ColumnDef,
  ColumnFiltersState,
  flexRender,
  getCoreRowModel,
  getFilteredRowModel,
  getSortedRowModel,
  Row,
  RowSelectionState,
  SortingState,
  Table as TanStackTable,
  useReactTable,
  VisibilityState,
} from "@tanstack/react-table";
import { useVirtualizer } from "@tanstack/react-virtual";
import { ChevronDown } from "lucide-react";
import React, { ReactNode, Suspense, useEffect, useImperativeHandle, useRef, useState } from "react";

interface VirtualizerOptions {
  count?: number;
  estimateSize?: (index: number) => number;
  overscan?: number;
  containerHeight?: number;
}

interface GenericDataTableProps<T> {
  data: T[];
  columns: ColumnDef<T>[];
  filterColumn?: string;
  getRowCanExpand?: (row: T) => boolean;
  getSubRows?: (row: T) => T[];
  DetailPanel?: React.ComponentType<{ data: T; path?: string }>;
  onRowClick?: (row: T) => void;
  onRowHover?: (row: T) => void;
  defaultPanelSize?: number;
  virtualizerRef?: React.RefObject<HTMLDivElement | null>;
  virtualizerOptions: VirtualizerOptions;
  onFilterChange?: (value: string) => void;
  defaultSorting?: SortingState;
  hideColumnButton?: boolean;
  customControls?: (table: TanStackTable<T>) => React.ReactNode;
  defaultSelectedRow?: T | null;
  selectRow?: T | null;
  customGetRowId?: (row: T) => string;
  customExpanded?: true | Record<string, boolean>;
  onDetailPanelClose?: () => void;
  onRowSelectionChange?: (row: RowSelectionState) => void;
  path?: string;
  isFetchingNextPage?: boolean;
  onReachEnd?: () => Promise<void> | void;
  endRef?: React.Ref<HTMLTableRowElement>;
  customComponent?: ReactNode;
  bouncePx?: number;
}

export interface DataTableHandle {
  scrollTop: () => void;
}

export function DataTable<T extends { uuid: string }>({
    data,
    columns,
    filterColumn,
    getRowCanExpand,
    getSubRows,
    DetailPanel,
    onRowClick,
    onRowHover,
    defaultPanelSize = 10,
    virtualizerOptions = {},
    onFilterChange,
    defaultSorting = [],
    hideColumnButton,
    customControls,
    defaultSelectedRow = null,
    customGetRowId,
    customExpanded = {},
    onDetailPanelClose,
    onRowSelectionChange,
    path,
    isFetchingNextPage,
    onReachEnd,
    virtualizerRef,
    endRef,
    bouncePx,
  }: GenericDataTableProps<T>,
  ref: React.Ref<DataTableHandle>,
) {
  const [expanded, setExpanded] = useState<true | Record<string, boolean>>(customExpanded);
  const [sorting, setSorting] = useState<SortingState>(defaultSorting);
  const [columnFilters, setColF] = useState<ColumnFiltersState>([]);
  const [columnVisibility, setVis] = useState<VisibilityState>({});
  const [rowSelection, setRowSelection] = useState<RowSelectionState>({});
  const [detailRow, setDetail] = useState<T | null | undefined>(defaultSelectedRow);
  const internalScrollElRef = useRef<HTMLDivElement>(null);
  const scrollElRef = virtualizerRef ?? internalScrollElRef;
  const MIN_LOADER_MS = 600;
  const [showLoader, setShowLoader] = useState(false);
  const loaderTimer = useRef<NodeJS.Timeout | null>(null);
  
  const table = useReactTable({
    data,
    columns,
    getRowId: customGetRowId,
    getSubRows,
    getRowCanExpand: getRowCanExpand ? () => true : undefined,
    state: {
      sorting,
      columnFilters,
      columnVisibility,
      rowSelection,
      expanded,
    },
    onExpandedChange: setExpanded,
    onSortingChange: setSorting,
    onColumnFiltersChange: setColF,
    onColumnVisibilityChange: setVis,
    onRowSelectionChange: (u) => {
      const next =
        typeof u === "function" ? u(rowSelection) : (u as RowSelectionState);
      setRowSelection(next);
      onRowSelectionChange?.(next);
    },
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
  });
  const rows = table.getRowModel().rows;
  
  
  useImperativeHandle(ref, () => ({
    scrollTop: () => scrollElRef.current?.scrollTo({ top: 0, behavior: "auto" }),
  }));
  
  const rowVirtualizer = useVirtualizer({
    count: virtualizerOptions.count ?? rows.length + (isFetchingNextPage ? 1 : 0),
    overscan: virtualizerOptions.overscan ?? 10,
    estimateSize: virtualizerOptions.estimateSize ?? (() => 45),
    getScrollElement: () => scrollElRef.current,
  });
  
  const internalSentinel = useRef<HTMLTableRowElement>(null);
  const sentinelRef = (endRef as React.RefObject<HTMLTableRowElement>) ?? internalSentinel;
  
  const fetchLockRef = useRef(false);
  const bouncedRef = useRef(false);
  
  const BOUNCE_PX = bouncePx ?? 0;
  useEffect(() => {
    if (!onReachEnd || !sentinelRef.current) return;
    
    const observer = new IntersectionObserver(
      async ([entry]) => {
        if (!entry.isIntersecting) {
          fetchLockRef.current = false;
          bouncedRef.current = false;
          return;
        }
        
        if (isFetchingNextPage || fetchLockRef.current) return;
        
        if (!bouncedRef.current && BOUNCE_PX) {
          scrollElRef.current?.scrollBy({
            top: -BOUNCE_PX,
            behavior: "smooth",
          });
          bouncedRef.current = true;
        }
        
        fetchLockRef.current = true;
        await onReachEnd?.();
      },
      { root: scrollElRef.current, threshold: 0.15 },
    );
    
    observer.observe(sentinelRef.current);
    return () => observer.disconnect();
  }, [onReachEnd, isFetchingNextPage, sentinelRef, scrollElRef]);
  
  
  useEffect(() => {
    if (isFetchingNextPage) {
      setShowLoader(true);
      if (loaderTimer.current) clearTimeout(loaderTimer.current);
    } else {
      loaderTimer.current = setTimeout(
        () => setShowLoader(false),
        MIN_LOADER_MS
      );
    }
    return () => {
      if (loaderTimer.current) {
        clearTimeout(loaderTimer.current);
      }
    };
  }, [isFetchingNextPage]);
  
  const paddingTop =
    rowVirtualizer.getVirtualItems()[0]?.start ?? 0;
  const paddingBottom =
    rowVirtualizer.getTotalSize() -
    (rowVirtualizer.getVirtualItems().at(-1)?.end ?? 0);
  
  const Collapsible = ({ row }: { row: Row<T> }) => (
    <>
      <TableRow
        data-row-index={row.index}
        className={`cursor-pointer hover:bg-secondary ${
          detailRow?.uuid === row.original.uuid ? "bg-primary/20" : ""
        }`}
        onClick={() => {
          if (onRowClick) onRowClick(row.original);
          else {
            setDetail((prev) => (prev?.uuid === row.original.uuid ? null : row.original));
            if (detailRow?.uuid === row.original.uuid) onDetailPanelClose?.();
          }
        }}
        onMouseEnter={() => onRowHover?.(row.original)}
        onFocus={() => onRowHover?.(row.original)}
      >
        {row.getVisibleCells().map((c) => (
          <TableCell key={c.id}>
            {flexRender(c.column.columnDef.cell, c.getContext())}
          </TableCell>
        ))}
      </TableRow>
      {row.getIsExpanded() &&
        row.subRows.map((s) => <Collapsible key={s.id} row={s}/>)}
    </>
  );
  
  return (
    <ResizablePanelGroup direction="horizontal" className="flex-1 rounded-lg">
      <ResizablePanel defaultSize={detailRow ? defaultPanelSize : 100} order={1}>
        <div className="flex items-center gap-2 p-2">
          {filterColumn && (
            <Input
              placeholder="Filter..."
              value={(table.getColumn(filterColumn)?.getFilterValue() as string) ?? ""}
              onChange={(e) => {
                onFilterChange?.(e.target.value);
                table.getColumn(filterColumn)?.setFilterValue(e.target.value);
              }}
              className="max-w-sm"
            />
          )}
          {customControls?.(table)}
          {!hideColumnButton && (
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="outline" className="ml-auto">
                  Columns <ChevronDown className="ml-2 h-4 w-4"/>
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                {table.getAllColumns().filter((c) => c.getCanHide()).map((c) => (
                  <DropdownMenuCheckboxItem
                    key={c.id}
                    className="capitalize"
                    checked={c.getIsVisible()}
                    onCheckedChange={(v) => c.toggleVisibility(!!v)}
                  >
                    {c.id}
                  </DropdownMenuCheckboxItem>
                ))}
              </DropdownMenuContent>
            </DropdownMenu>
          )}
        </div>
        <table className="w-full text-sm border-separate border-spacing-0">
          <thead>
          {table.getHeaderGroups().map(hg => (
            <tr key={hg.id} className="bg-background sticky top-[48px] z-20">
              {hg.headers.map(h => (
                <th key={h.id} className="px-3 py-2 text-left font-medium">
                  {flexRender(h.column.columnDef.header, h.getContext())}
                </th>
              ))}
            </tr>
          ))}
          </thead>
        </table>
        <div
          ref={scrollElRef}
          className="relative overflow-auto h-full"
          style={{
            height: virtualizerOptions.containerHeight ?? "100%",
            pointerEvents: isFetchingNextPage ? "none" : "auto",
          }}
          aria-busy={isFetchingNextPage}
        >
          {showLoader && (
            <div className="absolute left-1/2 -translate-x-1/2 bottom-16
                              flex items-center justify-center rounded-md
                              bg-background/90 px-3 py-1 shadow pointer-events-none">
                <span className="text-sm text-muted-foreground">
                  Fetching more results…
                </span>
            </div>
          )}
          
          <Table className="w-full caption-bottom text-sm border-separate border-spacing-0">
            <TableBody>
              {paddingTop > 0 && (
                <TableRow>
                  <TableCell style={{ height: paddingTop, padding: 0 }} colSpan={columns.length}/>
                </TableRow>
              )}
              
              {rowVirtualizer.getVirtualItems().map((virtualRow) => {
                const row = rows[virtualRow.index];
                if (!row) return null;
                // eslint-disable-next-line react/prop-types
                return <Collapsible key={row?.id} row={row}/>;
              })}
              
              {paddingBottom > 0 && (
                <TableRow>
                  <TableCell
                    colSpan={columns.length}
                    style={{ height: `${paddingBottom}px`, padding: 0 }}
                  />
                </TableRow>
              )}
              {isFetchingNextPage && (
                <TableRow>
                  <TableCell colSpan={columns.length} className="py-2 text-center text-muted-foreground text-sm italic">
                    Fetching more results...
                  </TableCell>
                </TableRow>
              )}
              <TableRow ref={sentinelRef}>
                <TableCell colSpan={columns.length} className="h-24 p-0"/>
              </TableRow>
            </TableBody>
          </Table>
        </div>
      </ResizablePanel>
      
      {detailRow && DetailPanel && (
        <>
          <ResizableHandle withHandle/>
          <ResizablePanel
            id='detail-panel'
            defaultSize={defaultPanelSize}
            order={2}
            collapsible
            minSize={12}
            onCollapse={() => {
              setDetail(null);
              onDetailPanelClose?.();
            }}
            className="p-4"
          >
            <Suspense
              fallback={<CardSkeleton items={5} className='flex flex-col'/>}
            >
              <DetailPanel data={detailRow} path={path}/>
            </Suspense>
          </ResizablePanel>
        </>
      )}
    </ResizablePanelGroup>
  );
}
