import { functionsByNameQueryOptions } from "@/utils/functions";
import { useSuspenseQuery } from "@tanstack/react-query";
import { useParams } from "@tanstack/react-router";

import { NotFound } from "@/components/NotFound";
import { FunctionOverviewUI } from "@/components/functions/FunctionOverviewUI";
import { Route } from "@/routes/_auth/projects/$projectUuid/functions/$functionName/_workbench/$functionUuid.$tab.$.tsx";

export const FunctionOverview = () => {
  const { projectUuid, functionName, functionUuid } = useParams({
    from: Route.id,
  });
  const { data: functions } = useSuspenseQuery(
    functionsByNameQueryOptions(functionName, projectUuid)
  );
  const fn = functions.find((f) => f.uuid === functionUuid);

  if (!fn) {
    return <NotFound />;
  }

  return <FunctionOverviewUI projectUuid={projectUuid} firstFunction={fn} isCompare={false} />;
};
