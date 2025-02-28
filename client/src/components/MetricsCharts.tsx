import { ChartSkeleton } from "@/components/ChartSkeleton";
import { GenerationCostAndTokensChart } from "@/components/CostAndTokensChart";
import { ResponseTimeChart } from "@/components/ResponseTimeChart";
import { Button } from "@/components/ui/button";
import { TimeFrame } from "@/types/types";
import { Calendar, CalendarDays, Clock } from "lucide-react";
import { Suspense, useState } from "react";

export const MetricCharts = ({
  projectUuid,
  generationUuid,
}: {
  projectUuid: string;
  generationUuid: string;
}) => {
  const [timeFrame, setTimeFrame] = useState<TimeFrame>(TimeFrame.DAY);
  const costTitle = `Cost and Tokens (${timeFrame})`;
  const latencyTitle = `Latency (${timeFrame})`;

  return (
    <div className='space-y-4'>
      <div className='inline-flex items-center p-1 rounded-lg bg-muted'>
        <Button
          variant={timeFrame === TimeFrame.DAY ? "default" : "ghost"}
          size='sm'
          className='flex items-center gap-1'
          onClick={() => setTimeFrame(TimeFrame.DAY)}
        >
          <Clock className='h-4 w-4' />
          <span>Day</span>
        </Button>
        <Button
          variant={timeFrame === TimeFrame.WEEK ? "default" : "ghost"}
          size='sm'
          className='flex items-center gap-1'
          onClick={() => setTimeFrame(TimeFrame.WEEK)}
        >
          <Calendar className='h-4 w-4' />
          <span>Week</span>
        </Button>
        <Button
          variant={timeFrame === TimeFrame.MONTH ? "default" : "ghost"}
          size='sm'
          className='flex items-center gap-1'
          onClick={() => setTimeFrame(TimeFrame.MONTH)}
        >
          <CalendarDays className='h-4 w-4' />
          <span>Month</span>
        </Button>
      </div>

      <div className='flex gap-2'>
        <Suspense fallback={<ChartSkeleton title={costTitle} />}>
          <GenerationCostAndTokensChart
            generationUuid={generationUuid}
            projectUuid={projectUuid}
            timeFrame={timeFrame}
            title={costTitle}
          />
        </Suspense>
        <Suspense fallback={<ChartSkeleton title={latencyTitle} />}>
          <ResponseTimeChart
            generationUuid={generationUuid}
            projectUuid={projectUuid}
            timeFrame={timeFrame}
            title={latencyTitle}
          />
        </Suspense>
      </div>
    </div>
  );
};
