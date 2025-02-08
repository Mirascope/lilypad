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
import { AnnotationQueueDialog } from "@/ee/components/AnnotationQueueDialog";
import { AnnotationPublic } from "@/ee/types/types";
import { useUploadDatasetMutation } from "@/ee/utils/datasets";
import { useToast } from "@/hooks/use-toast";
import { Label } from "@/types/types";
import { renderCardOutput } from "@/utils/panel-utils";
import { ColumnDef } from "@tanstack/react-table";
import JsonView from "@uiw/react-json-view";
import { MoreHorizontal } from "lucide-react";
import { useRef } from "react";
import ReactMarkdown from "react-markdown";

export const AnnotationsTable = ({
  projectUuid,
  generationUuid,
  data,
}: {
  projectUuid: string;
  generationUuid: string;
  data: AnnotationPublic[];
}) => {
  const virtualizerRef = useRef<HTMLDivElement>(null);
  const uploadDataset = useUploadDatasetMutation();
  const { toast } = useToast();
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

  const renderCustomControls = () => {
    const unannotatedRows = data.filter((annotation) => !annotation.label);
    const annotatedRows = data.filter((annotation) => annotation.label);
    const onClick = async () => {
      await uploadDataset.mutateAsync({
        projectUuid,
        generationUuid,
        annotations: annotatedRows,
      });
      toast({
        title: "Annotations added to dataset",
      });
    };
    return (
      <>
        <AnnotationQueueDialog unannotatedRows={unannotatedRows} />
        <IconDialog
          text={"Add to Dataset"}
          title={"Annotate selected traces"}
          description={`${annotatedRows.length} annotation(s) will be added.`}
          tooltipContent={"Add labeled annotations to your dataset."}
          buttonProps={{ disabled: annotatedRows.length === 0 }}
          dialogButtons={[
            <Button variant='default' onClick={onClick}>
              Add
            </Button>,
          ]}
        />
      </>
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
      customControls={renderCustomControls}
    />
  );
};
