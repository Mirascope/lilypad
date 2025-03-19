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
import { labelNodeDefinition } from "@/ee/components/LabelNode";
import { AnnotationPublic, Label } from "@/types/types";
import { renderCardOutput } from "@/utils/panel-utils";
import { usersByOrganizationQueryOptions } from "@/utils/users";
import { useSuspenseQuery } from "@tanstack/react-query";
import { ColumnDef } from "@tanstack/react-table";
import JsonView from "@uiw/react-json-view";
import { JsonData, JsonEditor } from "json-edit-react";
import { MoreHorizontal } from "lucide-react";
import { useRef } from "react";
import ReactMarkdown from "react-markdown";

export const AnnotationsTable = ({ data }: { data: AnnotationPublic[] }) => {
  const virtualizerRef = useRef<HTMLDivElement>(null);
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
  const columns: ColumnDef<AnnotationPublic>[] = [
    {
      header: "Input",
      enableHiding: false,
      cell: ({ row }) => {
        if (!row.original.span.arg_values) return "N/A";
        return (
          <Tooltip>
            <TooltipTrigger asChild>
              <div className='line-clamp-1'>
                {JSON.stringify(row.original.span.arg_values)}
              </div>
            </TooltipTrigger>
            <TooltipContent className='bg-white text-black'>
              {<JsonView value={row.original.span.arg_values} />}
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
                {<ReactMarkdown>{row.original.span.output}</ReactMarkdown>}
              </div>
            </TooltipTrigger>
            <TooltipContent className='bg-white text-black'>
              {renderCardOutput(row.original.span.output)}
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
      accessorKey: "assigned_to",
      header: "Annotated By",
      cell: ({ row }) => {
        const annotatedBy: string = row.getValue("assigned_to");
        return mappedUsers[annotatedBy] || "N/A";
      },
    },
    {
      id: "actions",
      enableHiding: false,
      cell: () => {
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
    <DataTable<AnnotationPublic>
      columns={columns}
      data={data}
      virtualizerRef={virtualizerRef}
      virtualizerOptions={{
        count: data.length,
        estimateSize: () => 45,
        overscan: 20,
      }}
      DetailPanel={AnnotationMoreDetails}
      defaultPanelSize={50}
    />
  );
};

const AnnotationMoreDetails = ({ data }: { data: AnnotationPublic }) => {
  return (
    <>
      <Typography variant='h3'>Data</Typography>
      <JsonEditor
        data={data.data as JsonData}
        restrictDelete={true}
        restrictAdd={true}
        restrictEdit={true}
        customNodeDefinitions={[labelNodeDefinition]}
      />
    </>
  );
};
