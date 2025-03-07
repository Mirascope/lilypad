import { Typography } from "@/components/ui/typography";
import { Playground } from "@/ee/components/Playground";
import { useIsEnterprise } from "@/hooks/use-isEnterprise";
import { createFileRoute, useParams } from "@tanstack/react-router";

export const Route = createFileRoute(
  "/_auth/projects/$projectUuid/generations/$generationName/_workbench/"
)({
  component: RouteComponent,
});

function RouteComponent() {
  const { projectUuid } = useParams({ from: Route.id });
  const isEnterprise = useIsEnterprise(projectUuid);
  if (!isEnterprise) {
    return (
      <div className='p-4'>
        <Typography variant='h4'>
          Only available for enterprise users
        </Typography>
      </div>
    );
  } else
    return (
      <div className='p-4 flex flex-col gap-4'>
        <Typography variant='h4'>Create New Generation</Typography>
        <Playground version={null} />
      </div>
    );
}
