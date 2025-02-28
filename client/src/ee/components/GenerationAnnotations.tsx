import TableSkeleton from "@/components/TableSkeleton";
import { AnnotationsTable } from "@/ee/components/AnnotationsTable";
import { annotationsByGenerationQueryOptions } from "@/ee/utils/annotations";
import { useSuspenseQuery } from "@tanstack/react-query";
import { Suspense } from "react";

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
    <Suspense fallback={<TableSkeleton />}>
      <AnnotationsTable data={data} />
    </Suspense>
  );
};
