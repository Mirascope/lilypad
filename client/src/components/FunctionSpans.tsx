import { TracesTable } from "@/components/TracesTable";
import { versionIdSpansQueryOptions } from "@/utils/spans";
import { useSuspenseQuery } from "@tanstack/react-query";
import { useParams } from "@tanstack/react-router";

export const FunctionSpans = () => {
  const { projectId, versionId } = useParams({
    from: "/projects/$projectId/functions/$functionName/versions/$versionId",
  });
  const { data } = useSuspenseQuery(
    versionIdSpansQueryOptions(Number(projectId), Number(versionId))
  );
  return <TracesTable data={data} />;
};
