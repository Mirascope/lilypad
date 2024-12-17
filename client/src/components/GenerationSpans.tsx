import { NotFound } from "@/components/NotFound";
import { TracesTable } from "@/components/TracesTable";
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
    return <NotFound />;
  }
  const { data } = useSuspenseQuery(
    spansByGenerationQueryOptions(projectUuid, generationUuid)
  );
  console.log(data);
  return <TracesTable data={data} />;
};
