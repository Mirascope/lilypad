import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { AggregateMetrics } from "@/types/types";
import {
  Bar,
  CartesianGrid,
  ComposedChart,
  Legend,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

export const CostAndTokensChart = ({
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
        <CardTitle>Cost & Token Usage Trends</CardTitle>
      </CardHeader>
      <CardContent>
        <div className='h-96'>
          <ResponsiveContainer width='100%' height='100%'>
            <ComposedChart data={aggregateMetrics}>
              <CartesianGrid strokeDasharray='3 3' />
              <XAxis dataKey='start_date' tickFormatter={formatDate} />
              <YAxis
                yAxisId='cost'
                orientation='left'
                label={{
                  value: "Cost ($)",
                  angle: -90,
                  position: "insideLeft",
                }}
              />
              <YAxis
                yAxisId='tokens'
                orientation='right'
                label={{ value: "Tokens", angle: 90, position: "insideRight" }}
              />
              <Tooltip formatter={(value, name) => [value.toFixed(2), name]} />
              <Legend />
              <Line
                yAxisId='cost'
                type='monotone'
                dataKey='total_cost'
                stroke='#8884d8'
                name='Total Cost'
              />
              <Bar
                yAxisId='tokens'
                dataKey='total_input_tokens'
                fill='#82ca9d'
                name='Input Tokens'
                stackId='tokens'
              />
              <Bar
                yAxisId='tokens'
                dataKey='total_output_tokens'
                fill='#ffc658'
                name='Output Tokens'
                stackId='tokens'
              />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
};
