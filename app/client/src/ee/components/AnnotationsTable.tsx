import { DataTable } from "@/src/components/DataTable";
import { Button } from "@/src/components/ui/button";
import { AnnotationPublic, Label } from "@/src/types/types";
import { usersByOrganizationQueryOptions } from "@/src/utils/users";
import { useSuspenseQuery } from "@tanstack/react-query";
import { ColumnDef } from "@tanstack/react-table";
import { NotebookPen } from "lucide-react";
import { useRef, useState } from "react";

export const AnnotationsTable = ({ data }: { data: AnnotationPublic[] }) => {
  const virtualizerRef = useRef<HTMLDivElement>(null);
  const { data: usersInOrg } = useSuspenseQuery(usersByOrganizationQueryOptions());
  const mappedUsers: Record<string, string> = usersInOrg.reduce(
    (acc, user) => ({
      ...acc,
      [user.uuid]: user.first_name,
    }),
    {}
  );
  const columns: ColumnDef<AnnotationPublic>[] = [
    // {
    //   header: "Input",
    //   enableHiding: false,
    //   cell: ({ row }) => {
    //     if (!row.original.span.arg_values) return "N/A";
    //     return (
    //       <Tooltip>
    //         <TooltipTrigger asChild>
    //           <div className='line-clamp-1'>
    //             {JSON.stringify(row.original.span.arg_values)}
    //           </div>
    //         </TooltipTrigger>
    //         <TooltipContent className='bg-background text-black'>
    //           {<JsonView value={row.original.span.arg_values} />}
    //         </TooltipContent>
    //       </Tooltip>
    //     );
    //   },
    // },
    // {
    //   accessorKey: "output",
    //   header: "Output",
    //   cell: ({ row }) => {
    //     return (
    //       <Tooltip>
    //         <TooltipTrigger asChild>
    //           <div className='line-clamp-1'>
    //             {<ReactMarkdown>{row.original.span.output}</ReactMarkdown>}
    //           </div>
    //         </TooltipTrigger>
    //         <TooltipContent className='bg-background text-black'>
    //           {renderCardOutput(row.original.span.output)}
    //         </TooltipContent>
    //       </Tooltip>
    //     );
    //   },
    // },
    {
      accessorKey: "assigned_to",
      header: "Annotated By",
      cell: ({ row }) => {
        const annotatedBy: string = row.getValue("assigned_to");
        return mappedUsers[annotatedBy] || "N/A";
      },
    },
    {
      accessorKey: "label",
      header: "Label",
      cell: ({ row }) => {
        const label: string = row.getValue("label") || "";
        return (
          <div
            className={row.getValue("label") === Label.PASS ? "text-green-600" : "text-destructive"}
          >
            {label.toUpperCase()}
          </div>
        );
      },
    },
    {
      accessorKey: "reasoning",
      header: "Reasoning",
      cell: ({ row }) => {
        const reasoning: string = row.getValue("reasoning") || "";
        return <div>{reasoning}</div>;
      },
    },
    // {
    //   id: "actions",
    //   enableHiding: false,
    //   cell: () => {
    //     return (
    //       <DropdownMenu>
    //         <DropdownMenuTrigger asChild>
    //           <Button variant='ghost' className='h-8 w-8 p-0'>
    //             <span className='sr-only'>Open menu</span>
    //             <MoreHorizontal className='h-4 w-4' />
    //           </Button>
    //         </DropdownMenuTrigger>
    //         <DropdownMenuContent align='end'>
    //           <DropdownMenuLabel>Actions</DropdownMenuLabel>
    //           <DropdownMenuSeparator />
    //           <DropdownMenuItem>View more details</DropdownMenuItem>
    //         </DropdownMenuContent>
    //       </DropdownMenu>
    //     );
    //   },
    // },
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
      hideColumnButton
    />
  );
};

// const AnnotationMoreDetails = ({ data }: { data: AnnotationPublic }) => {
//   return (
//     <>
//       <Typography variant='h3'>Data</Typography>
//       <JsonEditor
//         data={data.data as JsonData}
//         restrictDelete={true}
//         restrictAdd={true}
//         restrictEdit={true}
//         customNodeDefinitions={[labelNodeDefinition]}
//       />
//     </>
//   );
// };

export const AnnotationsButton = ({ annotations }: { annotations: AnnotationPublic[] }) => {
  const [showAnnotations, setShowAnnotations] = useState<boolean>(false);
  return (
    <div className={`flex flex-col ${showAnnotations ? "h-full" : ""}`}>
      <div className="shrink-0">
        <Button
          size="icon"
          className="relative h-8 w-8"
          variant="outline"
          onClick={() => setShowAnnotations(!showAnnotations)}
        >
          <NotebookPen />
          {annotations.length > 0 && (
            <div className="absolute -top-2 -right-2 flex h-5 w-5 items-center justify-center rounded-full bg-primary text-xs font-medium text-primary-foreground">
              {annotations.length > 9 ? "9+" : annotations.length}
            </div>
          )}
        </Button>
      </div>
      {showAnnotations && <AnnotationsTable data={annotations} />}
    </div>
  );
};
