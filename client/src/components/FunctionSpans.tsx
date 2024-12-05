import { NotFound } from "@/components/NotFound";
import { TracesTable } from "@/components/TracesTable";
import { versionUuidSpansQueryOptions } from "@/utils/spans";
import { useSuspenseQuery } from "@tanstack/react-query";

export const FunctionSpans = ({
  projectUuid,
  versionUuid,
}: {
  projectUuid: string;
  versionUuid?: string;
}) => {
  if (!versionUuid) {
    return <NotFound />;
  }
  const { data } = useSuspenseQuery(
    versionUuidSpansQueryOptions(projectUuid, versionUuid)
  );
  return <TracesTable data={data} />;
};
