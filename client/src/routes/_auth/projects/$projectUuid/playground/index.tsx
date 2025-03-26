import { LilypadLoading } from "@/components/LilypadLoading";
import { Typography } from "@/components/ui/typography";
import { VersionedPlayground } from "@/ee/components/VersionedPlayground";
import { useFeatureAccess } from "@/hooks/use-featureaccess";
import { createFileRoute, useParams } from "@tanstack/react-router";
import { Suspense } from "react";

export const Route = createFileRoute(
  "/_auth/projects/$projectUuid/playground/"
)({
  component: () => <NewPlaygroundRoute />,
});

const NewPlaygroundRoute = () => {
  const { projectUuid } = useParams({
    from: Route.id,
  });
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
      <Suspense fallback={<LilypadLoading />}>
        <VersionedPlayground projectUuid={projectUuid} isCompare={false} />
      </Suspense>
    );
};
