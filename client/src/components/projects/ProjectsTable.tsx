import { DataTable } from "@/components/DataTable";
import {
  CreateProjectDialog,
  DeleteProjectDialog,
  EditProjectDialog,
} from "@/components/projects/ProjectDialog";
import { Button } from "@/components/ui/button";
import { Typography } from "@/components/ui/typography";
import { ProjectPublic } from "@/types/types";
import { projectsQueryOptions } from "@/utils/projects";
import { formatDate } from "@/utils/strings";
import { useSuspenseQuery } from "@tanstack/react-query";
import { ColumnDef } from "@tanstack/react-table";
import { Copy } from "lucide-react";
import { useRef } from "react";
import { toast } from "sonner";

export const ProjectsTable = () => {
  const virtualizerRef = useRef<HTMLDivElement>(null);
  const { data } = useSuspenseQuery(projectsQueryOptions());
  const handleProjectCopy = (project: ProjectPublic) => {
    navigator.clipboard.writeText(project.uuid);
    toast.success(`Successfully copied Project ID to clipboard for project ${project.name}`);
  };
  const columns: ColumnDef<ProjectPublic>[] = [
    {
      accessorKey: "name",
      header: "Name",
    },
    {
      accessorKey: "created_at",
      header: "Created",
      cell: ({ row }) => {
        return <div>{formatDate(row.getValue("created_at"))}</div>;
      },
      minSize: 250,
    },
    {
      id: "actions",
      enableHiding: false,
      cell: ({ row }) => {
        return (
          <div className="flex gap-1">
            <Button
              variant="outline"
              size="icon"
              className="h-8 w-8"
              onClick={() => handleProjectCopy(row.original)}
            >
              <Copy />
            </Button>
            <EditProjectDialog
              projectUuid={row.original.uuid}
              defaultProjectFormData={{ name: row.original.name }}
            />
            <DeleteProjectDialog project={row.original} />
          </div>
        );
      },
    },
  ];
  return (
    <div>
      <div className="flex items-center gap-2">
        <Typography variant="h4">Projects</Typography>
        <CreateProjectDialog />
      </div>
      <DataTable<ProjectPublic>
        columns={columns}
        data={data}
        virtualizerRef={virtualizerRef}
        virtualizerOptions={{
          count: data.length,
          estimateSize: () => 45,
          overscan: 5,
        }}
        hideColumnButton
      />
    </div>
  );
};
