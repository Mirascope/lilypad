import React, { useState } from "react";
import { ChevronDown } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuCheckboxItem,
  DropdownMenuContent,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Input } from "@/components/ui/input";
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
  Row,
  SortingState,
  useReactTable,
  VisibilityState,
} from "@tanstack/react-table";
import {
  ResizableHandle,
  ResizablePanel,
  ResizablePanelGroup,
} from "@/components/ui/resizable";

interface GenericDataTableProps<T> {
  data: T[];
  columns: ColumnDef<T>[];
  filterColumn?: string;
  getRowCanExpand?: (row: T) => boolean;
  getSubRows?: (row: T) => T[];
  DetailPanel?: React.ComponentType<{ data: T }>;
  onRowClick?: (row: T) => void;
  defaultPanelSize?: number;
}

export const DataTable = <T extends { uuid: string }>({
  data,
  columns,
  filterColumn,
  getRowCanExpand,
  getSubRows,
  DetailPanel,
  onRowClick,
  defaultPanelSize = 50,
}: GenericDataTableProps<T>) => {
  const [expanded, setExpanded] = useState<true | Record<string, boolean>>({});
  const [sorting, setSorting] = useState<SortingState>([]);
  const [columnFilters, setColumnFilters] = useState<ColumnFiltersState>([]);
  const [columnVisibility, setColumnVisibility] = useState<VisibilityState>({});
  const [rowSelection, setRowSelection] = useState({});
  const [selectedRow, setSelectedRow] = useState<T | null>(null);

  const table = useReactTable({
    data,
    columns,
    onExpandedChange: setExpanded,
    onSortingChange: setSorting,
    onColumnFiltersChange: setColumnFilters,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    getRowCanExpand: getRowCanExpand ? () => true : undefined,
    onColumnVisibilityChange: setColumnVisibility,
    onRowSelectionChange: setRowSelection,
    state: {
      sorting,
      columnFilters,
      columnVisibility,
      rowSelection,
      expanded,
    },
    getSubRows,
  });

  const toggleRowSelection = (row: T) => {
    if (onRowClick) {
      onRowClick(row);
    } else {
      setSelectedRow((prevSelectedRow) =>
        prevSelectedRow && prevSelectedRow.uuid === row.uuid ? null : row
      );
    }
  };

  const CollapsibleRow = ({ row }: { row: Row<T> }) => {
    return (
      <>
        <TableRow
          key={row.id}
          data-state={row.getIsSelected() && "selected"}
          className='cursor-pointer hover:bg-gray-100'
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

  return (
    <ResizablePanelGroup direction='horizontal' className='rounded-lg border'>
      <ResizablePanel
        defaultSize={selectedRow ? defaultPanelSize : 100}
        order={1}
        className='p-2 flex flex-col gap-2'
      >
        <div className='flex items-center rounded-md'>
          {filterColumn && (
            <Input
              placeholder='Filter...'
              value={
                (table.getColumn(filterColumn)?.getFilterValue() as string) ??
                ""
              }
              onChange={(event) =>
                table
                  .getColumn(filterColumn)
                  ?.setFilterValue(event.target.value)
              }
              className='max-w-sm'
            />
          )}
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
        </div>
        <div className='rounded-md border h-[calc(100vh-100px)] overflow-auto'>
          <Table>
            <TableHeader>
              {table.getHeaderGroups().map((headerGroup) => (
                <TableRow key={headerGroup.id}>
                  {headerGroup.headers.map((header) => {
                    return (
                      <TableHead key={header.id}>
                        {header.isPlaceholder
                          ? null
                          : flexRender(
                              header.column.columnDef.header,
                              header.getContext()
                            )}
                      </TableHead>
                    );
                  })}
                </TableRow>
              ))}
            </TableHeader>
            <TableBody>
              {table.getRowModel().rows?.length ? (
                table
                  .getRowModel()
                  .rows.map((row) => <CollapsibleRow key={row.id} row={row} />)
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
      </ResizablePanel>
      {selectedRow && DetailPanel && (
        <>
          <ResizableHandle withHandle />
          <ResizablePanel
            defaultSize={defaultPanelSize}
            order={2}
            style={{ overflowY: "auto" }}
            collapsible={true}
            minSize={12}
            onCollapse={() => setSelectedRow(null)}
          >
            <div className='p-4 border rounded-md overflow-auto'>
              <DetailPanel data={selectedRow} />
            </div>
          </ResizablePanel>
        </>
      )}
    </ResizablePanelGroup>
  );
};
