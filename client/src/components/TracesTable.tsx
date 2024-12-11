import {
  ArrowUpDown,
  ChevronRight,
  MoreHorizontal,
  ArrowUp,
  ArrowDown,
} from "lucide-react";
import { Scope } from "@/types/types";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { SpanPublic } from "@/types/types";
import { ColumnDef, FilterFn } from "@tanstack/react-table";
import { LilypadPanel } from "@/components/LilypadPanel";
import { LlmPanel } from "@/components/LlmPanel";
import { useNavigate } from "@tanstack/react-router";
import { DataTable } from "@/components/DataTable";
import { useRef } from "react";

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

export const TracesTable = ({ data }: { data: SpanPublic[] }) => {
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
        const paddingLeft = `${depth * 1}rem`;
        const hasSubRows = row.subRows.length > 0;
        return (
          <div style={{ paddingLeft }}>
            {hasSubRows && (
              <ChevronRight
                onClick={(event) => {
                  row.toggleExpanded();
                  event.stopPropagation();
                }}
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
      accessorKey: "version_num",
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
              {/* {row.original.scope === Scope.LILYPAD && (
                <DropdownMenuItem
                  onClick={() => {
                    const { project_uuid, version_uuid, version } =
                      row.original;
                    console.log(row.original);
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
    return (
      <div className='p-4 border rounded-md overflow-auto'>
        <h2 className='text-lg font-semibold mb-2'>Row Details</h2>
        {data.scope === Scope.LILYPAD ? (
          <LilypadPanel span={data} />
        ) : (
          <LlmPanel spanId={data.uuid} />
        )}
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
      DetailPanel={DetailPanel}
      defaultPanelSize={50}
      filterColumn='display_name'
      getRowCanExpand={getRowCanExpand}
      getSubRows={getSubRows}
    />
  );
};
