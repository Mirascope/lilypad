import { TracesTable } from "@/components/TracesTable";
import { spansByFunctionQueryOptions } from "@/utils/spans";
import { useSuspenseQuery } from "@tanstack/react-query";

export const FunctionSpans = ({
  projectUuid,
  functionUuid,
}: {
  projectUuid: string;
  functionUuid?: string;
}) => {
  if (!functionUuid) {
    return <div>No function selected.</div>;
  }
  const { data } = useSuspenseQuery(
    spansByFunctionQueryOptions(projectUuid, functionUuid)
  );
  return <TracesTable data={data} />;
};
