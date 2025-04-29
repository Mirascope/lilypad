import { useAuth, UserConfig } from "@/auth";
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
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  ColumnDef,
  ColumnFiltersState,
  flexRender,
  getCoreRowModel,
  getFilteredRowModel,
  getSortedRowModel,
  OnChangeFn,
  Row,
  RowSelectionState,
  SortingState,
  Table as TanStackTable,
  useReactTable,
  VisibilityState,
} from "@tanstack/react-table";
import { useVirtualizer, VirtualItem } from "@tanstack/react-virtual";
import { ChevronDown } from "lucide-react";
import React, {
  ReactNode,
  Suspense,
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";

interface VirtualizerOptions {
  count: number;
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
  customComponent?: ReactNode;
  isFetching?: boolean;
  fetchNextPage?: () => void;
  columnWidths?: Record<string, string>;
  columnVisibilityStateKey?: string;
}

export const DataTable = <T extends { uuid: string }>({
  data,
  columns,
  filterColumn,
  getRowCanExpand,
  getSubRows,
  DetailPanel,
  onRowClick,
  onRowHover,
  defaultPanelSize = 50,
  virtualizerRef,
  virtualizerOptions,
  onFilterChange,
  defaultSorting = [],
  hideColumnButton,
  customControls,
  defaultSelectedRow = null,
  selectRow,
  customGetRowId = undefined,
  customExpanded = {},
  onDetailPanelClose,
  onRowSelectionChange,
  path,
  isFetching,
  fetchNextPage,
  columnWidths = {},
  columnVisibilityStateKey,
}: GenericDataTableProps<T>) => {
  const { updateUserConfig, userConfig } = useAuth();
  const [expanded, setExpanded] = useState<true | Record<string, boolean>>(
    customExpanded
  );
  const [sorting, setSorting] = useState<SortingState>(defaultSorting);
  const [columnFilters, setColumnFilters] = useState<ColumnFiltersState>([]);
  const [columnVisibility, setColumnVisibility] = useState<VisibilityState>(
    columnVisibilityStateKey
      ? ((userConfig?.[columnVisibilityStateKey as keyof UserConfig] as
          | VisibilityState
          | undefined) ?? {})
      : {}
  );
  const [rowSelection, setRowSelection] = useState<Record<string, boolean>>({});
  const [detailRow, setDetailRow] = useState<T | null | undefined>(
    defaultSelectedRow
  );
  const fetchMoreOnBottomReached = useCallback(
    (containerRefElement?: HTMLDivElement | null) => {
      if (containerRefElement) {
        const { scrollHeight, scrollTop, clientHeight } = containerRefElement;
        if (scrollHeight - scrollTop - clientHeight < 500) {
          fetchNextPage?.();
        }
      }
    },
    [fetchNextPage]
  );
  useEffect(() => {
    fetchMoreOnBottomReached(virtualizerRef?.current);
  }, [fetchMoreOnBottomReached, virtualizerRef]);

  const handleRowSelectionChange: OnChangeFn<RowSelectionState> = (
    updaterOrValue
  ) => {
    if (typeof updaterOrValue === "function") {
      setRowSelection((prev) => {
        const newSelection = updaterOrValue(prev);
        onRowSelectionChange?.(newSelection);
        return newSelection;
      });
    } else {
      setRowSelection(updaterOrValue);
      onRowSelectionChange?.(updaterOrValue);
    }
  };
  const handleColumnVisibilityChange: OnChangeFn<VisibilityState> = (
    updaterOrValue
  ) => {
    const newVisibility =
      typeof updaterOrValue === "function"
        ? updaterOrValue(columnVisibility)
        : updaterOrValue;

    setColumnVisibility(newVisibility);

    if (columnVisibilityStateKey) {
      updateUserConfig({
        [columnVisibilityStateKey]: newVisibility,
      });
    }
  };
  const table = useReactTable({
    data,
    columns,
    getRowId: customGetRowId,
    onExpandedChange: setExpanded,
    onSortingChange: setSorting,
    onColumnFiltersChange: setColumnFilters,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    getRowCanExpand: getRowCanExpand ? () => true : undefined,
    onColumnVisibilityChange: handleColumnVisibilityChange,
    onRowSelectionChange: handleRowSelectionChange,
    state: {
      sorting,
      columnFilters,
      columnVisibility,
      rowSelection,
      expanded,
    },
    getSubRows,
  });

  const { rows } = table.getRowModel();
  useEffect(() => {
    setDetailRow(selectRow);
  }, [selectRow]);

  const flatRows = useMemo(() => {
    const flat: { row: Row<T>; depth: number }[] = [];

    const flattenRows = (rows: Row<T>[], depth = 0) => {
      rows.forEach((row) => {
        flat.push({ row, depth });
        if (row.getIsExpanded() && row.subRows.length > 0) {
          flattenRows(row.subRows, depth + 1);
        }
      });
    };

    flattenRows(table.getRowModel().rows);
    return flat;
  }, [rows, expanded]);

  const rowVirtualizer = useVirtualizer({
    count: flatRows.length,
    getScrollElement: () => virtualizerRef?.current ?? null,
    estimateSize: virtualizerOptions.estimateSize ?? (() => 45),
    overscan: virtualizerOptions.overscan ?? 10,
    scrollPaddingStart: 0,
    scrollPaddingEnd: 0,
  });

  const toggleRowSelection = (row: T) => {
    if (onRowClick) {
      onRowClick(row);
    } else {
      setDetailRow((prevSelectedRow) =>
        prevSelectedRow && prevSelectedRow.uuid === row.uuid ? null : row
      );
      onDetailPanelClose?.();
    }
  };

  // Get column width either from columnWidths prop, columnDef.size, or a default
  const getColumnWidth = (columnId: string) => {
    if (columnWidths[columnId]) {
      return columnWidths[columnId];
    }

    const column = table.getColumn(columnId);
    if (column?.columnDef.size) {
      return `${column.columnDef.size}px`;
    }

    return "auto";
  };

  const renderRow = (
    rowInfo: {
      row: Row<T>;
      depth: number;
    },
    virtualRow: VirtualItem
  ) => {
    const { row, depth } = rowInfo;
    return (
      <TableRow
        data-index={virtualRow?.index}
        ref={(node) => virtualRow && rowVirtualizer.measureElement(node)}
        key={row.id}
        data-state={row.getIsSelected() && "selected"}
        className={`w-full absolute cursor-pointer hover:bg-secondary ${
          detailRow?.uuid === row.original.uuid ? "bg-primary/20" : ""
        }`}
        style={{
          transform: `translateY(${virtualRow.start}px)`,
          paddingLeft: depth > 0 ? `${depth * 1.5}rem` : undefined,
        }}
        onMouseEnter={() => onRowHover?.(row.original)}
        onFocus={() => onRowHover?.(row.original)}
        onClick={() => toggleRowSelection(row.original)}
      >
        {row.getVisibleCells().map((cell) => (
          <TableCell
            key={cell.id}
            style={{
              width: getColumnWidth(cell.column.id),
              minWidth: getColumnWidth(cell.column.id),
              maxWidth: getColumnWidth(cell.column.id),
            }}
          >
            {flexRender(cell.column.columnDef.cell, cell.getContext())}
          </TableCell>
        ))}
      </TableRow>
    );
  };

  const onCollapse = () => {
    setDetailRow(null);
    onDetailPanelClose?.();
  };

  return (
    <ResizablePanelGroup
      direction="horizontal"
      className="flex-1 rounded-lg w-full h-full"
    >
      <ResizablePanel
        id="data-table"
        defaultSize={detailRow ? defaultPanelSize : 100}
        order={1}
        className="flex flex-col p-2 gap-2 h-full"
      >
        <div className="flex items-center rounded-md gap-2">
          {filterColumn && (
            <>
              <Input
                placeholder="Filter..."
                value={
                  (table.getColumn(filterColumn)?.getFilterValue() as string) ??
                  ""
                }
                onChange={(event) => {
                  onFilterChange?.(event.target.value);
                  table
                    .getColumn(filterColumn)
                    ?.setFilterValue(event.target.value);
                }}
                className="max-w-sm"
              />
            </>
          )}
          {customControls?.(table)}
          {!hideColumnButton && (
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="outline" className="ml-auto">
                  Columns <ChevronDown className="ml-2 h-4 w-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                {table
                  .getAllColumns()
                  .filter((column) => column.getCanHide())
                  .map((column) => {
                    return (
                      <DropdownMenuCheckboxItem
                        key={column.id}
                        className="capitalize"
                        checked={column.getIsVisible()}
                        onCheckedChange={(value) =>
                          column.toggleVisibility(!!value)
                        }
                      >
                        {column.id}
                      </DropdownMenuCheckboxItem>
                    );
                  })}
              </DropdownMenuContent>
            </DropdownMenu>
          )}
        </div>

        <div className="flex flex-col overflow-hidden min-h-0 rounded-md border flex-1">
          <div
            ref={virtualizerRef}
            onScroll={(e) => fetchMoreOnBottomReached(e.currentTarget)}
            className="rounded-md overflow-auto relative"
            style={{
              height: virtualizerOptions.containerHeight ?? "100%",
            }}
          >
            <Table
              className="w-full"
              style={{
                width: "100%",
              }}
            >
              <TableHeader className="sticky top-0 z-10 bg-white">
                {table.getHeaderGroups().map((headerGroup) => (
                  <TableRow key={headerGroup.id}>
                    {headerGroup.headers.map((header) => (
                      <TableHead
                        key={header.id}
                        style={{
                          width: getColumnWidth(header.id),
                          minWidth: getColumnWidth(header.id),
                          maxWidth: getColumnWidth(header.id),
                        }}
                      >
                        {header.isPlaceholder
                          ? null
                          : flexRender(
                              header.column.columnDef.header,
                              header.getContext()
                            )}
                      </TableHead>
                    ))}
                  </TableRow>
                ))}
              </TableHeader>
              <TableBody
                className="relative"
                style={{
                  height: `${rowVirtualizer.getTotalSize()}px`,
                }}
              >
                {flatRows.length ? (
                  rowVirtualizer.getVirtualItems().map((virtualRow) => {
                    const rowInfo = flatRows[virtualRow.index];
                    if (!rowInfo) return null;
                    return renderRow(rowInfo, virtualRow);
                  })
                ) : (
                  <TableRow>
                    <TableCell
                      colSpan={columns.length}
                      className="h-24 text-center"
                    >
                      No results.
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
            {isFetching && <div>Fetching More...</div>}
          </div>
        </div>
      </ResizablePanel>

      {detailRow && DetailPanel && (
        <>
          <ResizableHandle withHandle />
          <ResizablePanel
            id="detail-panel"
            defaultSize={defaultPanelSize}
            order={2}
            className="flex flex-col h-full p-4"
            collapsible={true}
            minSize={12}
            onCollapse={onCollapse}
          >
            <Suspense
              fallback={<CardSkeleton items={5} className="flex flex-col" />}
            >
              <DetailPanel data={detailRow} path={path} />
            </Suspense>
          </ResizablePanel>
        </>
      )}
    </ResizablePanelGroup>
  );
};
