import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface InputValues {
  [key: string]: string;
}
export const InputsCards = ({ inputValues }: { inputValues: InputValues }) => {
  return (
    <Card className='w-auto'>
      <CardHeader>
        <CardTitle>{"Inputs"}</CardTitle>
      </CardHeader>
      <CardContent className='flex gap-2'>
        {Object.keys(inputValues).length > 0 ? (
          Object.entries(inputValues).map(([key, value]) => (
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
