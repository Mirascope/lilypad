import { Card, CardContent, CardHeader, CardTitle } from "@/src/components/ui/card";
import { Skeleton } from "@/src/components/ui/skeleton";

export const ChartSkeleton = ({ title }: { title: string }) => {
  return (
    <Card className="h-full w-full">
      <CardHeader>
        <CardTitle>{title}</CardTitle>
      </CardHeader>
      <CardContent className="h-full">
        <div className="flex flex-col justify-between">
          <Skeleton className="w-full" />
        </div>
      </CardContent>
    </Card>
  );
};
