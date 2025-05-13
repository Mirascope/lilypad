import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Typography } from "@/components/ui/typography";
import { AggregateMetrics, FunctionPublic, TimeFrame } from "@/types/types";
import { aggregatesByFunctionQueryOptions } from "@/utils/spans";
import { formatDate } from "@/utils/strings";
import { useSuspenseQueries } from "@tanstack/react-query";
import {
  Bar,
  CartesianGrid,
  ComposedChart,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

export const FunctionCostAndTokensChart = ({
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
    <CostAndTokensChart
      metricsData={extractedMetricsData}
      title={title}
      labels={labels}
    />
  );
};
export const CostAndTokensChart = ({
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

    metrics.forEach((metric) => {
      const date = metric.start_date;
      if (!dateMap.has(date)) {
        dateMap.set(date, { start_date: date });
      }

      const entry = dateMap.get(date);
      entry[`cost_${index}`] = metric.total_cost;
      entry[`input_tokens_${index}`] = metric.total_input_tokens;
      entry[`output_tokens_${index}`] = metric.total_output_tokens;
      entry[`source_${index}`] = sourceLabel;
    });
  });

  // Convert map to array and sort by date
  const combinedData = Array.from(dateMap.values()).sort(
    (a, b) =>
      new Date(a.start_date).getTime() - new Date(b.start_date).getTime()
  );

  // Custom tooltip to show input and output token details
  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;

      return (
        <div className="bg-background p-4 rounded shadow-md border">
          <p className="font-medium">{formatDate(label, false)}</p>

          {metricsData.map((_, index) => {
            // Only show data for this source if it exists for this date point
            if (data[`cost_${index}`] !== undefined) {
              return (
                <div key={index} className="mt-2">
                  <p
                    className="font-medium"
                    style={{ color: index === 0 ? "#6366f1" : "#f59e0b" }}
                  >
                    {labels[index]}
                  </p>
                  <p className="text-purple-600">
                    Total Cost: ${data[`cost_${index}`]?.toFixed(4)}
                  </p>
                  <p className="text-emerald-600">
                    Input Tokens:{" "}
                    {data[`input_tokens_${index}`]?.toLocaleString()}
                  </p>
                  <p className="text-amber-600">
                    Output Tokens:{" "}
                    {data[`output_tokens_${index}`]?.toLocaleString()}
                  </p>
                </div>
              );
            }
            return null;
          })}
        </div>
      );
    }
    return null;
  };

  // Define colors for each dataset
  const colors = ["#6366f1", "#f59e0b", "#10b981", "#ef4444"];
  return (
    <Card className="w-full h-full flex flex-col">
      <CardHeader className="shrink-0 pb-2">
        <CardTitle>{title}</CardTitle>
      </CardHeader>
      <CardContent className="flex-grow p-4 flex flex-col items-center justify-center h-full">
        {combinedData.length > 0 ? (
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={combinedData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="start_date"
                tickFormatter={(value) => formatDate(value, false)}
              />
              <YAxis
                yAxisId="cost"
                orientation="left"
                axisLine={{ strokeWidth: 1 }}
                tickLine={false}
                width={60}
              />
              <Tooltip content={<CustomTooltip />} />
              <Legend />

              {metricsData.map((_, index) => (
                <Bar
                  key={index}
                  yAxisId="cost"
                  dataKey={`cost_${index}`}
                  fill={colors[index % colors.length]}
                  name={labels[index]}
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
