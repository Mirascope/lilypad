import { CostAndTokensChart } from "@/components/CostAndTokensChart";
import { DataTable } from "@/components/DataTable";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { AggregateMetrics, GenerationPublic, TimeFrame } from "@/types/types";
import { generationsQueryOptions } from "@/utils/generations";
import { projectQueryOptions } from "@/utils/projects";
import { aggregatesByProjectQueryOptions } from "@/utils/spans";
import { useSuspenseQuery } from "@tanstack/react-query";
import { createFileRoute, useParams } from "@tanstack/react-router";
import { ColumnDef } from "@tanstack/react-table";
import { useRef, useState } from "react";
import {
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
export const Route = createFileRoute("/_auth/projects/$projectUuid/")({
  component: RouteComponent,
});

interface ProcessedData extends AggregateMetrics {
  date: string;
  formattedCost: string;
  total_tokens: number;
  average_duration_sec: string;
  uuid: string;
}

interface ConsolidatedRecord {
  [key: string]: {
    [key: string]: ProcessedData;
  };
}

interface PieChartData {
  name: string;
  value: number;
}

function RouteComponent() {
  return <ProjectDashboard />;
}

const ProjectDashboard = () => {
  const { projectUuid } = useParams({ from: Route.id });
  const [activeTab, setActiveTab] = useState("overview");
  const [timeFrame, setTimeFrame] = useState<TimeFrame>(TimeFrame.DAY);
  const { data: project } = useSuspenseQuery(projectQueryOptions(projectUuid));
  const { data } = useSuspenseQuery(
    aggregatesByProjectQueryOptions(projectUuid, timeFrame)
  );

  // Process data for visualization
  const processedData: ProcessedData[] = data.map((item) => {
    const date = item.start_date ? new Date(item.start_date) : new Date();

    return {
      ...item,
      date: date.toLocaleDateString(),
      formattedCost: `${item.total_cost.toFixed(5)}`,
      total_tokens: item.total_input_tokens + item.total_output_tokens,
      average_duration_sec: (item.average_duration_ms / 1000).toFixed(2),
      uuid: crypto.randomUUID(),
    };
  });

  // Group by date and generation uuid
  const consolidatedData: ConsolidatedRecord = {};
  processedData.forEach((item) => {
    if (!consolidatedData[item.date]) {
      consolidatedData[item.date] = {};
    }
    const generationKey = item.generation_uuid || item.uuid;
    if (!consolidatedData[item.date][generationKey]) {
      consolidatedData[item.date][generationKey] = item;
    } else {
      const existing = consolidatedData[item.date][generationKey];
      existing.total_cost += item.total_cost;
      existing.total_input_tokens += item.total_input_tokens;
      existing.total_output_tokens += item.total_output_tokens;
      existing.span_count += item.span_count;
      existing.total_tokens =
        existing.total_input_tokens + existing.total_output_tokens;
      existing.formattedCost = `${existing.total_cost.toFixed(5)}`;
    }
  });

  // Flatten the consolidated data for charts
  const chartData: ProcessedData[] = [];
  Object.keys(consolidatedData).forEach((date) => {
    Object.keys(consolidatedData[date]).forEach((uuid) => {
      chartData.push({
        ...consolidatedData[date][uuid],
      });
    });
  });

  // Sort by date
  chartData.sort((a, b) => {
    const dateA = a.start_date ? new Date(a.start_date).getTime() : 0; // codespell-ignore
    const dateB = b.start_date ? new Date(b.start_date).getTime() : 0;
    return dateA - dateB; // codespell-ignore
  });

  // Calculate totals
  const totalCost = chartData
    .reduce((sum, item) => sum + item.total_cost, 0)
    .toFixed(5);
  const totalTokens = chartData.reduce(
    (sum, item) => sum + item.total_tokens,
    0
  );
  const totalSpans = chartData.reduce((sum, item) => sum + item.span_count, 0);

  // Generate data for pie chart
  const pieData: PieChartData[] = [
    {
      name: "Input Tokens",
      value: chartData.reduce((sum, item) => sum + item.total_input_tokens, 0),
    },
    {
      name: "Output Tokens",
      value: chartData.reduce((sum, item) => sum + item.total_output_tokens, 0),
    },
  ];

  const COLORS: string[] = ["#6366f1", "#2f7f3e"];

  return (
    <div className='p-4 w-full'>
      <Card className='shadow-md'>
        <CardHeader>
          <CardTitle className='text-2xl font-bold'>
            {`${project.name} Dashboard`}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className='grid grid-cols-1 md:grid-cols-3 gap-4 mb-6'>
            <Card>
              <CardHeader className='pb-2'>
                <CardTitle className='text-sm font-medium'>
                  Total Cost
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className='text-2xl font-bold'>${totalCost}</div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className='pb-2'>
                <CardTitle className='text-sm font-medium'>
                  Total Tokens
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className='text-2xl font-bold'>{totalTokens}</div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className='pb-2'>
                <CardTitle className='text-sm font-medium'>
                  Total API Calls
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className='text-2xl font-bold'>{totalSpans}</div>
              </CardContent>
            </Card>
          </div>

          <Tabs
            value={activeTab}
            onValueChange={setActiveTab}
            className='w-full'
          >
            <TabsList className='grid grid-cols-3 mb-4'>
              <TabsTrigger value='overview'>Overview</TabsTrigger>
              <TabsTrigger value='tokens'>Token Usage</TabsTrigger>
              <TabsTrigger value='details'>Details</TabsTrigger>
            </TabsList>

            <TabsContent value='overview'>
              <div className='grid grid-cols-1 gap-6'>
                <CostAndTokensChart
                  aggregateMetrics={data}
                  title={`Cost and Tokens (${timeFrame})`}
                />
              </div>
            </TabsContent>

            <TabsContent value='tokens'>
              <div className='grid grid-cols-1 md:grid-cols-2 gap-6'>
                <Card>
                  <CardHeader>
                    <CardTitle>Token Usage by Type</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className='h-64'>
                      <ResponsiveContainer width='100%' height='100%'>
                        <PieChart>
                          <Pie
                            data={pieData}
                            cx='50%'
                            cy='50%'
                            labelLine={false}
                            label={({ name, percent }) =>
                              `${name}: ${(percent * 100).toFixed(0)}%`
                            }
                            outerRadius={80}
                            fill='#6366f1'
                            dataKey='value'
                          >
                            {pieData.map((_, index) => (
                              <Cell
                                key={`cell-${index}`}
                                fill={COLORS[index % COLORS.length]}
                              />
                            ))}
                          </Pie>
                          <Tooltip
                            formatter={(value) => value.toLocaleString()}
                          />
                        </PieChart>
                      </ResponsiveContainer>
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle>Daily Token Usage</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className='h-64'>
                      <ResponsiveContainer width='100%' height='100%'>
                        <LineChart data={chartData}>
                          <CartesianGrid strokeDasharray='3 3' />
                          <XAxis dataKey='date' />
                          <YAxis />
                          <Tooltip />
                          <Legend />
                          <Line
                            type='monotone'
                            dataKey='total_input_tokens'
                            name='Input Tokens'
                            stroke='#6366f1'
                            activeDot={{ r: 8 }}
                          />
                          <Line
                            type='monotone'
                            dataKey='total_output_tokens'
                            name='Output Tokens'
                            stroke='#2f7f3e'
                            activeDot={{ r: 8 }}
                          />
                        </LineChart>
                      </ResponsiveContainer>
                    </div>
                  </CardContent>
                </Card>
              </div>
            </TabsContent>

            <TabsContent value='details'>
              <Card>
                <CardHeader>
                  <CardTitle>Detailed Usage</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className='overflow-x-auto'>
                    <ProjectDetailsTable data={processedData} />
                  </div>
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
    </div>
  );
};

export const ProjectDetailsTable = ({ data }: { data: ProcessedData[] }) => {
  const { projectUuid } = useParams({ from: Route.id });
  const { data: generations } = useSuspenseQuery(
    generationsQueryOptions(projectUuid)
  );
  const mappedGenerations: { [key: string]: GenerationPublic } =
    generations.reduce(
      (acc, generation) => ({
        ...acc,
        [generation.uuid]: generation,
      }),
      {}
    );
  const virtualizerRef = useRef<HTMLDivElement>(null);
  const columns: ColumnDef<ProcessedData>[] = [
    {
      accessorKey: "date",
      header: "Date",
    },
    {
      accessorKey: "generation_uuid",
      header: "Generation",
      cell: ({ row }) => {
        const generationUuid: string = row.getValue("generation_uuid");
        const generation = mappedGenerations[generationUuid];
        return (
          <div>
            {generation.name} v{generation.version_num}
          </div>
        );
      },
    },
    {
      accessorKey: "formattedCost",
      header: "Cost",
    },
    {
      accessorKey: "total_input_tokens",
      header: "Input Tokens",
    },
    {
      accessorKey: "total_output_tokens",
      header: "Output Tokens",
    },
    {
      accessorKey: "span_count",
      header: "Span Count",
    },
  ];
  return (
    <>
      <DataTable<ProcessedData>
        columns={columns}
        data={data}
        virtualizerRef={virtualizerRef}
        defaultPanelSize={50}
        virtualizerOptions={{
          count: data.length,
          estimateSize: () => 45,
          overscan: 5,
        }}
        hideColumnButton
      />
    </>
  );
};
