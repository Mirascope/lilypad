import { CostAndTokensChart } from "@/src/components/CostAndTokensChart";
import { DataTable } from "@/src/components/DataTable";
import { Tab, TabGroup } from "@/src/components/TabGroup";
import TableSkeleton from "@/src/components/TableSkeleton";
import { Card, CardContent, CardHeader, CardTitle } from "@/src/components/ui/card";
import { Separator } from "@/src/components/ui/separator";
import { Typography } from "@/src/components/ui/typography";
import { useProjectAggregates } from "@/src/hooks/use-project-aggregates";
import { AggregateMetrics, FunctionPublic, TimeFrame } from "@/src/types/types";
import { functionsQueryOptions } from "@/src/utils/functions";
import { projectQueryOptions } from "@/src/utils/projects";
import { aggregatesByProjectQueryOptions } from "@/src/utils/spans";
import { useSuspenseQuery } from "@tanstack/react-query";
import { createFileRoute, useParams } from "@tanstack/react-router";
import { ColumnDef } from "@tanstack/react-table";
import { Suspense, useRef } from "react";
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

interface PieChartData {
  name: string;
  value: number;
}

function RouteComponent() {
  return <ProjectDashboard />;
}

export const ProjectDashboard = () => {
  const timeFrame = TimeFrame.LIFETIME;
  const { projectUuid } = useParams({ from: Route.id });
  const { data: project } = useSuspenseQuery(projectQueryOptions(projectUuid));
  const { data } = useSuspenseQuery(aggregatesByProjectQueryOptions(projectUuid, timeFrame));
  const { data: processedData, consolidatedData } = useProjectAggregates(projectUuid, timeFrame);

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
    const firstStartDate = a.start_date ? new Date(a.start_date).getTime() : 0;
    const secondStartDate = b.start_date ? new Date(b.start_date).getTime() : 0;
    return firstStartDate - secondStartDate;
  });

  // Calculate totals
  const totalCost = chartData.reduce((sum, item) => sum + item.total_cost, 0).toFixed(5);
  const totalTokens = chartData.reduce((sum, item) => sum + item.total_tokens, 0);
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

  const tabs: Tab[] = [
    {
      value: "overview",
      label: "Overview",
      component: (
        <div className="h-64">
          <CostAndTokensChart
            className="border-none shadow-none"
            metricsData={[data]}
            labels={["Total Cost"]}
            title={`Cost and Tokens (${timeFrame})`}
          />
        </div>
      ),
    },
    {
      value: "tokens",
      label: "Token Usage",
      component: (
        <div className="flex flex-col md:flex-row">
          <div className="flex-1">
            <Card className="h-full border-none shadow-none">
              <CardHeader>
                <CardTitle>Token Usage by Type</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={pieData}
                        cx="50%"
                        cy="50%"
                        labelLine={false}
                        label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                        outerRadius={80}
                        fill="#6366f1"
                        dataKey="value"
                      >
                        {pieData.map((_, index) => (
                          <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                        ))}
                      </Pie>
                      <Tooltip formatter={(value) => value.toLocaleString()} />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>
          </div>

          <div className="mx-2 hidden py-4 md:block">
            <Separator orientation="vertical" className="h-full" />
          </div>

          <div className="flex-1">
            <Card className="h-full border-none shadow-none">
              <CardHeader>
                <CardTitle>Daily Token Usage</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={chartData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="date" />
                      <YAxis />
                      <Tooltip />
                      <Legend />
                      <Line
                        type="monotone"
                        dataKey="total_input_tokens"
                        name="Input Tokens"
                        stroke="#6366f1"
                        activeDot={{ r: 8 }}
                      />
                      <Line
                        type="monotone"
                        dataKey="total_output_tokens"
                        name="Output Tokens"
                        stroke="#2f7f3e"
                        activeDot={{ r: 8 }}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      ),
    },
    {
      value: "details",
      label: "Details",
      component: (
        <Suspense fallback={<TableSkeleton />}>
          <ProjectDetailsTable data={processedData} />
        </Suspense>
      ),
    },
  ];

  return (
    <div className="flex w-full flex-col gap-2 p-4">
      <Typography variant="h3">{`${project.name} Dashboard`}</Typography>
      <div className="grid grid-cols-1 gap-2 md:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium">Total Cost</CardTitle>
          </CardHeader>
          <CardContent>${totalCost}</CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Total Tokens</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totalTokens}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Total API Calls</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totalSpans}</div>
          </CardContent>
        </Card>
      </div>
      <TabGroup tabs={tabs} />
    </div>
  );
};

export const ProjectDetailsTable = ({ data }: { data: ProcessedData[] }) => {
  const { projectUuid } = useParams({ from: Route.id });
  const { data: functions } = useSuspenseQuery(functionsQueryOptions(projectUuid));
  const mappedFunctions: Record<string, FunctionPublic> = functions.reduce(
    (acc, fn) => ({
      ...acc,
      [fn.uuid]: fn,
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
      accessorKey: "function_uuid",
      header: "Function",
      cell: ({ row }) => {
        const functionUuid: string = row.getValue("function_uuid");
        const fn = mappedFunctions[functionUuid];
        if (!fn) return <div>Unknown function</div>;
        return (
          <div>
            {fn.name} v{fn.version_num}
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
        className="border-none"
        columns={columns}
        data={data}
        virtualizerRef={virtualizerRef}
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
