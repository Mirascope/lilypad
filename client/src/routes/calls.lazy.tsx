import { CallPublicWithPromptVersion } from "@/types/types";
import { useQuery } from "@tanstack/react-query";
import { createLazyFileRoute } from "@tanstack/react-router";

import { DataTableDemo } from "./-callsTable";

export const Route = createLazyFileRoute("/calls")({
  component: () => <Call />,
});

export const Call = () => {
  const { isPending, error, data } = useQuery<CallPublicWithPromptVersion[]>({
    queryKey: ["calls"],
    queryFn: async () => {
      const response = await fetch("http://localhost:8000/api/calls");
      return await response.json();
    },
    refetchInterval: 1000,
  });
  if (isPending) return <div>Loading...</div>;
  if (error) return <div>An error occurred: {error.message}</div>;
  console.log(data);
  return <DataTableDemo data={data} />;
};
