import { NotFound } from "@/components/NotFound";
import { Playground } from "@/components/Playground";
import { SelectVersionForm } from "@/components/SelectVerisonForm";
import { promptQueryOptions } from "@/utils/prompts";
import { useSuspenseQuery } from "@tanstack/react-query";
import { createFileRoute, useParams } from "@tanstack/react-router";
import { Suspense } from "react";
export const Route = createFileRoute(
  "/_auth/projects/$projectUuid/prompts/$promptName/$"
)({
  component: () => {
    return (
      <Suspense fallback={<div>Loading...</div>}>
        <Prompt />
      </Suspense>
    );
  },
});

const Prompt = () => {
  const params = useParams({
    from: Route.id,
  });
  const { projectUuid, _splat } = params;
  if (!projectUuid) return <NotFound />;
  const promptUuid = _splat?.split("/")[1];
  const { data: promptVersion } = useSuspenseQuery(
    promptQueryOptions(projectUuid, promptUuid)
  );
  return (
    <div className='w-full'>
      <Suspense fallback={<div>Loading...</div>}>
        <SelectVersionForm promptUuid={promptUuid} />
        <Playground version={promptVersion} />
      </Suspense>
    </div>
  );
};
