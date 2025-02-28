import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

export const ChartSkeleton = ({ title }: { title: string }) => {
  return (
    <Card className='w-full'>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <div className='h-64 flex flex-col justify-between'>
          <Skeleton className='h-64 w-full' />
        </div>
      </CardContent>
    </Card>
  );
};
