import { TracesTable } from "@/components/TracesTable";
import { Route } from "@/routes/_auth/projects/$projectUuid/functions/$functionName/_workbench/$functionUuid.$tab.$.tsx";
import { spansByFunctionQueryOptions } from "@/utils/spans";
import { useSuspenseQuery } from "@tanstack/react-query";
export const FunctionSpans = ({
  projectUuid,
  functionUuid,
  traceUuid,
}: {
  projectUuid: string;
  functionUuid: string;
  traceUuid?: string;
}) => {
  const { data } = useSuspenseQuery(
    spansByFunctionQueryOptions(projectUuid, functionUuid)
  );
  return (
    <TracesTable data={data} traceUuid={traceUuid} path={Route.fullPath} />
  );
};
