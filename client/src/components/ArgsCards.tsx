import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { ScrollArea, ScrollBar } from "@/components/ui/scroll-area";
import { cn } from "@/lib/utils";
import JsonView from "@uiw/react-json-view";

interface Args {
  [key: string]: any;
}

interface ArgsCardsProps {
  args: Args;
}

export const ArgsCards = ({ args }: ArgsCardsProps) => {
  return (
    <Card className='w-full max-w-4xl'>
      <CardHeader>
        <CardTitle>{"Function Arguments"}</CardTitle>
      </CardHeader>
      <ScrollArea className='whitespace-nowrap rounded-md'>
        <CardContent className='flex gap-2'>
          {Object.keys(args).length > 0 ? (
            Object.entries(args).map(([key, value]) => (
              <ArgCard key={key} title={key} value={value} />
            ))
          ) : (
            <CardContent className='p-0'>{"No arguments"}</CardContent>
          )}
        </CardContent>
        <ScrollBar orientation='horizontal' />
      </ScrollArea>
    </Card>
  );
};

const ArgCard = ({ title, value }: { title: string; value: any }) => {
  return (
    <Dialog>
      <DialogTrigger asChild>
        <Card className='p-4 max-w-[200px] hover:shadow-lg transition-all duration-200 cursor-pointer'>
          <CardHeader className='p-0'>
            <CardTitle>{title}</CardTitle>
          </CardHeader>
          <CardContent className='p-0 truncate'>
            {typeof value === "object" && value ? (
              <JsonView collapsed={true} value={value} />
            ) : (
              <span className='text-base'>{String(value)}</span>
            )}
          </CardContent>
        </Card>
      </DialogTrigger>
      <DialogContent className={cn("max-w-[425px] overflow-x-auto")}>
        <DialogHeader className='flex-shrink-0'>
          <DialogTitle>{title}</DialogTitle>
        </DialogHeader>
        {typeof value === "object" && value ? (
          <JsonView collapsed={true} value={value} />
        ) : (
          <span className='text-base'>{String(value)}</span>
        )}
      </DialogContent>
    </Dialog>
  );
};
