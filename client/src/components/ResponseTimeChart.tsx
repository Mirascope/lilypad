import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Typography } from "@/components/ui/typography";
import { AggregateMetrics, FunctionPublic, TimeFrame } from "@/types/types";
import { aggregatesByFunctionQueryOptions } from "@/utils/spans";
import { formatDate } from "@/utils/strings";
import { useSuspenseQueries } from "@tanstack/react-query";
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

export const FunctionResponseTimeChart = ({
  projectUuid,
  firstFunction,
  secondFunction,
  timeFrame,
  title,
}: {
  projectUuid: string;
  firstFunction: FunctionPublic;
  secondFunction?: FunctionPublic;
  timeFrame: TimeFrame;
  title: string;
}) => {
  const metricsData = useSuspenseQueries({
    queries: [firstFunction.uuid, secondFunction?.uuid]
      .filter((uuid) => uuid !== undefined)
      .map((uuid) => ({
        ...aggregatesByFunctionQueryOptions(projectUuid, uuid, timeFrame),
      })),
  });
  const extractedMetricsData = metricsData.map((result) => result.data);
  const labels = [`${firstFunction.name} v${firstFunction.version_num}`];
  if (secondFunction) {
    labels.push(`${secondFunction.name} v${secondFunction.version_num}`);
  }
  return (
    <ResponseTimeChart
      metricsData={extractedMetricsData}
      title={title}
      labels={labels}
    />
  );
};

export const ResponseTimeChart = ({
  metricsData,
  title,
  labels,
}: {
  metricsData: AggregateMetrics[][];
  title: string;
  labels: string[];
}) => {
  // Create a map to organize data by date
  const dateMap = new Map();

  // Process all metrics data
  metricsData.forEach((metrics, index) => {
    const sourceLabel = labels[index];

    metrics?.forEach((metric) => {
      const date = metric.start_date;
      if (!dateMap.has(date)) {
        dateMap.set(date, { start_date: date });
      }

      const entry = dateMap.get(date);
      entry[`duration_${index}`] = metric.average_duration_ms;
      entry[`source_${index}`] = sourceLabel;
    });
  });

  // Convert map to array and sort by date
  const combinedData = Array.from(dateMap.values()).sort(
    (a, b) =>
      new Date(a.start_date).getTime() - new Date(b.start_date).getTime()
  );

  // Define colors for each dataset
  const colors = ["#6366f1", "#f59e0b", "#10b981", "#ef4444"];

  return (
    <Card className='w-full'>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <div className='h-64'>
          {combinedData.length > 0 ? (
            <ResponsiveContainer width='100%' height='100%'>
              <ComposedChart data={combinedData} margin={{ left: 20 }}>
                <CartesianGrid strokeDasharray='3 3' />
                <XAxis
                  dataKey='start_date'
                  tickFormatter={(value: string) => formatDate(value, false)}
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
                  labelFormatter={(label: string) => formatDate(label, false)}
                  formatter={(
                    value: number | string | unknown[],
                    name: string
                  ) => {
                    if (typeof value === "number") {
                      return [(value / 1_000_000_000).toFixed(2) + " ms", name];
                    }
                    return [
                      Number.isFinite(value)
                        ? Number(value).toFixed(2)
                        : String(value),
                      name,
                    ];
                  }}
                />
                <Legend />

                {metricsData.map((_, index) => (
                  <Line
                    key={index}
                    yAxisId='duration'
                    type='monotone'
                    dataKey={`duration_${index}`}
                    stroke={colors[index % colors.length]}
                    name={labels[index]}
                    activeDot={{ r: 8 }}
                  />
                ))}
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
