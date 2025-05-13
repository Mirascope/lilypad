import { CreateAPIKeyDialog } from "@/components/apiKeys/CreateAPIKeyDialog";
import { DeleteAPIKeyDialog } from "@/components/apiKeys/DeleteAPIKeyDialog";
import { DataTable } from "@/components/DataTable";
import { Typography } from "@/components/ui/typography";
import { APIKeyPublic } from "@/types/types";
import { apiKeysQueryOptions } from "@/utils/api-keys";
import { formatDate } from "@/utils/strings";
import { useSuspenseQuery } from "@tanstack/react-query";
import { ColumnDef } from "@tanstack/react-table";
import { useRef } from "react";

export const APIKeysTable = () => {
  const virtualizerRef = useRef<HTMLDivElement>(null);
  const { data } = useSuspenseQuery(apiKeysQueryOptions());
  const columns: ColumnDef<APIKeyPublic>[] = [
    {
      accessorKey: "name",
      header: "Name",
    },
    {
      accessorKey: "user.first_name",
      header: "Created By",
    },
    {
      accessorKey: "project.name",
      header: "Project",
    },
    {
      accessorKey: "environment.name",
      header: "Environment",
    },
    {
      accessorKey: "prefix",
      header: "Key",
      cell: ({ row }) => <div>{row.getValue("prefix")}...</div>,
    },
    {
      accessorKey: "expires_at",
      header: "Expires",
      cell: ({ row }) => {
        return <div>{formatDate(row.getValue("expires_at"))}</div>;
      },
    },
    {
      id: "actions",
      enableHiding: false,
      cell: ({ row }) => {
        return <DeleteAPIKeyDialog apiKey={row.original} />;
      },
    },
  ];
  return (
    <div>
      <div className="flex gap-2 items-center">
        <Typography variant="h4">API Keys</Typography>
        <CreateAPIKeyDialog />
      </div>
      <DataTable<APIKeyPublic>
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
