import { NotFound } from "@/components/NotFound";
import { TracesTable } from "@/components/TracesTable";
import { versionIdSpansQueryOptions } from "@/utils/spans";
import { useSuspenseQuery } from "@tanstack/react-query";

export const FunctionSpans = ({
  projectId,
  versionId,
}: {
  projectId: number;
  versionId?: number;
}) => {
  if (!versionId) {
    return <NotFound />;
  }
  const { data } = useSuspenseQuery(
    versionIdSpansQueryOptions(Number(projectId), versionId)
  );
  return <TracesTable data={data} />;
};
