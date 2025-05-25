import TableSkeleton from "@/components/TableSkeleton";
import { AnnotationsTable } from "@/ee/components/AnnotationsTable";
import { annotationsByFunctionQueryOptions } from "@/ee/utils/annotations";
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
