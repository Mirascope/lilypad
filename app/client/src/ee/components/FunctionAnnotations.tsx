import TableSkeleton from "@/src/components/TableSkeleton";
import { AnnotationsTable } from "@/src/ee/components/AnnotationsTable";
import { annotationsByFunctionQueryOptions } from "@/src/ee/utils/annotations";
import { useSuspenseQuery } from "@tanstack/react-query";
import { Suspense } from "react";

export const FunctionAnnotations = ({
  projectUuid,
  functionUuid,
}: {
  projectUuid: string;
  functionUuid: string;
}) => {
  const { data } = useSuspenseQuery(annotationsByFunctionQueryOptions(projectUuid, functionUuid));
  return (
    <Suspense fallback={<TableSkeleton />}>
      <AnnotationsTable data={data} />
    </Suspense>
  );
};
