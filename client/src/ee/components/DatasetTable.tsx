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
import { Typography } from "@/components/ui/typography";
import { DatasetRow } from "@/ee/types/types";
import { getDatasetByGenerationUuidQueryOptions } from "@/ee/utils/datasets";
import { Label } from "@/types/types";
import { renderCardOutput } from "@/utils/panel-utils";
import { usersByOrganizationQueryOptions } from "@/utils/users";
import { useSuspenseQuery } from "@tanstack/react-query";
import { ColumnDef } from "@tanstack/react-table";
import JsonView from "@uiw/react-json-view";
import { JsonData, JsonEditor } from "json-edit-react";
import { MoreHorizontal } from "lucide-react";
import { useRef } from "react";
import ReactMarkdown from "react-markdown";

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
  const { data: usersInOrg } = useSuspenseQuery(
    usersByOrganizationQueryOptions()
  );
  const mappedUsers: { [key: string]: string } = usersInOrg.reduce(
    (acc, user) => ({
      ...acc,
      [user.uuid]: user.first_name,
    }),
    {}
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
              <div className='line-clamp-1'>
                {JSON.stringify(row.original.input)}
              </div>
            </TooltipTrigger>
            <TooltipContent className='bg-white text-black'>
              {<JsonView value={row.original.input} />}
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
              <div className='line-clamp-1'>
                {<ReactMarkdown>{row.getValue("output")}</ReactMarkdown>}
              </div>
            </TooltipTrigger>
            <TooltipContent className='bg-white text-black'>
              {renderCardOutput(row.getValue("output"))}
            </TooltipContent>
          </Tooltip>
        );
      },
    },
    {
      accessorKey: "label",
      header: "Label",
      cell: ({ row }) => {
        const label: string = row.getValue("label") || "";
        return (
          <div
            className={
              row.getValue("label") === Label.PASS
                ? "text-green-600"
                : "text-destructive"
            }
          >
            {label.toUpperCase()}
          </div>
        );
      },
    },
    {
      accessorKey: "annotated_by",
      header: "Annotated By",
      cell: ({ row }) => {
        const annotatedBy: string = row.getValue("annotated_by");
        return mappedUsers[annotatedBy] || "N/A";
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
      DetailPanel={DatasetMoreDetails}
      defaultPanelSize={50}
      customControls={() => (
        <div>
          {passData.length} out of {data.length} passed.
        </div>
      )}
    />
  );
};

const DatasetMoreDetails = ({ data }: { data: DatasetRow }) => {
  return (
    <>
      <Typography variant='h3'>Data</Typography>
      <JsonEditor
        data={data.data as JsonData}
        restrictDelete={true}
        restrictAdd={true}
        restrictEdit={true}
      />
    </>
  );
};
