import { useSuspenseQuery } from "@tanstack/react-query";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { annotationMetricsByFunctionQueryOptions } from "@/ee/utils/annotations";
import { CheckCircle, CircleX } from "lucide-react";
import { useEffect, useState } from "react";

interface AnnotationMetricsProps {
  projectUuid: string;
  functionUuid: string;
  title?: string;
  description?: string;
}
export const AnnotationMetrics = ({
  projectUuid,
  functionUuid,
  title = "Annotation Pass Rate",
  description,
}: AnnotationMetricsProps) => {
  const { data: annotationMetrics } = useSuspenseQuery(
    annotationMetricsByFunctionQueryOptions(projectUuid, functionUuid)
  );
  return (
    <SuccessMetrics
      successCount={annotationMetrics.success_count}
      totalCount={annotationMetrics.total_count}
      title={title}
      description={description}
    />
  );
};

interface SuccessMetricsProps {
  successCount?: number;
  totalCount?: number;
  title: string;
  description?: string;
}

const SuccessMetrics = ({
  successCount = 0,
  totalCount = 0,
  title,
  description,
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
    <Card className="w-full max-w-md">
      <CardHeader className="pb-2">
        <CardTitle>{title}</CardTitle>
        {description && <CardDescription>{description}</CardDescription>}
      </CardHeader>
      <CardContent>
        <div className="flex flex-col items-center space-y-4">
          <div className="relative w-40 h-40 flex items-center justify-center">
            <svg className="w-full h-full" viewBox="0 0 160 160">
              <circle
                cx="80"
                cy="80"
                r={radius}
                fill="none"
                stroke="#e6e6e6"
                strokeWidth="12"
              />
              <circle
                cx="80"
                cy="80"
                r={radius}
                fill="none"
                stroke="currentColor"
                strokeWidth="12"
                strokeLinecap="round"
                strokeDasharray={circumference}
                strokeDashoffset={strokeDashoffset}
                className={getColor()}
                transform="rotate(-90 80 80)"
              />
            </svg>
            <div className="absolute flex flex-col items-center justify-center">
              <span className="text-3xl font-bold">{percentage}%</span>
              <span className="text-sm text-gray-500">Pass Rate</span>
            </div>
          </div>

          <div className="flex justify-between items-center text-sm w-full">
            <div className="flex items-center space-x-1">
              <CheckCircle className="h-4 w-4 text-green-500" />
              <span>{successCount} pass</span>
            </div>
            <div className="flex items-center space-x-1">
              <CircleX className="h-4 w-4 text-destructive" />
              <span>{totalCount - successCount} fail</span>
            </div>
            <div className="font-medium">
              {successCount} / {totalCount} total
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};
