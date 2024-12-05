import { LLMFunction } from "@/components/LLMFunction";
import { NotFound } from "@/components/NotFound";
import { SelectVersionForm } from "@/components/SelectVerisonForm";
import { versionQueryOptions } from "@/utils/versions";
import { useSuspenseQuery } from "@tanstack/react-query";
import { createFileRoute, useParams } from "@tanstack/react-router";
export const Route = createFileRoute(
  "/_auth/projects/$projectUuid/functions/$functionName/$"
)({
  component: () => {
    const params = useParams({
      from: Route.id,
    });
    const { projectUuid, _splat } = params;
    const versionUuid = _splat?.split("/")[1];
    if (!projectUuid) return <NotFound />;
    const { data: version } = useSuspenseQuery(
      versionQueryOptions(projectUuid, versionUuid)
    );
    return (
      <div className='w-full'>
        <SelectVersionForm versionUuid={versionUuid} />
        <LLMFunction projectUuid={projectUuid} version={version} />
      </div>
    );
  },
});
