import CardSkeleton from "@/components/CardSkeleton";
import { CodeSnippet } from "@/components/CodeSnippet";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Separator } from "@/components/ui/separator";
import { Typography } from "@/components/ui/typography";
import { useToast } from "@/hooks/use-toast";
import { GenerationTab } from "@/types/generations";
import { GenerationPublic } from "@/types/types";
import {
  uniqueLatestVersionGenerationNamesQueryOptions,
  useArchiveGenerationByNameMutation,
} from "@/utils/generations";
import { useSuspenseQuery } from "@tanstack/react-query";
import {
  createFileRoute,
  useNavigate,
  useParams,
} from "@tanstack/react-router";
import { MoreHorizontal, Trash } from "lucide-react";
import { Suspense, useState } from "react";

export const Route = createFileRoute(
  "/_auth/projects/$projectUuid/generations/"
)({
  component: () => <GenerationsList />,
});

const GenerationCards = () => {
  const { projectUuid } = useParams({ from: Route.id });
  const { data } = useSuspenseQuery(
    uniqueLatestVersionGenerationNamesQueryOptions(projectUuid)
  );
  if (data.length === 0) {
    return <GenerationNoDataPlaceholder />;
  }
  return (
    <>
      {data.map((generation) => (
        <GenerationCard key={generation.uuid} generation={generation} />
      ))}
    </>
  );
};
const GenerationCard = ({ generation }: { generation: GenerationPublic }) => {
  const navigate = useNavigate();
  const [hover, setHover] = useState(false);
  const { projectUuid } = useParams({ from: Route.id });
  const { toast } = useToast();
  const archiveGenerationName = useArchiveGenerationByNameMutation();
  const handleClick = () => {
    navigate({
      to: `/projects/${projectUuid}/generations/${generation.name}/${generation.uuid}/${GenerationTab.OVERVIEW}`,
    });
  };
  const handleArchive = async () => {
    await archiveGenerationName.mutateAsync({
      projectUuid,
      generationName: generation.name,
    });
    toast({ title: `Successfully deleted generation ${generation.name}` });
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
        <CardTitle className='flex justify-between items-center'>
          {generation.name}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant='ghost' className='h-8 w-8 p-0'>
                <span className='sr-only'>Open menu</span>
                <MoreHorizontal className='h-4 w-4' />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align='end'>
              <DropdownMenuLabel>Actions</DropdownMenuLabel>
              {/* Prevents closing the dropdown */}
              <div onClick={(e) => e.stopPropagation()}>
                <Dialog>
                  <DialogTrigger asChild>
                    <DropdownMenuItem
                      className='flex items-center gap-2 text-destructive hover:text-destructive focus:text-destructive'
                      onSelect={(e) => e.preventDefault()}
                    >
                      <Trash className='w-4 h-4' />
                      <span className='font-medium'>Delete generation</span>
                    </DropdownMenuItem>
                  </DialogTrigger>
                  <DialogContent className={"max-w-[425px] overflow-x-auto"}>
                    <DialogTitle>{`Delete Generation ${generation.name}`}</DialogTitle>
                    <DialogDescription>
                      {`Deleting ${generation.name} will delete all versions of this generation.`}
                    </DialogDescription>
                    <DialogFooter>
                      <DialogClose asChild>
                        <Button variant='destructive' onClick={handleArchive}>
                          Delete Generation
                        </Button>
                      </DialogClose>
                      <DialogClose asChild>
                        <Button variant='outline'>Cancel</Button>
                      </DialogClose>
                    </DialogFooter>
                  </DialogContent>
                </Dialog>
              </div>
            </DropdownMenuContent>
          </DropdownMenu>
        </CardTitle>
        <CardDescription>
          Latest Version: v{generation.version_num}
        </CardDescription>
      </CardHeader>
      <Separator />
      <CardContent className='p-0 m-6 overflow-auto max-h-[100px]'>
        <CodeSnippet code={generation.code} />
      </CardContent>
      <CardFooter className='flex flex-col gap-2 items-start'>
        <div className='flex flex-col gap-2 w-full'>
          <h3 className='text-sm font-medium text-gray-500'>Prompt</h3>
          {generation.prompt ? (
            <>
              <CardDescription>
                Using {generation.prompt.name}: v{generation.prompt.version_num}
              </CardDescription>
              <CodeSnippet code={generation.prompt.code} />
            </>
          ) : (
            <Typography variant='small'>No prompt</Typography>
          )}
        </div>
      </CardFooter>
    </Card>
  );
};
const GenerationsList = () => {
  return (
    <div className='p-4 flex flex-col lg:items-center gap-2'>
      <div className='text-left'>
        <h1 className='text-4xl font-bold text-left mb-2'>Generations</h1>
        <div className='flex gap-2 max-w-full flex-wrap'>
          <Suspense fallback={<CardSkeleton items={2} />}>
            <GenerationCards />
          </Suspense>
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
