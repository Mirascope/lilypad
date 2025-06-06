import { DataTable } from "@/src/components/DataTable";
import { CreateEnvironmentDialog } from "@/src/components/environments/CreateEnvironmentDialog";
import { DeleteEnvironmentDialog } from "@/src/components/environments/DeleteEnvironmentDialog";
import { Typography } from "@/src/components/ui/typography";
import { EnvironmentPublic } from "@/src/types/types";
import { environmentsQueryOptions } from "@/src/utils/environments";
import { formatDate } from "@/src/utils/strings";
import { useSuspenseQuery } from "@tanstack/react-query";
import { ColumnDef } from "@tanstack/react-table";
import { useRef } from "react";

export const EnvironmentsTable = () => {
  const virtualizerRef = useRef<HTMLDivElement>(null);
  const { data } = useSuspenseQuery(environmentsQueryOptions());
  const columns: ColumnDef<EnvironmentPublic>[] = [
    {
      accessorKey: "name",
      header: "Name",
    },
    {
      accessorKey: "description",
      header: "Description",
    },
    {
      accessorKey: "created_at",
      header: "Created",
      cell: ({ row }) => {
        return <div>{formatDate(row.getValue("created_at"))}</div>;
      },
    },
    {
      id: "actions",
      enableHiding: false,
      cell: ({ row }) => {
        return <DeleteEnvironmentDialog environment={row.original} />;
      },
    },
  ];

  return (
    <div>
      <div className="flex items-center gap-2">
        <Typography variant="h4">Environment</Typography>
        <CreateEnvironmentDialog />
      </div>
      <DataTable<EnvironmentPublic>
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
