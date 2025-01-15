import { CodeSnippet } from "@/components/CodeSnippet";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Dialog, DialogContent, DialogTrigger } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import { Typography } from "@/components/ui/typography";
import { cn } from "@/lib/utils";
import { PromptPublic } from "@/types/types";
import { uniqueLatestVersionPromptNamesQueryOptions } from "@/utils/prompts";
import { FormattedText } from "@/utils/strings";
import { useSuspenseQuery } from "@tanstack/react-query";
import {
  createFileRoute,
  useNavigate,
  useParams,
} from "@tanstack/react-router";
import { Plus } from "lucide-react";
import { Suspense, useState } from "react";

export const Route = createFileRoute("/_auth/projects/$projectUuid/prompts/")({
  component: () => (
    <Suspense fallback={<div>Loading...</div>}>
      <PromptsList />
    </Suspense>
  ),
});

const PromptCard = ({ prompt }: { prompt: PromptPublic }) => {
  const navigate = useNavigate();
  const [hover, setHover] = useState(false);
  const { projectUuid } = useParams({ from: Route.id });
  const handleClick = () => {
    navigate({
      to: `/projects/${projectUuid}/prompts/${prompt.name}/versions/${prompt.uuid}`,
    });
  };
  return (
    <Card
      className={`w-full lg:max-w-[400px] transition-all duration-200 ${hover ? "shadow-lg" : ""}`}
    >
      <CardHeader
        className='px-6 py-4 cursor-pointer'
        onClick={handleClick}
        onMouseEnter={() => setHover(true)}
        onMouseLeave={() => setHover(false)}
      >
        <CardTitle>{prompt.name}</CardTitle>
        <CardDescription>Latest Version: v{prompt.version_num}</CardDescription>
      </CardHeader>
      <Separator />
      <CardContent className='p-6 flex gap-6 flex-col'>
        <div className='space-y-2'>
          <h3 className='text-sm font-medium text-gray-500'>Template</h3>
          <div className='whitespace-pre-wrap'>
            <FormattedText
              template={prompt.template}
              values={prompt.arg_types}
            />
          </div>
        </div>
        <div className='space-y-2'>
          <h3 className='text-sm font-medium text-gray-500'>Code</h3>
          <CodeSnippet
            className='overflow-auto max-h-[100px]'
            code={prompt.code}
          />
        </div>
      </CardContent>
    </Card>
  );
};
const PromptsList = () => {
  const { projectUuid } = useParams({ from: Route.id });
  const { data } = useSuspenseQuery(
    uniqueLatestVersionPromptNamesQueryOptions(projectUuid)
  );
  if (data.length === 0) {
    return (
      <div className='p-4 flex flex-col lg:items-center gap-2'>
        <PromptNoDataPlaceholder />
      </div>
    );
  }
  return (
    <div className='p-4 flex flex-col lg:items-center gap-2'>
      <div className='text-left'>
        <h1 className='text-4xl font-bold text-left flex gap-2 mb-2'>
          Prompts
          {data.length > 0 && <CreatePromptButton />}
        </h1>
        <div className='flex gap-2 max-w-full flex-wrap'>
          {data.map((prompt, i) => (
            <PromptCard key={prompt.uuid} prompt={prompt} />
          ))}
        </div>
      </div>
    </div>
  );
};
const CreatePromptButton = () => {
  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button>
          <Plus />
        </Button>
      </DialogTrigger>
      <DialogContent className={cn("max-w-[425px] overflow-x-auto")}>
        <PromptNoDataPlaceholder />
      </DialogContent>
    </Dialog>
  );
};
const PromptNoDataPlaceholder = () => {
  const { projectUuid } = useParams({ from: Route.id });
  const navigate = useNavigate();
  const [value, setValue] = useState("");
  const handleClick = (e: React.MouseEvent<HTMLButtonElement>) => {
    e.preventDefault();
    navigate({
      to: `/projects/${projectUuid}/prompts/${value}`,
    });
  };
  return (
    <form className='flex flex-col gap-2'>
      <Typography variant='h3'>Create a new prompt</Typography>
      <Label>Prompt Name</Label>
      <Input
        value={value}
        onChange={(e) => setValue(e.target.value)}
        placeholder='Enter prompt name'
      />
      <Button onClick={handleClick}>Get Started</Button>
    </form>
  );
};
