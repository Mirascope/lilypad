import { Typography } from "@/components/ui/typography";
import { Playground } from "@/ee/components/Playground";
import { useFeatureAccess } from "@/hooks/use-featureaccess";
import { createFileRoute } from "@tanstack/react-router";

export const Route = createFileRoute(
  "/_auth/projects/$projectUuid/generations/$generationName/_workbench/"
)({
  component: RouteComponent,
});

function RouteComponent() {
  const features = useFeatureAccess();
  if (!features.playground) {
    return (
      <div className='p-4'>
        <Typography variant='h4'>
          Not available for your current plan. Please upgrade to use this
          feature.
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
