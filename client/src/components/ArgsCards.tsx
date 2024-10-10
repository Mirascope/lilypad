import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface Args {
  [key: string]: string;
}
export const ArgsCards = ({ args }: { args: Args }) => {
  return (
    <Card className="w-auto">
      <CardHeader>
        <CardTitle>{"Function Arguments"}</CardTitle>
      </CardHeader>
      <CardContent className="flex gap-2">
        {Object.keys(args).length > 0 ? (
          Object.entries(args).map(([key, value]) => (
            <Card key={key}>
              <CardHeader>
                <CardTitle>{key}</CardTitle>
              </CardHeader>
              <CardContent>{`${value}`}</CardContent>
            </Card>
          ))
        ) : (
          <CardContent>{"No inputs"}</CardContent>
        )}
      </CardContent>
    </Card>
  );
};
