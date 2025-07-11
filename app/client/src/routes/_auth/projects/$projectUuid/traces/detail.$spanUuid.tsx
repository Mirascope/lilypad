import { createFileRoute, useNavigate, useParams } from "@tanstack/react-router";
import { Suspense } from "react";
import { toast } from "sonner";
import { z } from "zod";

import { LilypadLoading } from "@/src/components/LilypadLoading";
import { SpanFullDetail } from "@/src/components/traces/SpanFullDetail";

export const Route = createFileRoute("/_auth/projects/$projectUuid/traces/detail/$spanUuid")({
  parseParams: (params) => ({
    projectUuid: z.string().parse(params.projectUuid),
    spanUuid: z.string().parse(params.spanUuid),
  }),
  component: () => <SpanDetailPage />,
});

export const SpanDetailPage = () => {
  const navigate = useNavigate();
  const { projectUuid, spanUuid } = useParams({ from: Route.id });
  const handleBackToTraces = () => {
    navigate({
      to: "/projects/$projectUuid/traces/$",
      params: { projectUuid, _splat: spanUuid },
    }).catch(() => toast.error("Failed to navigate"));
  };
  return (
    <Suspense fallback={<LilypadLoading />}>
      <SpanFullDetail
        handleBackToTraces={handleBackToTraces}
        projectUuid={projectUuid}
        spanUuid={spanUuid}
      />
    </Suspense>
  );
};
