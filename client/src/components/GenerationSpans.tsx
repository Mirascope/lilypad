import { TracesTable } from "@/components/TracesTable";
import { useIsEnterprise } from "@/hooks/use-isEnterprise";
import { spansByGenerationQueryOptions } from "@/utils/spans";
import { useSuspenseQuery } from "@tanstack/react-query";

export const GenerationSpans = ({
  projectUuid,
  generationUuid,
}: {
  projectUuid: string;
  generationUuid?: string;
}) => {
  if (!generationUuid) {
    return <div>No generation selected.</div>;
  }
  const { data } = useSuspenseQuery(
    spansByGenerationQueryOptions(projectUuid, generationUuid)
  );
  const isEnterprise = useIsEnterprise(projectUuid);
  return <TracesTable data={data} isEnterprise={isEnterprise} />;
};
