import { createLazyFileRoute } from "@tanstack/react-router";
import { Combobox } from "@/components/ui/combobox";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { DiffTool } from "@/routes/-diffTool";
import { Typography } from "@/components/ui/typography";
export const Route = createLazyFileRoute("/diff")({
  component: () => <Comparison />,
});

const Comparison = () => {
  const [value, setValue] = useState("");
  const {
    isPending,
    error,
    data: function_names,
  } = useQuery<string[]>({
    queryKey: ["function_names"],
    queryFn: async () => {
      const response = await fetch("http://localhost:8000/api/prompt-versions");
      return await response.json();
    },
  });

  if (isPending) return <div>Loading...</div>;
  if (error) return <div>An error occurred: {error.message}</div>;

  return (
    <div className='p-2 flex flex-col gap-2'>
      <Typography variant='h3'>Diff Tool</Typography>
      <Combobox
        items={function_names.map((item) => ({ value: item, label: item }))}
        value={value}
        setValue={setValue}
      />
      {value && <DiffTool value={value} />}
    </div>
  );
};
