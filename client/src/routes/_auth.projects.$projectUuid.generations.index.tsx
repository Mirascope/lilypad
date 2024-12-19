import { CodeSnippet } from "@/components/CodeSnippet";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { Typography } from "@/components/ui/typography";
import { GenerationPublic } from "@/types/types";
import { uniqueLatestVersionGenerationNamesQueryOptions } from "@/utils/generations";
import { useSuspenseQuery } from "@tanstack/react-query";
import {
  createFileRoute,
  useNavigate,
  useParams,
} from "@tanstack/react-router";

export const Route = createFileRoute(
  "/_auth/projects/$projectUuid/generations/"
)({
  component: () => <GenerationsList />,
});

const GenerationCards = ({
  generation,
  index,
}: {
  generation: GenerationPublic;
  index: number;
}) => {
  const navigate = useNavigate();
  const { projectUuid } = useParams({ from: Route.id });
  const handleClick = () => {
    navigate({ to: `/projects/${projectUuid}/generations/${generation.name}` });
  };
  return (
    <Card className='w-auto h max-w-[400px]'>
      <CardHeader
        className='px-6 py-4 over:shadow-lg transition-all duration-200 cursor-pointer'
        onClick={handleClick}
      >
        <CardTitle>{generation.name}</CardTitle>
        <CardDescription>
          Latest Version: v{generation.version_num}
        </CardDescription>
      </CardHeader>
      <Separator />
      <CardContent className='p-0 m-6 overflow-auto max-h-[100px]'>
        <CodeSnippet code={generation.code} />
      </CardContent>
      <CardFooter className='flex flex-col gap-2 items-start'>
        {generation.prompt ? (
          <div className='flex flex-col gap-2 w-full'>
            <CardTitle className='font-semibold leading-none tracking-tight'>
              Prompt
            </CardTitle>
            <CardDescription>
              Using {generation.prompt.name}: v{generation.prompt.version_num}
            </CardDescription>
            <CodeSnippet code={generation.prompt.code} />
          </div>
        ) : (
          <Typography variant='body1'>No prompt</Typography>
        )}
      </CardFooter>
    </Card>
  );
};
const GenerationsList = () => {
  const { projectUuid } = useParams({ from: Route.id });
  const { data } = useSuspenseQuery(
    uniqueLatestVersionGenerationNamesQueryOptions(projectUuid)
  );
  if (data.length === 0) {
    return <GenerationNoDataPlaceholder />;
  }
  return (
    <div className='p-4 flex flex-col items-center gap-2'>
      <div className='text-left'>
        <h1 className='text-4xl font-bold text-left'>Generations</h1>
        <div className='flex gap-2 max-w-full flex-wrap'>
          {data.map((generation, i) => (
            <GenerationCards
              key={generation.uuid}
              generation={generation}
              index={i}
            />
          ))}
        </div>
      </div>
    </div>
  );
};

const GenerationNoDataPlaceholder = () => {
  return (
    <div className='min-h-screen p-8'>
      <div className='max-w-4xl mx-auto'>
        <div>
          No generations found. Start by decorating your LLM powered functions
          with <code>@lilypad.generation()</code>.
        </div>
        <CodeSnippet
          code={`
from openai import OpenAI

import lilypad

client = OpenAI()
lilypad.configure()


@lilypad.generation()
def recommend_book(genre: str) -> str:
completion = client.chat.completions.create(
model="gpt-4o-mini",
messages=[{"role": "user", "content": f"Recommend a {genre} book"}],
)
return str(completion.choices[0].message.content)


recommend_book("fantasy")`}
        />
      </div>
    </div>
  );
};
