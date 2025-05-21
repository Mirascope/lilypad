import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Typography } from "@/components/ui/typography";
import { annotationMetricsByFunctionQueryOptions } from "@/ee/utils/annotations";
import { useSuspenseQuery } from "@tanstack/react-query";
import { CheckCircle, CircleX } from "lucide-react";
import { Cell, Label, Pie, PieChart, ResponsiveContainer } from "recharts";

interface AnnotationMetricsProps {
  projectUuid: string;
  functionUuid: string;
  title?: string;
  description?: string;
  className?: string;
}
export const AnnotationMetrics = ({
  projectUuid,
  functionUuid,
  title = "Annotation Pass Rate",
  description,
  className = "",
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
      className={className}
    />
  );
};

interface SuccessMetricsProps {
  successCount?: number;
  totalCount?: number;
  title: string;
  description?: string;
  className?: string;
}

const SuccessMetrics = ({
  successCount = 0,
  totalCount = 0,
  title,
  description,
  className = "",
}: SuccessMetricsProps) => {
  // Calculate percentage
  const percentage = totalCount > 0 ? Math.round((successCount / totalCount) * 100) : 0;

  // Determine color based on percentage for the label
  const getColor = () => {
    if (percentage > 75) return "text-green-500";
    if (percentage > 50) return "text-yellow-500";
    return "text-red-500";
  };

  // Define fixed colors for the pie chart
  const SUCCESS_COLOR = "#409b45"; // green-500
  const FAIL_COLOR = "oklch(0.55 0.18 48)"; // red-500

  return (
    <Card className={`flex h-full w-full flex-col ${className}`}>
      <CardHeader className="shrink-0 pb-2">
        <CardTitle>{title}</CardTitle>
        {description && <CardDescription>{description}</CardDescription>}
      </CardHeader>
      <CardContent className="flex flex-grow flex-col items-center justify-center py-6">
        {totalCount ? (
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={[
                  { name: "Success", value: successCount },
                  { name: "Fail", value: totalCount - successCount },
                ]}
                cx="50%"
                cy="50%"
                innerRadius="55%"
                outerRadius="80%"
                startAngle={90}
                endAngle={450}
                dataKey="value"
                blendStroke
                isAnimationActive={false}
              >
                <Label
                  value={`${percentage}%`}
                  position="center"
                  fontSize="16"
                  fontWeight="bold"
                  className={getColor()}
                />
                {/* Fixed colors: green for success, red for fail */}
                <Cell fill={SUCCESS_COLOR} />
                <Cell fill={FAIL_COLOR} />
              </Pie>
            </PieChart>
          </ResponsiveContainer>
        ) : (
          <Typography affects="muted">No Data</Typography>
        )}
      </CardContent>
      <CardFooter className="shrink-0 pt-0 pb-4">
        <div className="flex w-full items-center justify-between text-xs sm:text-sm">
          <div className="flex items-center space-x-1">
            <CheckCircle className="h-4 w-4 text-green-500" />
            <span>{successCount} pass</span>
          </div>
          <div className="flex items-center space-x-1">
            <CircleX className="text-destructive h-4 w-4" />
            <span>{totalCount - successCount} fail</span>
          </div>
          <div className="font-medium">
            {successCount} / {totalCount} total
          </div>
        </div>
      </CardFooter>
    </Card>
  );
};
