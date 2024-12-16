import { CreateEditorForm } from "@/components/CreateEditorForm";
import { GenerationWorkbench } from "@/components/GenerationWorkbench";
import { NotFound } from "@/components/NotFound";
import { SelectVersionForm } from "@/components/SelectVerisonForm";
import { promptQueryOptions } from "@/utils/prompts";
import { useSuspenseQuery } from "@tanstack/react-query";
import { createFileRoute, useParams } from "@tanstack/react-router";
export const Route = createFileRoute(
  "/_auth/projects/$projectUuid/prompts/$promptName/$"
)({
  component: () => {
    const params = useParams({
      from: Route.id,
    });
    const { projectUuid, _splat } = params;
    const promptUuid = _splat?.split("/")[1];
    if (!projectUuid) return <NotFound />;
    const { data: promptVersion } = useSuspenseQuery(
      promptQueryOptions(projectUuid, promptUuid)
    );
    return (
      <div className='w-full'>
        <SelectVersionForm promptUuid={promptUuid} />
        <CreateEditorForm version={promptVersion} />
      </div>
    );
  },
});
