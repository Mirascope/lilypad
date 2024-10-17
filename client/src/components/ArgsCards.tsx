import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ReactNode } from "react";

interface Args {
  [key: string]: string;
}

interface ArgsCardsProps {
  args: Args;
  customContent?: (key: string, value: string) => ReactNode;
}

export const ArgsCards = ({ args, customContent }: ArgsCardsProps) => {
  return (
    <Card className='w-auto'>
      <CardHeader>
        <CardTitle>{"Function Arguments"}</CardTitle>
      </CardHeader>
      <CardContent className='flex gap-2'>
        {Object.keys(args).length > 0 ? (
          Object.entries(args).map(([key, value]) => (
            <Card key={key}>
              <CardHeader>
                <CardTitle>{key}</CardTitle>
              </CardHeader>
              {customContent ? (
                customContent(key, value)
              ) : (
                <CardContent>{`${value}`}</CardContent>
              )}
            </Card>
          ))
        ) : (
          <CardContent>{"No inputs"}</CardContent>
        )}
      </CardContent>
    </Card>
  );
};
