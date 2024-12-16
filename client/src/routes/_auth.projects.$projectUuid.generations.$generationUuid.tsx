import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { PromptPublic } from "@/types/types";
import {
  generationQueryOptions,
  usePatchGenerationMutation,
} from "@/utils/generations";
import { promptsBySignature } from "@/utils/prompts";
import { useSuspenseQuery } from "@tanstack/react-query";
import { createFileRoute, useParams } from "@tanstack/react-router";
import ReactMarkdown from "react-markdown";
import JsonView from "@uiw/react-json-view";
export const Route = createFileRoute(
  "/_auth/projects/$projectUuid/generations/$generationUuid"
)({
  component: () => <Generation />,
});

const PromptCard = ({
  prompt,
  activePromptUuid,
  index,
}: {
  prompt: PromptPublic;
  activePromptUuid?: string;
  index: number;
}) => {
  const { projectUuid, generationUuid } = useParams({ from: Route.id });
  const patchGeneration = usePatchGenerationMutation();
  const handleButtonClick = () => {
    patchGeneration.mutate({
      projectUuid,
      generationUuid,
      generationUpdate: { prompt_uuid: prompt.uuid },
    });
  };
  return (
    <Card className='w-auto'>
      <CardHeader>
        <CardTitle>{prompt.name}</CardTitle>
        <CardDescription>Version {index + 1}</CardDescription>
      </CardHeader>
      <CardContent className='flex flex-col gap-2'>
        <ReactMarkdown>{prompt.template}</ReactMarkdown>
        <Separator />
        <JsonView value={prompt.call_params} />
      </CardContent>
      <CardFooter>
        <Button
          className='w-full'
          disabled={prompt.uuid === activePromptUuid}
          onClick={handleButtonClick}
        >
          {prompt.uuid === activePromptUuid ? "Active" : "Set active"}
        </Button>
      </CardFooter>
    </Card>
  );
};
const Generation = () => {
  const { projectUuid, generationUuid } = useParams({ from: Route.id });
  const { data: generation } = useSuspenseQuery(
    generationQueryOptions(projectUuid, generationUuid)
  );
  const { data: prompts } = useSuspenseQuery(
    promptsBySignature(projectUuid, generation.prompt?.signature)
  );
  return (
    <div>
      <h1>{generation.name}</h1>
      {prompts.map((prompt, i) => (
        <PromptCard
          key={prompt.uuid}
          activePromptUuid={generation.prompt?.uuid}
          prompt={prompt}
          index={i}
        />
      ))}
    </div>
  );
};
