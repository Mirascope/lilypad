import {
  ArrowUpDown,
  ChevronRight,
  ChevronDown,
  MoreHorizontal,
} from "lucide-react";
import { useState } from "react";
import { Scope } from "@/types/types";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuCheckboxItem,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
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
import { SpanPublic } from "@/types/types";
import {
  ColumnDef,
  ColumnFiltersState,
  FilterFn,
  flexRender,
  getCoreRowModel,
  getFilteredRowModel,
  getSortedRowModel,
  Row,
  SortingState,
  useReactTable,
  VisibilityState,
} from "@tanstack/react-table";
import { LilypadPanel } from "@/components/LilypadPanel";
import {
  ResizableHandle,
  ResizablePanel,
  ResizablePanelGroup,
} from "@/components/ui/resizable";
import { LlmPanel } from "@/components/LlmPanel";
import { useNavigate } from "@tanstack/react-router";

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

export function DataTableDemo({ data }: { data: SpanPublic[] }) {
  const navigate = useNavigate();
  const columns: ColumnDef<SpanPublic>[] = [
    {
      accessorKey: "display_name",
      header: "Name",
      enableHiding: false,
      filterFn: onlyParentFilter,
      cell: ({ row }) => {
        const depth = row.depth;
        const paddingLeft = `${depth * 1}rem`;
        const hasSubRows = row.subRows.length > 0;
        return (
          <div
            style={{ paddingLeft }}
            onClick={(event) => {
              row.toggleExpanded();
              event.stopPropagation();
            }}
          >
            {hasSubRows && (
              <ChevronRight
                className={`h-4 w-4 inline mr-2 ${
                  row.getIsExpanded() ? "rotate-90" : ""
                }`}
              />
            )}
            {row.getValue("display_name")}
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
      header: "Version",
    },
    // {
    //   accessorKey: "output",
    //   header: "Output",
    //   cell: ({ row }) => {
    //     return (
    //       <Tooltip>
    //         <TooltipTrigger asChild>
    //           <div className='line-clamp-1'>{row.getValue("output")}</div>
    //         </TooltipTrigger>
    //         <TooltipContent>
    //           <p className='max-w-xs break-words'>{row.getValue("output")}</p>
    //         </TooltipContent>
    //       </Tooltip>
    //     );
    //   },
    // },
    {
      accessorKey: "created_at",
      id: "timestamp",
      header: ({ column }) => {
        return (
          <Button
            variant='ghost'
            onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
          >
            Timestamp
            <ArrowUpDown className='ml-2 h-4 w-4' />
          </Button>
        );
      },
      cell: ({ row }) => (
        <div className='lowercase'>{row.getValue("timestamp")}</div>
      ),
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
              {row.original.scope === Scope.LILYPAD && (
                <DropdownMenuItem
                  onClick={() => {
                    const { project_id, version_id, id } = row.original;
                    navigate({
                      to: `/projects/${project_id}/versions/${version_id}`,
                      search: {
                        spanId: id,
                      },
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
  const [expanded, setExpanded] = useState<true | Record<string, boolean>>({});
  const [sorting, setSorting] = useState<SortingState>([]);
  const [columnFilters, setColumnFilters] = useState<ColumnFiltersState>([]);
  const [columnVisibility, setColumnVisibility] = useState<VisibilityState>({});
  const [rowSelection, setRowSelection] = useState({});
  const [selectedRow, setSelectedRow] = useState<SpanPublic | null>(null);
  const table = useReactTable({
    data,
    columns,
    onExpandedChange: setExpanded,
    onSortingChange: setSorting,
    onColumnFiltersChange: setColumnFilters,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    getRowCanExpand: (row) => row.original.child_spans.length > 0,
    onColumnVisibilityChange: setColumnVisibility,
    onRowSelectionChange: setRowSelection,
    state: {
      sorting,
      columnFilters,
      columnVisibility,
      rowSelection,
      expanded,
    },
    getSubRows: (row) => row.child_spans || [],
  });

  const toggleRowSelection = (row: SpanPublic) => {
    setSelectedRow((prevSelectedRow: SpanPublic | null) =>
      prevSelectedRow && prevSelectedRow.id === row.id ? null : row
    );
  };

  const CollapsibleRow = ({ row }: { row: Row<SpanPublic> }) => {
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
        defaultSize={selectedRow ? 50 : 100}
        order={1}
        id={"traces-table-container"}
        className='p-2 flex flex-col gap-2'
      >
        <div className='flex items-center rounded-md'>
          <Input
            placeholder='Filter name...'
            value={
              (table.getColumn("display_name")?.getFilterValue() as string) ??
              ""
            }
            onChange={(event) =>
              table
                .getColumn("display_name")
                ?.setFilterValue(event.target.value)
            }
            className='max-w-sm'
          />
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
      {selectedRow && (
        <>
          <ResizableHandle withHandle />
          <ResizablePanel
            defaultSize={50}
            order={2}
            id={`${selectedRow.id}-details`}
            style={{ overflowY: "auto" }}
            collapsible={true}
            minSize={12}
            onCollapse={() => setSelectedRow(null)}
          >
            <div className='p-4 border rounded-md overflow-auto'>
              <h2 className='text-lg font-semibold mb-2'>Row Details</h2>
              {selectedRow.scope === Scope.LILYPAD ? (
                <LilypadPanel span={selectedRow} />
              ) : (
                <LlmPanel span={selectedRow} />
              )}
            </div>
          </ResizablePanel>
        </>
      )}
    </ResizablePanelGroup>
  );
}
