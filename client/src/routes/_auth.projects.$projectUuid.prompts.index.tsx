import {
  createFileRoute,
  Link,
  useNavigate,
  useParams,
} from "@tanstack/react-router";
import { Input } from "@/components/ui/input";
import { Typography } from "@/components/ui/typography";
import { Button } from "@/components/ui/button";
import { FormEvent, useState } from "react";
import { useSuspenseQuery } from "@tanstack/react-query";
import { uniquePromptNamesQueryOptions } from "@/utils/prompts";
import { Card, CardContent } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
export const Route = createFileRoute("/_auth/projects/$projectUuid/prompts/")({
  component: () => <CreatePrompt />,
});

export const CreatePrompt = () => {
  const { projectUuid } = useParams({ from: Route.id });
  const { data: promptNames } = useSuspenseQuery(
    uniquePromptNamesQueryOptions(projectUuid)
  );
  const [value, setValue] = useState("");
  const navigate = useNavigate();
  const handleClick = (e: FormEvent<HTMLInputElement>) => {
    e.preventDefault();
    navigate({
      to: `/projects/${projectUuid}/prompts/${value}`,
    });
  };
  return (
    <div className='min-h-screen flex flex-col items-center w-[600px] m-auto'>
      <Typography variant='h3'>Prompts</Typography>
      <div className='flex flex-wrap gap-2'>
        {promptNames.length > 0 &&
          promptNames.map((promptName) => (
            <Link
              key={promptName}
              to={`/projects/${projectUuid}/prompts/${promptName}`}
            >
              <Card className='flex items-center justify-center transition-colors hover:bg-gray-100 dark:hover:bg-gray-800'>
                <CardContent className='p-4'>{promptName}</CardContent>
              </Card>
            </Link>
          ))}
      </div>
      <Separator className='my-4' />
      <form className=' flex flex-col gap-2'>
        <Typography variant='h3'>Create a new prompt</Typography>
        <Input
          value={value}
          onChange={(e) => setValue(e.target.value)}
          placeholder='Enter prompt name'
        />
        <Button onClick={handleClick}>Get Started</Button>
      </form>
    </div>
  );
};
