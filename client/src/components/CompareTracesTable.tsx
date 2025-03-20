import { TracesTable } from "@/components/TracesTable";
import { spansByGenerationQueryOptions } from "@/utils/spans";
import { useSuspenseQueries } from "@tanstack/react-query";

export const CompareTracesTable = ({
  projectUuid,
  firstGenerationUuid,
  secondGenerationUuid,
}: {
  projectUuid: string;
  firstGenerationUuid: string;
  secondGenerationUuid?: string;
}) => {
  const data = useSuspenseQueries({
    queries: [firstGenerationUuid, secondGenerationUuid]
      .filter((uuid) => uuid !== undefined)
      .map((uuid) => ({
        ...spansByGenerationQueryOptions(projectUuid, uuid),
      })),
  });
  const flattenedData = data.map((result) => result.data).flat();
  return <TracesTable data={flattenedData} />;
};
