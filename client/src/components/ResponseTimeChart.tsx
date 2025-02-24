import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { AggregateMetrics } from "@/types/types";
import {
  Area,
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
  aggregateMetrics,
}: {
  aggregateMetrics: AggregateMetrics[];
}) => {
  // Normalize dates for display
  const formatDate = (date) => {
    const d = new Date(date);
    return d.toLocaleDateString();
  };

  return (
    <Card className='w-full'>
      <CardHeader>
        <CardTitle>Performance Metrics</CardTitle>
      </CardHeader>
      <CardContent>
        <div className='h-96'>
          <ResponsiveContainer width='100%' height='100%'>
            <ComposedChart data={aggregateMetrics}>
              <CartesianGrid strokeDasharray='3 3' />
              <XAxis dataKey='start_date' tickFormatter={formatDate} />
              <YAxis
                yAxisId='duration'
                orientation='left'
                label={{
                  value: "Duration (ms)",
                  angle: -90,
                  position: "insideLeft",
                }}
              />
              <YAxis
                yAxisId='count'
                orientation='right'
                label={{
                  value: "Request Count",
                  angle: 90,
                  position: "insideRight",
                }}
              />
              <Tooltip formatter={(value, name) => [value.toFixed(2), name]} />
              <Legend />
              <Line
                yAxisId='duration'
                type='monotone'
                dataKey='total_duration_ms'
                stroke='#8884d8'
                name='Avg Duration'
              />
              <Area
                yAxisId='count'
                type='monotone'
                dataKey='span_count'
                fill='#82ca9d'
                stroke='#82ca9d'
                name='Request Volume'
              />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
};
