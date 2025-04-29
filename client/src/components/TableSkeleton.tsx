import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { useRef } from "react";

interface TableSkeletonProps {
  columns?: number;
  rows?: number;
  showHeader?: boolean;
  isFetchingNextPage?: boolean;
}

const TableSkeleton = ({
  columns = 4,
  rows = 5,
  showHeader = true,
  isFetchingNextPage = false,
}: TableSkeletonProps) => {
  const endRef = useRef<HTMLTableRowElement>(null);

  return (
    <div className="rounded-md border">
      <Table>
        {showHeader && (
          <TableHeader>
            <TableRow>
              {Array.from({ length: columns }).map((_, index) => (
                <TableHead key={index}>
                  <Skeleton className="h-4 w-[80px]" />
                </TableHead>
              ))}
            </TableRow>
          </TableHeader>
        )}
        <TableBody>
          {Array.from({ length: rows }).map((_, rowIndex) => (
            <TableRow key={rowIndex}>
              {Array.from({ length: columns }).map((_, colIndex) => (
                <TableCell key={colIndex}>
                  <Skeleton
                    className={`h-4 w-[${colIndex === 0 ? "120px" : "80px"}]`}
                  />
                </TableCell>
              ))}
            </TableRow>
          ))}
          <TableRow ref={endRef}>
            <TableCell colSpan={columns} className="h-6 p-0" />
          </TableRow>
          {isFetchingNextPage && (
            <TableRow>
              <TableCell colSpan={columns} className="text-center">
                Loading...
              </TableCell>
            </TableRow>
          )}
        </TableBody>
      </Table>
    </div>
  );
};

export default TableSkeleton;
