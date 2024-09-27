import { SpanPublic } from "@/types/types";
import { useQuery } from "@tanstack/react-query";
import { createLazyFileRoute } from "@tanstack/react-router";

import { DataTableDemo } from "./-callsTable";

export const Route = createLazyFileRoute("/traces")({
  component: () => <Trace />,
});

export const Trace = () => {
  const { isPending, error, data } = useQuery<SpanPublic[]>({
    queryKey: ["traces"],
    queryFn: async () => {
      const response = await fetch("http://localhost:8000/api/traces");
      return await response.json();
    },
    refetchInterval: 1000,
  });
  if (isPending) return <div>Loading...</div>;
  if (error) return <div>An error occurred: {error.message}</div>;
  console.log(data);
  return (
    <div className='h-screen p-2'>
      <DataTableDemo data={data} />
    </div>
  );
};
