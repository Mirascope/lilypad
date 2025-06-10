import { Progress } from "@/src/components/progress";
import { Alert, AlertDescription } from "@/src/components/ui/alert";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/src/components/ui/card";
import { eventSummariesQueryOptions } from "@/src/utils/billing";
import { formatRelativeTime } from "@/src/utils/strings";
import { useSuspenseQuery } from "@tanstack/react-query";
import { AlertCircle } from "lucide-react";

const MeterUsageProgress = () => {
  const { data: eventSummaries, dataUpdatedAt } = useSuspenseQuery(eventSummariesQueryOptions());
  const monthYearShort = new Date(dataUpdatedAt).toLocaleString("default", {
    month: "short",
    year: "numeric",
  });

  const percentage = Math.min(
    (eventSummaries.current_meter / eventSummaries.monthly_total) * 100,
    100
  );
  const remaining = Math.max(eventSummaries.monthly_total - eventSummaries.current_meter, 0);
  const isOverLimit = eventSummaries.current_meter > eventSummaries.monthly_total;
  const isNearLimit = percentage >= 80 && !isOverLimit;

  // Determine color based on usage
  const getProgressColor = () => {
    if (isOverLimit) return "bg-destructive";
    if (percentage >= 90) return "bg-orange-500";
    if (percentage >= 80) return "bg-yellow-500";
    return "bg-primary";
  };

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Usage</CardTitle>
              <CardDescription>
                {monthYearShort} • Last updated: {formatRelativeTime(dataUpdatedAt)}
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Main progress bar */}
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span className="font-medium">
                {eventSummaries.current_meter.toLocaleString()} Traces
              </span>
              <span className="text-muted-foreground">
                {eventSummaries.monthly_total.toLocaleString()} limit
              </span>
            </div>
            <div className="relative">
              <Progress
                value={percentage}
                className="h-3"
                indicatorClassName={getProgressColor()}
              />
              {percentage > 100 && (
                <div className="absolute inset-0 flex items-center justify-center">
                  <span className="text-xs font-medium text-white">{percentage.toFixed(0)}%</span>
                </div>
              )}
            </div>
            <div className="flex justify-between text-xs text-muted-foreground">
              <span>{percentage.toFixed(1)}% used</span>
              {!isOverLimit && <span>{remaining.toLocaleString()} Traces remaining</span>}
              {isOverLimit && (
                <span className="font-medium text-red-500">
                  {(eventSummaries.current_meter - eventSummaries.monthly_total).toLocaleString()}{" "}
                  over limit
                </span>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Alerts */}
      {isOverLimit && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            You have exceeded your monthly limit by{" "}
            {(eventSummaries.current_meter - eventSummaries.monthly_total).toLocaleString()} API
            calls. Additional usage may incur overage charges.
          </AlertDescription>
        </Alert>
      )}

      {isNearLimit && !isOverLimit && (
        <Alert>
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            You're approaching your monthly limit. Consider upgrading your plan to avoid service
            interruptions.
          </AlertDescription>
        </Alert>
      )}
    </div>
  );
};

export default MeterUsageProgress;
