import { Card, CardContent, CardHeader, CardTitle } from "@/src/components/ui/card";
import { Typography } from "@/src/components/ui/typography";
import { AggregateMetrics, FunctionPublic, TimeFrame } from "@/src/types/types";
import { aggregatesByFunctionQueryOptions } from "@/src/utils/spans";
import { formatDate } from "@/src/utils/strings";
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
  return <ResponseTimeChart metricsData={extractedMetricsData} title={title} labels={labels} />;
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
    (a, b) => new Date(a.start_date).getTime() - new Date(b.start_date).getTime()
  );

  // Define colors for each dataset
  const colors = ["#6366f1", "#f59e0b", "#10b981", "#ef4444"];

  return (
    <Card className="flex h-full w-full flex-col">
      <CardHeader className="shrink-0 pb-2">
        <CardTitle>{title}</CardTitle>
      </CardHeader>
      <CardContent className="flex h-full flex-grow flex-col items-center justify-center p-4">
        {combinedData.length > 0 ? (
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={combinedData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="start_date"
                tickFormatter={(value: string) => formatDate(value, false)}
              />
              <YAxis
                yAxisId="duration"
                orientation="left"
                tickFormatter={(value) => (value / 1_000_000_000).toFixed(2)}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: "var(--background)",
                  borderRadius: "0.375rem",
                  border: "1px solid var(--border)",
                }}
                wrapperClassName="bg-background rounded-md shadow-md"
                labelClassName="text-foreground font-medium"
                labelFormatter={(label: string) => formatDate(label, false)}
                formatter={(value: number | string | unknown[], name: string) => {
                  // Find the corresponding color for this data series
                  const colorIndex = labels.findIndex((label) => label === name);
                  const color = colors[colorIndex % colors.length];

                  if (typeof value === "number") {
                    return [(value / 1_000_000_000).toFixed(2) + " ms", name, color];
                  }
                  return [
                    Number.isFinite(value) ? Number(value).toFixed(2) : String(value),
                    name,
                    color,
                  ];
                }}
              />
              <Legend />

              {metricsData.map((_, index) => (
                <Line
                  key={index}
                  yAxisId="duration"
                  type="monotone"
                  dataKey={`duration_${index}`}
                  stroke={colors[index % colors.length]}
                  name={labels[index]}
                  activeDot={{ r: 8 }}
                />
              ))}
            </ComposedChart>
          </ResponsiveContainer>
        ) : (
          <Typography affects="muted">No Data</Typography>
        )}
      </CardContent>
    </Card>
  );
};
