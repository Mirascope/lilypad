import { CodeSnippet } from "@/components/CodeSnippet";
import { Label } from "@/components/ui/label";
import { functionsByNameQueryOptions } from "@/utils/functions";
import { useSuspenseQuery } from "@tanstack/react-query";
import {
  createFileRoute,
  useNavigate,
  useParams,
} from "@tanstack/react-router";

import CardSkeleton from "@/components/CardSkeleton";
import { FunctionSpans } from "@/components/FunctionSpans";
import { LilypadLoading } from "@/components/LilypadLoading";
import { MetricCharts } from "@/components/MetricsCharts";
import { NotFound } from "@/components/NotFound";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { FunctionAnnotations } from "@/ee/components/FunctionAnnotations";
import { annotationMetricsByFunctionQueryOptions } from "@/ee/utils/annotations";
import { useFeatureAccess } from "@/hooks/use-featureaccess";
import { useToast } from "@/hooks/use-toast";
import { Route as FunctionRoute } from "@/routes/_auth/projects/$projectUuid/functions/$functionName/_workbench/route";
import { FunctionTab } from "@/types/functions";
import { CheckCircle, CircleX, SquareTerminal } from "lucide-react";
import { Suspense, useEffect, useState } from "react";

export const Route = createFileRoute(
  "/_auth/projects/$projectUuid/functions/$functionName/_workbench/$functionUuid/$tab"
)({
  component: () => (
    <Suspense fallback={<LilypadLoading />}>
      <Function />
    </Suspense>
  ),
});

const Function = () => {
  const { projectUuid, functionName, functionUuid, tab } = useParams({
    from: FunctionRoute.id,
  });
  const { data: functions } = useSuspenseQuery(
    functionsByNameQueryOptions(functionName, projectUuid)
  );
  const fn = functions.find((f) => f.uuid === functionUuid);
  if (tab === FunctionTab.OVERVIEW) {
    return <FunctionOverview />;
  } else if (tab === FunctionTab.TRACES) {
    return fn ? (
      <FunctionSpans projectUuid={projectUuid} functionUuid={fn.uuid} />
    ) : (
      <div>No function selected</div>
    );
  } else if (tab === FunctionTab.ANNOTATIONS) {
    return fn ? (
      <FunctionAnnotations projectUuid={projectUuid} functionUuid={fn.uuid} />
    ) : (
      <div>No function selected</div>
    );
  }
};

const FunctionOverview = () => {
  const { projectUuid, functionName, functionUuid } = useParams({
    from: Route.id,
  });
  const { data: functions } = useSuspenseQuery(
    functionsByNameQueryOptions(functionName, projectUuid)
  );
  const features = useFeatureAccess();
  const navigate = useNavigate();
  const { toast } = useToast();
  const fn = functions.find((f) => f.uuid === functionUuid);
  const handlePlaygroundButtonClick = () => {
    navigate({
      to: `/projects/${projectUuid}/playground/${functionName}/${functionUuid}`,
    }).catch(() =>
      toast({
        title: "Failed to navigate",
      })
    );
  };
  if (!fn) {
    return <NotFound />;
  } else {
    return (
      <div className='p-2 flex flex-1 flex-col gap-2 max-w-4xl mx-auto'>
        {features.annotations && <AnnotationMetrics />}
        <Suspense fallback={<CardSkeleton />}>
          <MetricCharts firstFunction={fn} projectUuid={projectUuid} />
        </Suspense>
        <div>
          <Label>Code</Label>
          <CodeSnippet code={fn.code} />
        </div>
        <div>
          <Button variant='outline' onClick={handlePlaygroundButtonClick}>
            <SquareTerminal className='w-4 h-4 mr-2' />
            Go to playground
          </Button>
        </div>
      </div>
    );
  }
};

const AnnotationMetrics = () => {
  const { projectUuid, functionUuid } = useParams({
    from: Route.id,
  });
  const { data: annotationMetrics } = useSuspenseQuery(
    annotationMetricsByFunctionQueryOptions(projectUuid, functionUuid)
  );
  return (
    <SuccessMetrics
      successCount={annotationMetrics.success_count}
      totalCount={annotationMetrics.total_count}
    />
  );
};

interface SuccessMetricsProps {
  successCount?: number;
  totalCount?: number;
  title?: string;
  description?: string;
}

const SuccessMetrics = ({
  successCount = 0,
  totalCount = 0,
  title = "Annotation Pass Rate",
}: SuccessMetricsProps) => {
  // Calculate percentage
  const percentage =
    totalCount > 0 ? Math.round((successCount / totalCount) * 100) : 0;

  // Animated progress for the circle
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    // Animate progress on mount or when values change
    const timer = setTimeout(() => {
      setProgress(percentage);
    }, 100);

    return () => clearTimeout(timer);
  }, [percentage]);

  // Calculate circle properties
  const radius = 70;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (progress / 100) * circumference;

  // Determine color based on percentage
  const getColor = () => {
    if (percentage > 75) return "text-green-500";
    if (percentage > 50) return "text-yellow-500";
    return "text-red-500";
  };

  return (
    <Card className='w-full max-w-md'>
      <CardHeader className='pb-2'>
        <CardTitle>{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <div className='flex flex-col items-center space-y-4'>
          <div className='relative w-40 h-40 flex items-center justify-center'>
            <svg className='w-full h-full' viewBox='0 0 160 160'>
              <circle
                cx='80'
                cy='80'
                r={radius}
                fill='none'
                stroke='#e6e6e6'
                strokeWidth='12'
              />
              <circle
                cx='80'
                cy='80'
                r={radius}
                fill='none'
                stroke='currentColor'
                strokeWidth='12'
                strokeLinecap='round'
                strokeDasharray={circumference}
                strokeDashoffset={strokeDashoffset}
                className={getColor()}
                transform='rotate(-90 80 80)'
              />
            </svg>
            <div className='absolute flex flex-col items-center justify-center'>
              <span className='text-3xl font-bold'>{percentage}%</span>
              <span className='text-sm text-gray-500'>Pass Rate</span>
            </div>
          </div>

          <div className='flex justify-between items-center text-sm w-full'>
            <div className='flex items-center space-x-1'>
              <CheckCircle className='h-4 w-4 text-green-500' />
              <span>{successCount} pass</span>
            </div>
            <div className='flex items-center space-x-1'>
              <CircleX className='h-4 w-4 text-destructive' />
              <span>{totalCount - successCount} fail</span>
            </div>
            <div className='font-medium'>
              {successCount} / {totalCount} total
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};
