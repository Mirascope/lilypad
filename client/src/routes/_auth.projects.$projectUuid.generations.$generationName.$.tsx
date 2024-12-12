import { GenerationWorkbench } from "@/components/GenerationWorkbench";
import { NotFound } from "@/components/NotFound";
import { SelectVersionForm } from "@/components/SelectVerisonForm";
import { generationQueryOptions } from "@/utils/generations";
import { useSuspenseQuery } from "@tanstack/react-query";
import { createFileRoute, useParams } from "@tanstack/react-router";
export const Route = createFileRoute(
  "/_auth/projects/$projectUuid/generations/$generationName/$"
)({
  component: () => {
    const params = useParams({
      from: Route.id,
    });
    const { projectUuid, _splat } = params;
    const generationUuid = _splat?.split("/")[1];
    if (!projectUuid) return <NotFound />;
    const { data: version } = useSuspenseQuery(
      generationQueryOptions(projectUuid, generationUuid)
    );
    return (
      <div className='w-full'>
        <SelectVersionForm versionUuid={generationUuid} />
        <GenerationWorkbench
          projectUuid={projectUuid}
          generationVersion={version}
        />
      </div>
    );
  },
});
