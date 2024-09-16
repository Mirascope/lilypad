import { useQuery } from '@tanstack/react-query';
import { createLazyFileRoute } from '@tanstack/react-router';

import { DataTableDemo } from './-callsTable';

export const Route = createLazyFileRoute("/calls")({
  component: () => <Call />,
});

export const Call = () => {
  const { isPending, error, data, isFetching } = useQuery({
    queryKey: ["calls"],
    queryFn: async () => {
      const response = await fetch("http://localhost:3000/api/calls");
      return await response.json();
    },
  });
  console.log(data);
  return <DataTableDemo data={data} />;
};
