import { AnnotationsTable } from "@/ee/components/AnnotationsTable";
import { annotationsByGenerationQueryOptions } from "@/ee/utils/annotations";
import { useSuspenseQuery } from "@tanstack/react-query";

export const GenerationAnnotations = ({
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
    annotationsByGenerationQueryOptions(projectUuid, generationUuid)
  );
  return (
    <AnnotationsTable
      data={data}
      projectUuid={projectUuid}
      generationUuid={generationUuid}
    />
  );
};
