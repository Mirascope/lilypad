import {
  Card,
  CardContent,
  CardFooter,
  CardHeader,
} from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

const CardSkeleton = ({
  items = 2,
  className,
}: {
  items?: number;
  className?: string;
}) => {
  return (
    <div
      className={cn(
        "grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4",
        className
      )}
    >
      {[...Array(items)].map((_, index) => (
        <Card key={index} className="overflow-hidden">
          <CardHeader className="pb-4">
            <Skeleton className="h-6 w-2/3" />
          </CardHeader>

          <CardContent className="space-y-4">
            {/* Multiple lines of content */}
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-5/6" />
            <Skeleton className="h-4 w-4/6" />
          </CardContent>

          <CardFooter className="flex justify-between">
            <Skeleton className="h-8 w-24" />
            <Skeleton className="h-8 w-24" />
          </CardFooter>
        </Card>
      ))}
    </div>
  );
};

export default CardSkeleton;
