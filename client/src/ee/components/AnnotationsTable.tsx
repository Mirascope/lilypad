import { DataTable } from "@/components/DataTable";
import IconDialog from "@/components/IconDialog";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { AnnotationPublic, Label } from "@/types/types";
import { ColumnDef, Row } from "@tanstack/react-table";
import { MoreHorizontal } from "lucide-react";
import { useRef } from "react";

export const AnnotationsTable = ({ data }: { data: AnnotationPublic[] }) => {
  const virtualizerRef = useRef<HTMLDivElement>(null);

  const columns: ColumnDef<AnnotationPublic>[] = [
    {
      accessorKey: "input",
      header: "Input",
      enableHiding: false,
      cell: ({ row }) => {
        // Render json in table
        return <div>Placeholder</div>;
      },
    },
    {
      accessorKey: "output",
      header: "Output",
      cell: ({ row }) => {
        return (
          <Tooltip>
            <TooltipTrigger asChild>
              <div className='line-clamp-1'>{row.getValue("output")}</div>
            </TooltipTrigger>
            <TooltipContent className='bg-white text-black'>
              <p className='max-w-xs break-words'>{row.getValue("output")}</p>
            </TooltipContent>
          </Tooltip>
        );
      },
    },
    {
      accessorKey: "label",
      header: "Label",
      cell: ({ row }) => {
        return (
          <div
            className={
              row.getValue("label") === Label.PASS
                ? "text-green-600"
                : "text-destructive"
            }
          >
            {row.getValue("label")}
          </div>
        );
      },
    },
    {
      accessorKey: "reasoning",
      header: "Reasoning",
      cell: ({ row }) => {
        return (
          <Tooltip>
            <TooltipTrigger asChild>
              <div className='line-clamp-1'>{row.getValue("reasoning")}</div>
            </TooltipTrigger>
            <TooltipContent className='bg-white text-black'>
              <p className='max-w-xs break-words'>
                {row.getValue("reasoning")}
              </p>
            </TooltipContent>
          </Tooltip>
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
              <DropdownMenuSeparator />
              <DropdownMenuItem>View more details</DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        );
      },
    },
  ];

  const renderCustomControls = (rows: Row<AnnotationPublic>[]) => {
    const annotations = rows.map((row) => row.original);
    return (
      <IconDialog
        text={"Add to Dataset"}
        title={"Annotate selected traces"}
        description={`${rows.length} trace(s) selected.`}
        tooltipContent={"Add annotations to your dataset."}
      >
        <div>Dummy</div>
      </IconDialog>
    );
  };
  return (
    <DataTable<AnnotationPublic>
      columns={columns}
      data={data}
      virtualizerRef={virtualizerRef}
      virtualizerOptions={{
        count: data.length,
        estimateSize: () => 45,
        overscan: 20,
      }}
      defaultPanelSize={50}
      defaultSorting={[{ id: "timestamp", desc: true }]}
      customControls={renderCustomControls}
    />
  );
};
