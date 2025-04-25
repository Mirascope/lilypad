import CardSkeleton from "@/components/CardSkeleton";
import { Comment } from "@/components/Comment";
import { LilypadLoading } from "@/components/LilypadLoading";
import { LilypadPanel } from "@/components/LilypadPanel";
import { LlmPanel } from "@/components/LlmPanel";
import { Badge } from "@/components/ui/badge";
import {
  ResizableHandle,
  ResizablePanel,
  ResizablePanelGroup,
} from "@/components/ui/resizable";
import { Typography } from "@/components/ui/typography";
import { UpdateAnnotationForm } from "@/ee/components/AnnotationForm";
import { annotationsByProjectQueryOptions } from "@/ee/utils/annotations";
import {
  AnnotationPublic,
  FunctionPublic,
  Scope,
  UserPublic,
} from "@/types/types";
import { functionsQueryOptions } from "@/utils/functions";
import { formatRelativeTime } from "@/utils/strings";
import { usersByOrganizationQueryOptions } from "@/utils/users";
import { useSuspenseQuery } from "@tanstack/react-query";
import {
  createFileRoute,
  useNavigate,
  useParams,
} from "@tanstack/react-router";
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
  const [activeAnnotation, setActiveAnnotation] =
    useState<AnnotationPublic | null>(annotations[0] || null);
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
  return (
    <div className='h-screen'>
      <ResizablePanelGroup direction='horizontal'>
        <ResizablePanel defaultSize={20} id='annotation-list' order={1}>
          <Suspense fallback={<LilypadLoading />}>
            <AnnotationList
              activeAnnotation={activeAnnotation}
              setActiveAnnotation={setActiveAnnotation}
            />
          </Suspense>
        </ResizablePanel>
        <ResizableHandle />
        <ResizablePanel defaultSize={80} id='annotation-view' order={2}>
          {activeAnnotation ? (
            <Suspense
              fallback={<CardSkeleton items={5} className='flex flex-col' />}
            >
              <ResizablePanelGroup direction='horizontal'>
                <ResizablePanel
                  defaultSize={60}
                  id='annotation-view-panel'
                  order={1}
                >
                  <AnnotationView
                    annotation={activeAnnotation}
                    path={Route.fullPath}
                  />
                </ResizablePanel>
                <ResizableHandle />
                <ResizablePanel
                  defaultSize={40}
                  id='annotation-comment'
                  order={2}
                >
                  <AnnotationComment spanUuid={activeAnnotation.span_uuid} />
                </ResizablePanel>
              </ResizablePanelGroup>
            </Suspense>
          ) : (
            <div className='w-full h-full flex justify-center items-center'>
              <Typography variant='h3'>
                {annotations.length < 1
                  ? "No more annotations"
                  : "Select a trace"}
              </Typography>
            </div>
          )}
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
  const { projectUuid } = useParams({
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
    <div className='p-4 flex flex-col h-full'>
      <div className='flex-shrink-0 mb-2'>
        <Typography variant='h4'>Annotations</Typography>
        <Typography affects='muted' variant='span'>
          {annotations.length > 0 && `${annotations.length} item(s) remaining`}
        </Typography>
        <Typography affects='muted'>{`Last updated: ${formatRelativeTime(new Date(dataUpdatedAt))}`}</Typography>
      </div>
      <div className='flex flex-col gap-2 overflow-auto'>
        {annotations.map((annotation) => {
          const fn = annotation.function_uuid
            ? functionsMap[annotation.function_uuid]
            : null;
          return (
            <div
              key={annotation.uuid}
              className={`border-b cursor-pointer p-2 ${activeAnnotation?.uuid === annotation.uuid ? "bg-primary/20" : ""}`}
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
              <div className='flex items-center justify-between'>
                <div>
                  <Typography variant='span' affects='small' className='mr-1'>
                    {annotation.span.display_name}
                  </Typography>
                  {fn && (
                    <Typography affects='muted' variant='span'>
                      v{fn.version_num}
                    </Typography>
                  )}
                </div>
                <Typography variant='span' affects='muted'>
                  {formatRelativeTime(annotation.created_at, true)}
                </Typography>
              </div>
              <div>
                {annotation.assigned_to && (
                  <Badge>{usersMap[annotation.assigned_to].first_name}</Badge>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

const AnnotationView = ({
  annotation,
  path,
}: {
  annotation: AnnotationPublic;
  path: string;
}) => {
  const navigate = useNavigate();
  useEffect(() => {
    if (path) {
      navigate({
        to: path,
        replace: true,
        params: { _splat: annotation.uuid },
      }).catch(() => {
        toast.error("Failed to navigate");
      });
    }
  }, [annotation, navigate, path]);
  const handleSubmit = () => {
    if (path) {
      navigate({
        to: path,
        replace: true,
        params: { _splat: "next" },
      }).catch(() => {
        toast.error("Failed to navigate");
      });
    }
  };
  return (
    <div className='p-4 flex flex-col h-full'>
      <div className='flex-shrink-0 mb-2'>
        <UpdateAnnotationForm
          annotation={annotation}
          spanUuid={annotation.span_uuid}
          onSubmit={handleSubmit}
        />
      </div>
      <div className='flex-grow overflow-auto'>
        {annotation.span.scope === Scope.LILYPAD ? (
          <LilypadPanel spanUuid={annotation.span_uuid} />
        ) : (
          <LlmPanel spanUuid={annotation.span_uuid} />
        )}
      </div>
    </div>
  );
};

const AnnotationComment = ({ spanUuid }: { spanUuid: string }) => {
  return (
    <div className='flex flex-col h-full p-4'>
      <div className='flex-shrink-0 mb-2'>
        <Typography variant='h4'>Comments</Typography>
      </div>
      <Comment spanUuid={spanUuid} />
    </div>
  );
};
