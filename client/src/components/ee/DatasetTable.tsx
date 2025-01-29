import CardSkeleton from "@/components/CardSkeleton";
import { DataTable } from "@/components/DataTable";
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
import { ColumnDef } from "@tanstack/react-table";
import { MoreHorizontal } from "lucide-react";
import { Suspense, useRef } from "react";

export const DatasetTable = ({
  generationUuid,
}: {
  generationUuid?: string;
}) => {
  const virtualizerRef = useRef<HTMLDivElement>(null);
  const data: AnnotationPublic[] = [
    {
      uuid: "1",
      generation_uuid: "1",
      span_uuid: "1",
      input: { a: "test" },
      output: "test",
      label: Label.PASS,
      reasoning: "test",
    },
    {
      uuid: "2",
      generation_uuid: "1",
      span_uuid: "2",
      input: { a: "test", b: "1" },
      output: "test",
      label: Label.FAIL,
      reasoning: "test",
    },
  ];
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

  const DetailPanel = ({ data }: { data: AnnotationPublic }) => {
    return (
      <div className='p-4 border rounded-md overflow-auto'>
        <h2 className='text-lg font-semibold mb-2'>Row Details</h2>
        <Suspense
          fallback={<CardSkeleton items={5} className='flex flex-col' />}
        >
          <div>Placeholder</div>
        </Suspense>
      </div>
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
      DetailPanel={DetailPanel}
      defaultPanelSize={50}
      //   filterColumn='display_name'
      //   defaultSorting={[{ id: "timestamp", desc: true }]}
    />
  );
};
