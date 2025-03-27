import { TracesTable } from "@/components/TracesTable";
import { spansByFunctionQueryOptions } from "@/utils/spans";
import { useSuspenseQueries } from "@tanstack/react-query";

export const CompareTracesTable = ({
  projectUuid,
  firstFunctionUuid,
  secondFunctionUuid,
}: {
  projectUuid: string;
  firstFunctionUuid: string;
  secondFunctionUuid?: string;
}) => {
  const data = useSuspenseQueries({
    queries: [firstFunctionUuid, secondFunctionUuid]
      .filter((uuid) => uuid !== undefined)
      .map((uuid) => ({
        ...spansByFunctionQueryOptions(projectUuid, uuid),
      })),
  });
  const flattenedData = data.map((result) => result.data).flat();
  return <TracesTable data={flattenedData} />;
};
