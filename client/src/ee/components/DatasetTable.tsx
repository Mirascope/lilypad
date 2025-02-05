import { DataTable } from "@/components/DataTable";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { getDatasetByGenerationUuidQueryOptions } from "@/ee/utils/datasets";
import { DatasetRow, Label } from "@/types/types";
import { useSuspenseQuery } from "@tanstack/react-query";
import { ColumnDef } from "@tanstack/react-table";
import JsonView from "@uiw/react-json-view";
import { useRef } from "react";

export const DatasetTable = ({
  projectUuid,
  generationUuid,
}: {
  projectUuid: string;
  generationUuid: string;
}) => {
  const { data: datasetResponse } = useSuspenseQuery(
    getDatasetByGenerationUuidQueryOptions(projectUuid, generationUuid)
  );
  const data = datasetResponse?.rows || [];
  const virtualizerRef = useRef<HTMLDivElement>(null);
  const passData = data.filter((row) => row.label === Label.PASS);
  const columns: ColumnDef<DatasetRow>[] = [
    {
      accessorKey: "input",
      header: "Input",
      enableHiding: false,
      cell: ({ row }) => {
        // Render json in table
        if (!row.original.input) return "N/A";
        return (
          <Tooltip>
            <TooltipTrigger asChild>
              <div className='line-clamp-1'>{row.original.input}</div>
            </TooltipTrigger>
            <TooltipContent className='bg-white text-black'>
              {<JsonView value={JSON.parse(row.original.input)} />}
            </TooltipContent>
          </Tooltip>
        );
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
  ];

  return (
    <DataTable<DatasetRow>
      columns={columns}
      data={data}
      virtualizerRef={virtualizerRef}
      virtualizerOptions={{
        count: data.length,
        estimateSize: () => 45,
        overscan: 20,
      }}
      defaultPanelSize={50}
      customControls={() => (
        <div>
          {passData.length} out of {data.length} passed.
        </div>
      )}
    />
  );
};
