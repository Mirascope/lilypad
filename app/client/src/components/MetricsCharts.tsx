import { ChartSkeleton } from "@/src/components/ChartSkeleton";
import { FunctionCostAndTokensChart } from "@/src/components/CostAndTokensChart";
import { FunctionResponseTimeChart } from "@/src/components/ResponseTimeChart";
import { Button } from "@/src/components/ui/button";
import { cn } from "@/src/lib/utils";
import { FunctionPublic, TimeFrame } from "@/src/types/types";
import { Calendar, CalendarDays, Clock } from "lucide-react";
import { Suspense, useState } from "react";

export const MetricCharts = ({
  projectUuid,
  firstFunction,
  secondFunction,
  className,
}: {
  projectUuid: string;
  firstFunction: FunctionPublic;
  secondFunction?: FunctionPublic;
  className?: string;
}) => {
  const [timeFrame, setTimeFrame] = useState<TimeFrame>(TimeFrame.DAY);
  const costTitle = `Cost and Tokens (${timeFrame})`;
  const latencyTitle = `Latency (${timeFrame})`;

  return (
    <div className="flex h-full flex-col space-y-2">
      <div className="shrink-0">
        <div className="inline-flex items-center rounded-lg bg-muted p-1">
          <Button
            variant={timeFrame === TimeFrame.DAY ? "default" : "ghost"}
            size="sm"
            className="flex items-center gap-1"
            onClick={() => setTimeFrame(TimeFrame.DAY)}
          >
            <Clock className="h-4 w-4" />
            <span>Day</span>
          </Button>
          <Button
            variant={timeFrame === TimeFrame.WEEK ? "default" : "ghost"}
            size="sm"
            className="flex items-center gap-1"
            onClick={() => setTimeFrame(TimeFrame.WEEK)}
          >
            <Calendar className="h-4 w-4" />
            <span>Week</span>
          </Button>
          <Button
            variant={timeFrame === TimeFrame.MONTH ? "default" : "ghost"}
            size="sm"
            className="flex items-center gap-1"
            onClick={() => setTimeFrame(TimeFrame.MONTH)}
          >
            <CalendarDays className="h-4 w-4" />
            <span>Month</span>
          </Button>
        </div>
      </div>

      <div className={cn("flex grow-1 gap-2", className)}>
        <Suspense fallback={<ChartSkeleton title={costTitle} />}>
          <FunctionCostAndTokensChart
            firstFunction={firstFunction}
            secondFunction={secondFunction}
            projectUuid={projectUuid}
            timeFrame={timeFrame}
            title={costTitle}
          />
        </Suspense>
        <Suspense fallback={<ChartSkeleton title={latencyTitle} />}>
          <FunctionResponseTimeChart
            firstFunction={firstFunction}
            secondFunction={secondFunction}
            projectUuid={projectUuid}
            timeFrame={timeFrame}
            title={latencyTitle}
          />
        </Suspense>
      </div>
    </div>
  );
};
