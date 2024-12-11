import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea, ScrollBar } from "@/components/ui/scroll-area";
import JsonView from "@uiw/react-json-view";

interface Args {
  [key: string]: any;
}

interface ArgsCardsProps {
  args: Args;
}

export const ArgsCards = ({ args }: ArgsCardsProps) => {
  return (
    <Card className='w-auto'>
      <CardHeader>
        <CardTitle>{"Function Arguments"}</CardTitle>
      </CardHeader>
      <ScrollArea className='whitespace-nowrap rounded-md'>
        <CardContent className='flex gap-2'>
          {Object.keys(args).length > 0 ? (
            Object.entries(args).map(([key, value]) => (
              <Card key={key} className='p-4'>
                <CardHeader className='p-0'>
                  <CardTitle>{key}</CardTitle>
                </CardHeader>
                <CardContent className='p-0'>
                  {typeof value === "object" ? (
                    <JsonView collapsed={true} value={value} />
                  ) : (
                    <span>{String(value)}</span>
                  )}
                </CardContent>
              </Card>
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
