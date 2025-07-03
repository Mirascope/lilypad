import CardSkeleton from "@/src/components/CardSkeleton";
import { LilypadLoading } from "@/src/components/LilypadLoading";
import { FunctionTitle } from "@/src/components/traces/FunctionTitle";
import { LilypadPanel } from "@/src/components/traces/LilypadPanel";
import { SpanMetrics } from "@/src/components/traces/SpanMetrics";
import { Badge } from "@/src/components/ui/badge";
import { Button } from "@/src/components/ui/button";
import {
  ResizableHandle,
  ResizablePanel,
  ResizablePanelGroup,
} from "@/src/components/ui/resizable";
import { Separator } from "@/src/components/ui/separator";
import { Typography } from "@/src/components/ui/typography";
import { AnnotationView } from "@/src/ee/components/annotations/AnnotationView";
import {
  annotationsByProjectQueryOptions,
  useDeleteAnnotationMutation,
} from "@/src/ee/utils/annotations";
import { cn } from "@/src/lib/utils";
import { AnnotationPublic, FunctionPublic, UserPublic } from "@/src/types/types";
import { functionsQueryOptions } from "@/src/utils/functions";
import { SpanComments } from "@/src/utils/panel-utils";
import { formatRelativeTime } from "@/src/utils/strings";
import { usersByOrganizationQueryOptions } from "@/src/utils/users";
import { useSuspenseQuery } from "@tanstack/react-query";
import { createFileRoute, useNavigate, useParams } from "@tanstack/react-router";
import { RefreshCcw, Trash } from "lucide-react";
import { Dispatch, SetStateAction, Suspense, useEffect, useState } from "react";
import { toast } from "sonner";

export const Route = createFileRoute("/_auth/projects/$projectUuid/annotations/$")({
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
  const { data: annotations } = useSuspenseQuery(annotationsByProjectQueryOptions(projectUuid));
  console.log("Annotations:", annotations);
  const navigate = useNavigate();
  const [activeAnnotation, setActiveAnnotation] = useState<AnnotationPublic | null>(
    annotations[0] || null
  );
  const span = activeAnnotation?.span;
  useEffect(() => {
    const annotation = annotations.find((annotation) => annotation.uuid === annotationUuid);
    if (annotationUuid === "next") {
      if (annotations.length == 0) {
        setActiveAnnotation(null);
        navigate({
          to: Route.fullPath,
          replace: true,
          params: { projectUuid, _splat: "" },
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

  useEffect(() => {
    navigate({
      to: Route.fullPath,
      replace: true,
      params: { projectUuid, _splat: activeAnnotation?.uuid ?? "" },
    }).catch(() => {
      toast.error("Failed to navigate");
    });
  }, [activeAnnotation]);

  if (!span) {
    return (
      <div className="flex h-full flex-col p-4">
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
  return (
    <ResizablePanelGroup direction="horizontal" className="h-full p-4">
      <ResizablePanel defaultSize={25} minSize={15} className="flex flex-col gap-1">
        <Typography variant="h3" className="max-w-md shrink-0 truncate">
          Annotation Queue
        </Typography>
        <div className="flex min-h-0 flex-1 flex-col gap-2 overflow-y-auto">
          <Suspense fallback={<LilypadLoading />}>
            <div className="grow-1">
              <AnnotationList
                activeAnnotation={activeAnnotation}
                setActiveAnnotation={setActiveAnnotation}
              />
            </div>
            <Separator />
            <div className="shrink-0">
              <Typography variant="h3" className="max-w-md truncate">
                Criteria
              </Typography>
              {activeAnnotation && (
                <AnnotationView annotation={activeAnnotation} path={Route.fullPath} />
              )}
            </div>
          </Suspense>
        </div>
      </ResizablePanel>

      <ResizableHandle withHandle className="m-4" />

      <ResizablePanel defaultSize={75} minSize={50} className="flex h-full flex-col">
        <FunctionTitle span={span} />

        <ResizablePanelGroup
          direction="horizontal"
          className="h-full min-h-0 flex-1 overflow-hidden"
        >
          <ResizablePanel defaultSize={65} minSize={40} className="overflow-hidden">
            <div className="h-full overflow-y-auto">
              <LilypadPanel spanUuid={span.uuid} showMetrics={false} />
            </div>
          </ResizablePanel>

          <ResizableHandle withHandle className="m-4" />

          <ResizablePanel
            defaultSize={35}
            minSize={25}
            className="flex h-full w-full flex-col gap-4 overflow-hidden"
          >
            <div className="shrink-0">
              <SpanMetrics span={span} />
            </div>
            <div className="min-h-0 flex-1">
              <Suspense fallback={<CardSkeleton items={1} />}>
                <SpanComments
                  projectUuid={projectUuid}
                  spanUuid={span.uuid}
                  activeAnnotation={activeAnnotation}
                />
              </Suspense>
            </div>
          </ResizablePanel>
        </ResizablePanelGroup>
      </ResizablePanel>
    </ResizablePanelGroup>
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
  const {
    data: annotations,
    dataUpdatedAt,
    refetch,
    isLoading,
  } = useSuspenseQuery(annotationsByProjectQueryOptions(projectUuid));

  const { data: users } = useSuspenseQuery(usersByOrganizationQueryOptions());
  const deleteAnnotation = useDeleteAnnotationMutation();
  const { data: functions } = useSuspenseQuery(functionsQueryOptions(projectUuid));
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
    <div className="flex h-full flex-col gap-2">
      <Typography variant="span" affects="muted" className="flex items-center gap-2">
        {`Last updated: ${formatRelativeTime(new Date(dataUpdatedAt))}`}
        <Button
          variant="outline"
          size="icon"
          loading={isLoading}
          onClick={() => {
            refetch();
            toast.success("Refreshed annotations");
          }}
          className="group relative size-8 overflow-hidden transition-all hover:bg-gray-100"
        >
          <RefreshCcw className="h-4 w-4" />
        </Button>
      </Typography>
      <Typography affects="muted" variant="span">
        {annotations.length > 0 && `${annotations.length} item(s) remaining`}
      </Typography>
      <div className="flex flex-col gap-2 overflow-auto">
        {annotations.map((annotation) => {
          const fn = annotation.function_uuid ? functionsMap[annotation.function_uuid] : null;
          return (
            <div
              key={annotation.uuid}
              className={cn(
                "group relative flex cursor-pointer items-center rounded-md px-1 py-2 transition-colors hover:bg-accent/50",
                annotationUuid === annotation.uuid && "bg-accent font-medium"
              )}
              onClick={() => {
                if (activeAnnotation?.uuid === annotation.uuid) {
                  setActiveAnnotation(null);
                  navigate({
                    to: Route.fullPath,
                    replace: true,
                    params: { projectUuid, _splat: "" },
                  }).catch(() => {
                    toast.error("Failed to navigate");
                  });
                } else {
                  setActiveAnnotation(annotation);
                }
              }}
            >
              <div className="flex w-full min-w-0 flex-col">
                <div className="flex w-full items-center gap-2 pr-8">
                  <span className="max-w-full truncate font-medium">
                    {annotation.span.display_name}
                  </span>
                  {fn && (
                    <Typography variant="span" className="shrink-0 text-xs whitespace-nowrap">
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
              <Button
                type="button"
                variant="outlineDestructive"
                size="icon"
                className="absolute top-1/2 right-2 size-7 -translate-y-1/2 transform opacity-0 transition-opacity group-hover:opacity-100"
                onClick={(e) => {
                  e.stopPropagation();
                  deleteAnnotation
                    .mutateAsync({
                      projectUuid: annotation.project_uuid,
                      annotationUuid: annotation.uuid,
                    })
                    .catch(() => toast.error("Failed to remove annotation from queue"));
                  toast.success("Annotation removed from queue.");
                }}
              >
                <Trash className="size-4" />
              </Button>
            </div>
          );
        })}
      </div>
    </div>
  );
};
