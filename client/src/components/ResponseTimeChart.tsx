import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Typography } from "@/components/ui/typography";
import { TimeFrame } from "@/types/types";
import { aggregatesByGenerationQueryOptions } from "@/utils/spans";
import { formatDate } from "@/utils/strings";
import { useSuspenseQuery } from "@tanstack/react-query";
import {
  CartesianGrid,
  ComposedChart,
  Legend,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

export const ResponseTimeChart = ({
  projectUuid,
  generationUuid,
  timeFrame,
  title,
}: {
  projectUuid: string;
  generationUuid: string;
  timeFrame: TimeFrame;
  title: string;
}) => {
  const { data: aggregateMetrics } = useSuspenseQuery(
    aggregatesByGenerationQueryOptions(projectUuid, generationUuid, timeFrame)
  );
  return (
    <Card className='w-full'>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <div className='h-64'>
          {aggregateMetrics.length > 0 ? (
            <ResponsiveContainer width='100%' height='100%'>
              <ComposedChart data={aggregateMetrics} margin={{ left: 20 }}>
                <CartesianGrid strokeDasharray='3 3' />
                <XAxis
                  dataKey='start_date'
                  tickFormatter={(value) => formatDate(value, false)}
                />
                <YAxis
                  yAxisId='duration'
                  orientation='left'
                  label={{
                    value: "Duration (ms)",
                    angle: -90,
                    position: "insideLeft",
                    offset: -10,
                    style: { textAnchor: "middle" },
                  }}
                  tickFormatter={(value) => (value / 1_000_000_000).toFixed(2)}
                />
                <Tooltip
                  labelFormatter={(label) => formatDate(label, false)}
                  formatter={(
                    value: number | string | Array<any>,
                    name: string
                  ) => {
                    if (name === "Avg Duration" && typeof value === "number") {
                      return [
                        (value / 1_000_000_000).toFixed(2) + " ms",
                        "Avg Duration (s)",
                      ];
                    }
                    return [
                      typeof value === "number" ? value.toFixed(2) : value,
                      name,
                    ];
                  }}
                />
                <Legend />
                <Line
                  yAxisId='duration'
                  type='monotone'
                  dataKey='average_duration_ms'
                  stroke='#6366f1'
                  name='Avg Duration'
                />
              </ComposedChart>
            </ResponsiveContainer>
          ) : (
            <Typography variant='muted'>No Data</Typography>
          )}
        </div>
      </CardContent>
    </Card>
  );
};
