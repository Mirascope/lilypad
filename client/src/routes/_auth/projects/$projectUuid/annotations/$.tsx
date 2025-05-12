import CardSkeleton from "@/components/CardSkeleton";
import { LilypadLoading } from "@/components/LilypadLoading";
import { FunctionTitle } from "@/components/traces/FunctionTitle";
import { LilypadPanel } from "@/components/traces/LilypadPanel";
import { SpanMetrics } from "@/components/traces/SpanMetrics";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  ResizableHandle,
  ResizablePanel,
  ResizablePanelGroup,
} from "@/components/ui/resizable";
import { Typography } from "@/components/ui/typography";
import {
  annotationsByProjectQueryOptions,
  useDeleteAnnotationMutation,
} from "@/ee/utils/annotations";
import { cn } from "@/lib/utils";
import { AnnotationPublic, FunctionPublic, UserPublic } from "@/types/types";
import { functionsQueryOptions } from "@/utils/functions";
import { SpanComments } from "@/utils/panel-utils";
import { formatRelativeTime } from "@/utils/strings";
import { usersByOrganizationQueryOptions } from "@/utils/users";
import { useSuspenseQuery } from "@tanstack/react-query";
import {
  createFileRoute,
  useNavigate,
  useParams,
} from "@tanstack/react-router";
import { Trash } from "lucide-react";
import { Dispatch, SetStateAction, Suspense, useEffect, useState } from "react";
import { toast } from "sonner";

export const Route = createFileRoute(
  "/_auth/projects/$projectUuid/annotations/$"
)({
  component: () => {
    return (
      <Suspense fallback={<LilypadLoading />}>
        <AnnotationLayout />
      </Suspense>
    );
  },
});

const AnnotationLayout = () => {
  const { projectUuid, _splat: annotationUuid } = useParams({ from: Route.id });
  const { data: annotations } = useSuspenseQuery(
    annotationsByProjectQueryOptions(projectUuid)
  );
  const navigate = useNavigate();
  const deleteAnnotation = useDeleteAnnotationMutation();
  const [activeAnnotation, setActiveAnnotation] =
    useState<AnnotationPublic | null>(annotations[0] || null);
  const span = activeAnnotation?.span;
  useEffect(() => {
    const annotation = annotations.find(
      (annotation) => annotation.uuid === annotationUuid
    );
    if (annotationUuid === "next") {
      if (annotations.length == 0) {
        setActiveAnnotation(null);
        navigate({
          to: Route.fullPath,
          replace: true,
          params: { projectUuid, _splat: undefined },
        }).catch(() => {
          toast.error("Failed to navigate");
        });
        return;
      }
      setActiveAnnotation(annotations[0]);
    } else if (annotation) {
      setActiveAnnotation(annotation);
    } else {
      setActiveAnnotation(null);
    }
  }, [annotations, annotationUuid]);
  if (!span) {
    return (
      <div className="flex flex-col h-full p-4">
        <div className="shrink-0">
          <Typography variant="h3">No Annotation Selected</Typography>
        </div>
        <AnnotationList
          activeAnnotation={activeAnnotation}
          setActiveAnnotation={setActiveAnnotation}
        />
      </div>
    );
  }
  // TODO: Annotation needs refresh button
  return (
    <div className="container h-screen w-full p-2 max-w-screen-2xl overflow-hidden">
      <ResizablePanelGroup direction="horizontal" className="h-full">
        <ResizablePanel
          defaultSize={25}
          minSize={15}
          className="flex flex-col gap-1"
        >
          <Typography variant="h3" className="truncate max-w-md shrink-0">
            Annotation Queue
          </Typography>
          <div className="overflow-y-auto flex-1 min-h-0">
            <Suspense fallback={<LilypadLoading />}>
              <AnnotationList
                activeAnnotation={activeAnnotation}
                setActiveAnnotation={setActiveAnnotation}
              />
            </Suspense>
          </div>
        </ResizablePanel>

        <ResizableHandle withHandle className="m-4" />

        <ResizablePanel
          defaultSize={75}
          minSize={50}
          className="flex flex-col h-full"
        >
          <div className="flex justify-between items-center mb-4 shrink-0">
            <FunctionTitle span={span} />
            {annotationUuid && (
              <Button
                type="button"
                loading={deleteAnnotation.isPending}
                variant="outlineDestructive"
                onClick={() => {
                  deleteAnnotation
                    .mutateAsync({
                      projectUuid,
                      annotationUuid,
                    })
                    .catch(() => toast.error("Failed to delete annotation"));
                  toast.success("Annotation deleted");
                }}
              >
                <Trash className="size-4" />
                {deleteAnnotation.isPending
                  ? "Removing..."
                  : "Remove Annotation"}
              </Button>
            )}
          </div>

          <ResizablePanelGroup
            direction="horizontal"
            className="flex-1 min-h-0 h-full overflow-hidden"
          >
            <ResizablePanel
              defaultSize={65}
              minSize={40}
              className="overflow-hidden"
            >
              <div className="h-full overflow-y-auto">
                <LilypadPanel spanUuid={span.uuid} showMetrics={false} />
              </div>
            </ResizablePanel>

            <ResizableHandle withHandle className="m-4" />

            <ResizablePanel
              defaultSize={35}
              minSize={25}
              className="flex flex-col overflow-hidden h-full gap-4"
            >
              <div className="shrink-0">
                <SpanMetrics span={span} />
              </div>
              <div className="flex-1 min-h-0">
                <Suspense fallback={<CardSkeleton items={1} />}>
                  <SpanComments
                    projectUuid={projectUuid}
                    spanUuid={span.uuid}
                    activeAnnotation={activeAnnotation}
                    path={Route.fullPath}
                  />
                </Suspense>
              </div>
            </ResizablePanel>
          </ResizablePanelGroup>
        </ResizablePanel>
      </ResizablePanelGroup>
    </div>
  );
};

const AnnotationList = ({
  activeAnnotation,
  setActiveAnnotation,
}: {
  activeAnnotation: AnnotationPublic | null;
  setActiveAnnotation: Dispatch<SetStateAction<AnnotationPublic | null>>;
}) => {
  const { projectUuid, _splat: annotationUuid } = useParams({
    from: Route.id,
  });
  const navigate = useNavigate();
  const { data: annotations, dataUpdatedAt } = useSuspenseQuery(
    annotationsByProjectQueryOptions(projectUuid)
  );

  const { data: users } = useSuspenseQuery(usersByOrganizationQueryOptions());
  const { data: functions } = useSuspenseQuery(
    functionsQueryOptions(projectUuid)
  );
  const functionsMap = functions.reduce(
    (acc, fn) => {
      acc[fn.uuid] = fn;
      return acc;
    },
    {} as Record<string, FunctionPublic>
  );
  const usersMap = users.reduce(
    (acc, user) => {
      acc[user.uuid] = user;
      return acc;
    },
    {} as Record<string, UserPublic>
  );
  return (
    <div className="flex flex-col h-full gap-2">
      <Typography
        variant="span"
        affects="muted"
      >{`Last updated: ${formatRelativeTime(new Date(dataUpdatedAt))}`}</Typography>
      <Typography affects="muted" variant="span">
        {annotations.length > 0 && `${annotations.length} item(s) remaining`}
      </Typography>
      <div className="flex flex-col gap-2 overflow-auto">
        {annotations.map((annotation) => {
          const fn = annotation.function_uuid
            ? functionsMap[annotation.function_uuid]
            : null;
          return (
            <div
              key={annotation.uuid}
              className={cn(
                "flex items-center py-2 px-1 rounded-md transition-colors hover:bg-accent/50 cursor-pointer",
                annotationUuid === annotation.uuid && "bg-accent font-medium"
              )}
              onClick={() => {
                if (activeAnnotation?.uuid === annotation.uuid) {
                  setActiveAnnotation(null);
                  navigate({
                    to: Route.fullPath,
                    replace: true,
                    params: { projectUuid, _splat: undefined },
                  }).catch(() => {
                    toast.error("Failed to navigate");
                  });
                } else {
                  setActiveAnnotation(annotation);
                }
              }}
            >
              <div className="flex flex-col min-w-0 w-full">
                <div className="flex items-center gap-2 w-full">
                  <span className="truncate font-medium max-w-full">
                    {annotation.span.display_name}
                  </span>
                  {fn && (
                    <Typography
                      variant="span"
                      className="text-xs whitespace-nowrap shrink-0"
                    >
                      v{fn.version_num}
                    </Typography>
                  )}
                  <Badge variant="neutral" size="sm" className="shrink-0">
                    {formatRelativeTime(annotation.created_at, true)}
                  </Badge>
                  {annotation.assigned_to && (
                    <Badge variant="neutral" size="sm" className="shrink-0">
                      {usersMap[annotation.assigned_to].first_name}
                    </Badge>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
