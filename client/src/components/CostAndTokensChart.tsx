import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Typography } from "@/components/ui/typography";
import { AggregateMetrics, TimeFrame } from "@/types/types";
import { aggregatesByGenerationQueryOptions } from "@/utils/spans";
import { formatDate } from "@/utils/strings";
import { useSuspenseQuery } from "@tanstack/react-query";
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

export const GenerationCostAndTokensChart = ({
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
    <CostAndTokensChart aggregateMetrics={aggregateMetrics} title={title} />
  );
};
export const CostAndTokensChart = ({
  aggregateMetrics,
  title,
}: {
  aggregateMetrics: AggregateMetrics[];
  title: string;
}) => {
  // Custom tooltip to show input and output token details
  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className='bg-white p-4 rounded shadow-md border'>
          <p className='font-medium'>{formatDate(label, false)}</p>
          <p className='text-purple-600'>
            Total Cost: ${data?.total_cost?.toFixed(4)}
          </p>
          <p className='text-emerald-600'>
            Input Tokens: {data?.total_input_tokens?.toLocaleString()}
          </p>
          <p className='text-amber-600'>
            Output Tokens: {data?.total_output_tokens?.toLocaleString()}
          </p>
        </div>
      );
    }
    return null;
  };

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
                  yAxisId='cost'
                  orientation='left'
                  label={{
                    value: "Cost ($)",
                    angle: -90,
                    position: "insideLeft",
                    offset: -10,
                    style: { textAnchor: "middle" },
                  }}
                />
                <Tooltip content={<CustomTooltip />} />
                <Legend />
                <Bar
                  yAxisId='cost'
                  dataKey='total_cost'
                  fill='#6366f1'
                  name='Total Cost'
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
