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
import { useVirtualizer } from "@tanstack/react-virtual";
import { ChevronDown } from "lucide-react";
import React, { ReactNode, Suspense, useEffect, useState } from "react";

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
}: GenericDataTableProps<T>) => {
  const [expanded, setExpanded] = useState<true | Record<string, boolean>>(
    customExpanded
  );
  const [sorting, setSorting] = useState<SortingState>(defaultSorting);
  const [columnFilters, setColumnFilters] = useState<ColumnFiltersState>([]);
  const [columnVisibility, setColumnVisibility] = useState<VisibilityState>({});
  const [rowSelection, setRowSelection] = useState<Record<string, boolean>>({});
  const [detailRow, setDetailRow] = useState<T | null | undefined>(
    defaultSelectedRow
  );
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
    onColumnVisibilityChange: setColumnVisibility,
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
  const rowVirtualizer = useVirtualizer({
    count: virtualizerOptions.count,
    getScrollElement: () => virtualizerRef?.current || null,
    estimateSize: virtualizerOptions.estimateSize ?? (() => 45),
    overscan: virtualizerOptions.overscan ?? 10,
    // Use container height from options or default to undefined
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

  const CollapsibleRow = ({ row }: { row: Row<T> }) => {
    return (
      <>
        <TableRow
          key={row.id}
          data-state={row.getIsSelected() && "selected"}
          className={`cursor-pointer hover:bg-secondary ${
            detailRow?.uuid === row.original.uuid ? "bg-primary/20" : ""
          }`}
          onMouseEnter={() => onRowHover?.(row.original)}
          onFocus={() => onRowHover?.(row.original)}
          onClick={() => toggleRowSelection(row.original)}
        >
          {row.getVisibleCells().map((cell) => (
            <TableCell key={cell.id}>
              {flexRender(cell.column.columnDef.cell, cell.getContext())}
            </TableCell>
          ))}
        </TableRow>
        {row.getIsExpanded() &&
          row.subRows.map((subRow) => (
            <CollapsibleRow key={subRow.id} row={subRow} />
          ))}
      </>
    );
  };

  const onCollapse = () => {
    setDetailRow(null);
    onDetailPanelClose?.();
  };
  const paddingTop = rowVirtualizer.getVirtualItems()[0]?.start ?? 0;
  const paddingBottom =
    rowVirtualizer.getTotalSize() -
    (rowVirtualizer.getVirtualItems()[
      rowVirtualizer.getVirtualItems().length - 1
    ]?.end ?? 0);

  return (
    <ResizablePanelGroup
      direction='horizontal'
      className='flex-1 rounded-lg w-full h-full'
    >
      <ResizablePanel
        id='data-table'
        defaultSize={detailRow ? defaultPanelSize : 100}
        order={1}
        className='flex flex-col p-2 gap-2 h-full'
      >
        <div className='flex items-center rounded-md gap-2'>
          {filterColumn && (
            <>
              <Input
                placeholder='Filter...'
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
                className='max-w-sm'
              />
            </>
          )}
          {customControls?.(table)}
          {!hideColumnButton && (
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant='outline' className='ml-auto'>
                  Columns <ChevronDown className='ml-2 h-4 w-4' />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align='end'>
                {table
                  .getAllColumns()
                  .filter((column) => column.getCanHide())
                  .map((column) => {
                    return (
                      <DropdownMenuCheckboxItem
                        key={column.id}
                        className='capitalize'
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

        <div className='flex flex-col overflow-hidden min-h-0 rounded-md border flex-1'>
          <div
            ref={virtualizerRef}
            className='rounded-md overflow-auto h-full'
            style={{
              height: virtualizerOptions.containerHeight ?? "100%",
            }}
          >
            <Table>
              <TableHeader>
                {table.getHeaderGroups().map((headerGroup) => (
                  <TableRow key={headerGroup.id}>
                    {headerGroup.headers.map((header) => (
                      <TableHead key={header.id}>
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
              <TableBody>
                {rows.length ? (
                  <>
                    {paddingTop > 0 && (
                      <TableRow>
                        <TableCell
                          colSpan={columns.length}
                          style={{ height: `${paddingTop}px`, padding: 0 }}
                        />
                      </TableRow>
                    )}
                    {rowVirtualizer.getVirtualItems().map((virtualRow) => {
                      const row = table.getRowModel().rows[virtualRow.index];
                      if (!row) return null;
                      return <CollapsibleRow key={row?.id} row={row} />;
                    })}
                    {paddingBottom > 0 && (
                      <TableRow>
                        <TableCell
                          colSpan={columns.length}
                          style={{ height: `${paddingBottom}px`, padding: 0 }}
                        />
                      </TableRow>
                    )}
                  </>
                ) : (
                  <TableRow>
                    <TableCell
                      colSpan={columns.length}
                      className='h-24 text-center'
                    >
                      No results.
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </div>
        </div>
      </ResizablePanel>

      {detailRow && DetailPanel && (
        <>
          <ResizableHandle withHandle />
          <ResizablePanel
            id='detail-panel'
            defaultSize={defaultPanelSize}
            order={2}
            className='flex flex-col h-full p-4'
            collapsible={true}
            minSize={12}
            onCollapse={onCollapse}
          >
            <Suspense
              fallback={<CardSkeleton items={5} className='flex flex-col' />}
            >
              <DetailPanel data={detailRow} path={path} />
            </Suspense>
          </ResizablePanel>
        </>
      )}
    </ResizablePanelGroup>
  );
};
