import { generationsQueryOptions } from "@/utils/generations";
import { useSuspenseQuery } from "@tanstack/react-query";
import {
  createFileRoute,
  useNavigate,
  useParams,
} from "@tanstack/react-router";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { GenerationPublic } from "@/types/types";
import { CodeSnippet } from "@/components/CodeSnippet";
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
    navigate({ to: `/projects/${projectUuid}/generations/${generation.uuid}` });
  };
  return (
    <Card className='w-auto' onClick={handleClick}>
      <CardHeader>
        <CardTitle>{generation.name}</CardTitle>
        <CardDescription>Version {index + 1}</CardDescription>
      </CardHeader>
      <CardContent className='flex gap-2'></CardContent>
    </Card>
  );
};
const GenerationsList = () => {
  const { projectUuid } = useParams({ from: Route.id });
  const { data } = useSuspenseQuery(generationsQueryOptions(projectUuid));
  return (
    <>
      {data.length > 0 ? (
        <div className='flex'>
          {data.map((generation, i) => (
            <GenerationCards
              key={generation.uuid}
              generation={generation}
              index={i}
            />
          ))}
        </div>
      ) : (
        <div className='min-h-screen p-8'>
          <div className='max-w-4xl mx-auto'>
            <div>
              No generations found. Start by decorating your LLM powered
              functions with <code>@lilypad.generation()</code>.
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
      )}
    </>
  );
};
