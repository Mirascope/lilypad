import { useAuth, UserConfig } from "@/src/auth";
import { Button } from "@/src/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuCheckboxItem,
  DropdownMenuContent,
  DropdownMenuTrigger,
} from "@/src/components/ui/dropdown-menu";
import { Input } from "@/src/components/ui/input";
import { ScrollArea, ScrollBar } from "@/src/components/ui/scroll-area";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/src/components/ui/table";
import { useTable } from "@/src/hooks/use-table";
import { cn } from "@/src/lib/utils";
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
import React, { ReactNode, useCallback, useMemo, useState, useEffect } from "react";

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
  onRowClick?: (row: T) => void;
  onRowHover?: (row: T) => void;
  virtualizerRef?: React.RefObject<HTMLDivElement | null>;
  virtualizerOptions: VirtualizerOptions;
  onFilterChange?: (value: string) => void;
  defaultSorting?: SortingState;
  hideColumnButton?: boolean;
  customControls?: (table: TanStackTable<T>) => React.ReactNode;
  customGetRowId?: (row: T) => string;
  customExpanded?: true | Record<string, boolean>;
  customComponent?: ReactNode;
  isFetching?: boolean;
  fetchNextPage?: () => void;
  columnVisibilityStateKey?: string;
  className?: string;
}

export const DataTable = <T extends { uuid: string }>({
  data,
  columns,
  filterColumn,
  getRowCanExpand,
  getSubRows,
  onRowClick,
  onRowHover,
  virtualizerRef,
  virtualizerOptions,
  onFilterChange,
  defaultSorting = [],
  hideColumnButton,
  customControls,
  customGetRowId = undefined,
  customExpanded = {},
  isFetching,
  fetchNextPage,
  columnVisibilityStateKey,
  className,
}: GenericDataTableProps<T>) => {
  const { updateUserConfig, userConfig } = useAuth();
  const [expanded, setExpanded] = useState<true | Record<string, boolean>>(customExpanded);
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

  // Use our context for detail panel and selected rows
  const { detailRow, setDetailRow, onDetailPanelClose, setSelectedRows, selectedRows } = useTable<T>();
  
  // Sync rowSelection when selectedRows is cleared externally
  useEffect(() => {
    if (selectedRows.length === 0 && Object.keys(rowSelection).length > 0) {
      setRowSelection({});
    }
  }, [selectedRows, rowSelection]);

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

  const flattenedData = useMemo(() => {
    // Helper function to flatten data recursively
    const flattenData = (rows: T[]): T[] => {
      return rows.flatMap((row) => {
        // Start with the current row
        const result: T[] = [row];

        // Add all sub-rows if available
        if (getSubRows) {
          const subRows = getSubRows(row);
          if (subRows && subRows.length > 0) {
            result.push(...flattenData(subRows));
          }
        }

        return result;
      });
    };

    return flattenData(data);
  }, [data, getSubRows]); // Recompute only when data or getSubRows changes

  const handleRowSelectionChange: OnChangeFn<RowSelectionState> = (updaterOrValue) => {
    if (typeof updaterOrValue === "function") {
      // First, compute the new selection
      const currentSelection = rowSelection;
      const newSelection = updaterOrValue(currentSelection);

      // Set our local state
      setRowSelection(newSelection);
      // Then extract the selected rows and update context
      const selectedRows = Object.keys(newSelection)
        .filter((key) => newSelection[key])
        .map((key) =>
          flattenedData.find((row) => {
            const rowId = customGetRowId ? customGetRowId(row) : row.uuid;
            return rowId === key;
          })
        )
        .filter((item): item is T => item !== undefined);
      // Schedule the callback to run after render
      queueMicrotask(() => {
        setSelectedRows(selectedRows);
      });
    } else {
      // Set our local state
      setRowSelection(updaterOrValue);

      // Extract the selected rows and update context
      const selectedRows = Object.keys(updaterOrValue)
        .filter((key) => updaterOrValue[key])
        .map((key) =>
          flattenedData.find((row) => {
            const rowId = customGetRowId ? customGetRowId(row) : row.uuid;
            return rowId === key;
          })
        )
        .filter((item): item is T => item !== undefined);
      // Schedule the callback to run after render
      queueMicrotask(() => {
        setSelectedRows(selectedRows);
      });
    }
  };
  const handleColumnVisibilityChange: OnChangeFn<VisibilityState> = (updaterOrValue) => {
    const newVisibility =
      typeof updaterOrValue === "function" ? updaterOrValue(columnVisibility) : updaterOrValue;

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
    // First, find the table row to toggle its selection
    const rowId = customGetRowId ? customGetRowId(row) : row.uuid;
    const tableRow = table.getRowModel().rowsById[rowId];
    
    if (tableRow) {
      // Toggle the checkbox selection
      tableRow.toggleSelected();
    }
    
    // Then handle the detail panel
    if (onRowClick) {
      onRowClick(row);
    } else {
      // Compare using the same ID logic as table rows
      const currentDetailId = detailRow ? (customGetRowId ? customGetRowId(detailRow) : detailRow.uuid) : null;
      const clickedRowId = customGetRowId ? customGetRowId(row) : row.uuid;
      
      if (currentDetailId === clickedRowId) {
        onDetailPanelClose();
      } else {
        setDetailRow(row);
      }
    }
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
        className={`w-full cursor-pointer hover:bg-accent ${
          detailRow?.uuid === row.original.uuid ? "bg-accent/50" : ""
        }`}
        style={{
          paddingLeft: depth > 0 ? `${depth * 1.5}rem` : undefined,
        }}
        onMouseEnter={() => onRowHover?.(row.original)}
        onFocus={() => onRowHover?.(row.original)}
        onClick={() => toggleRowSelection(row.original)}
      >
        {row.getVisibleCells().map((cell) => {
          return (
            <TableCell key={cell.id} className="overflow-hidden text-ellipsis whitespace-nowrap">
              {flexRender(cell.column.columnDef.cell, cell.getContext())}
            </TableCell>
          );
        })}
      </TableRow>
    );
  };
  return (
    <>
      <div className="flex items-center gap-2 rounded-md">
        {filterColumn && (
          <>
            <Input
              placeholder="Filter..."
              value={(table.getColumn(filterColumn)?.getFilterValue() as string) ?? ""}
              onChange={(event) => {
                onFilterChange?.(event.target.value);
                table.getColumn(filterColumn)?.setFilterValue(event.target.value);
              }}
              className="max-w-sm"
            />
          </>
        )}
        {customControls?.(table)}
        {!hideColumnButton && (
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="outline" className="mb-2 ml-auto">
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
                      onCheckedChange={(value) => column.toggleVisibility(!!value)}
                    >
                      {column.id}
                    </DropdownMenuCheckboxItem>
                  );
                })}
            </DropdownMenuContent>
          </DropdownMenu>
        )}
      </div>
      <div
        className={cn("flex min-h-0 flex-1 flex-col overflow-hidden rounded-md border", className)}
      >
        <ScrollArea
          ref={virtualizerRef}
          className="relative overflow-auto rounded-md"
          style={{
            height: virtualizerOptions.containerHeight ?? "100%",
          }}
          onScroll={(e) => fetchMoreOnBottomReached(e.currentTarget)}
        >
          <ScrollBar orientation="horizontal" />
          <Table className="w-full">
            <TableHeader className="sticky top-0 z-10 bg-background">
              {table.getHeaderGroups().map((headerGroup) => (
                <TableRow key={headerGroup.id} className="w-full">
                  {headerGroup.headers.map((header) => (
                    <TableHead key={header.id}>
                      {header.isPlaceholder
                        ? null
                        : flexRender(header.column.columnDef.header, header.getContext())}
                    </TableHead>
                  ))}
                </TableRow>
              ))}
            </TableHeader>
            <TableBody>
              {flatRows.length ? (
                <>
                  {rowVirtualizer.getVirtualItems().length > 0 && (
                    <TableRow
                      style={{
                        height: `${Math.max(0, rowVirtualizer.getVirtualItems()[0].start)}px`,
                      }}
                    />
                  )}

                  {rowVirtualizer.getVirtualItems().map((virtualRow) => {
                    const rowInfo = flatRows[virtualRow.index];
                    if (!rowInfo) return null;
                    return renderRow(rowInfo, virtualRow);
                  })}

                  {rowVirtualizer.getVirtualItems().length > 0 && (
                    <TableRow
                      style={{
                        height: `${Math.max(
                          0,
                          rowVirtualizer.getTotalSize() -
                            (rowVirtualizer.getVirtualItems()[
                              rowVirtualizer.getVirtualItems().length - 1
                            ]?.end || 0)
                        )}px`,
                      }}
                    />
                  )}
                </>
              ) : (
                <TableRow className="w-full">
                  <TableCell colSpan={columns.length} className="h-24 text-center">
                    No results.
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
          {isFetching && <div className="p-2">Fetching More...</div>}
        </ScrollArea>
      </div>
    </>
  );
};
