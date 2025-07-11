import CardSkeleton from "@/src/components/CardSkeleton";
import { CodeBlock } from "@/src/components/code-block";
import { LilypadLoading } from "@/src/components/LilypadLoading";
import { Button } from "@/src/components/ui/button";
import { Card, CardDescription, CardHeader, CardTitle } from "@/src/components/ui/card";
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogTitle,
  DialogTrigger,
} from "@/src/components/ui/dialog";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuTrigger,
} from "@/src/components/ui/dropdown-menu";
import { Typography } from "@/src/components/ui/typography";
import { ProcessedData, useProjectAggregates } from "@/src/hooks/use-project-aggregates";
import { FunctionTab } from "@/src/types/functions";
import { FunctionPublic, TimeFrame } from "@/src/types/types";
import {
  fetchFunctionsByName,
  functionKeys,
  uniqueLatestVersionFunctionNamesQueryOptions,
  useArchiveFunctionByNameMutation,
} from "@/src/utils/functions";
import { useQueryClient, useSuspenseQuery } from "@tanstack/react-query";
import { createFileRoute, useNavigate, useParams } from "@tanstack/react-router";
import { Clock, DollarSign, MoreHorizontal, Trash } from "lucide-react";
import { Suspense, useState } from "react";
import { toast } from "sonner";

export const Route = createFileRoute("/_auth/projects/$projectUuid/functions/")({
  component: () => (
    <Suspense fallback={<LilypadLoading />}>
      <FunctionsList />
    </Suspense>
  ),
});

const FunctionCards = () => {
  const { projectUuid } = useParams({ from: Route.id });
  const { data } = useSuspenseQuery(uniqueLatestVersionFunctionNamesQueryOptions(projectUuid));
  const { functionAggregates } = useProjectAggregates(projectUuid, TimeFrame.LIFETIME);
  if (data.length === 0) {
    return <FunctionNoDataPlaceholder />;
  }
  return (
    <>
      {data.map((fn) => (
        <FunctionCard key={fn.uuid} fn={fn} processedData={functionAggregates[fn.uuid]} />
      ))}
    </>
  );
};
const FunctionCard = ({
  fn,
  processedData,
}: {
  fn: FunctionPublic;
  processedData?: ProcessedData;
}) => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [hover, setHover] = useState(false);
  const { projectUuid } = useParams({ from: Route.id });
  const archiveFunctionName = useArchiveFunctionByNameMutation();
  const handleClick = () => {
    navigate({
      to: `/projects/${projectUuid}/functions/${fn.name}/${fn.uuid}/${FunctionTab.OVERVIEW}`,
    }).catch(() => toast.error("Failed to navigate"));
  };
  const handleArchive = async () => {
    await archiveFunctionName.mutateAsync({
      projectUuid,
      functionName: fn.name,
    });
    toast.success(`Successfully deleted function ${fn.name}`);
  };
  const prefetch = () => {
    queryClient
      .prefetchQuery({
        queryKey: functionKeys.list(fn.name),
        queryFn: () => fetchFunctionsByName(fn.name, projectUuid),
      })
      .catch(() => toast.error("Failed to prefetch function"));
  };
  return (
    <Card
      className={`w-full max-w-[300px] transition-all duration-200 ${hover ? "shadow-lg" : ""}`}
    >
      <CardHeader
        className="cursor-pointer px-6 py-4"
        onClick={handleClick}
        onMouseEnter={() => {
          setHover(true);
          prefetch();
        }}
        onMouseLeave={() => setHover(false)}
        onFocus={() => {
          setHover(true);
          prefetch();
        }}
        onBlur={() => setHover(false)}
      >
        <CardTitle className="flex items-center justify-between">
          <div className="flex gap-2">
            {fn.name}
            <Typography variant="p" affects="muted">
              v{fn.version_num}
            </Typography>
          </div>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" className="h-8 w-8 p-0">
                <span className="sr-only">Open menu</span>
                <MoreHorizontal className="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuLabel>Actions</DropdownMenuLabel>
              {/* Prevents closing the dropdown */}
              <div onClick={(e) => e.stopPropagation()}>
                <Dialog>
                  <DialogTrigger asChild>
                    <DropdownMenuItem
                      className="flex items-center gap-2 text-destructive hover:text-destructive focus:text-destructive"
                      onSelect={(e) => e.preventDefault()}
                    >
                      <Trash className="h-4 w-4" />
                      <span className="font-medium">Delete function</span>
                    </DropdownMenuItem>
                  </DialogTrigger>
                  <DialogContent className={"max-w-[425px] overflow-x-auto"}>
                    <DialogTitle>{`Delete Function ${fn.name}`}</DialogTitle>
                    <DialogDescription>
                      {`Deleting ${fn.name} will delete all versions of this function.`}
                    </DialogDescription>
                    <DialogFooter>
                      <DialogClose asChild>
                        <Button variant="destructive" onClick={handleArchive}>
                          Delete Function
                        </Button>
                      </DialogClose>
                      <DialogClose asChild>
                        <Button variant="outline">Cancel</Button>
                      </DialogClose>
                    </DialogFooter>
                  </DialogContent>
                </Dialog>
              </div>
            </DropdownMenuContent>
          </DropdownMenu>
        </CardTitle>
        <CardDescription>
          {processedData && (
            <span className="flex gap-4">
              <span className="flex items-center gap-1">
                <DollarSign className="size-4" />
                {(processedData.total_cost / processedData.span_count).toFixed(5)}
              </span>
              <span className="flex items-center gap-1">
                <Clock className="size-4" />
                {(processedData.average_duration_ms / 1_000_000_000).toFixed(3)}s
              </span>
            </span>
          )}
        </CardDescription>
      </CardHeader>
    </Card>
  );
};
export const FunctionsList = () => {
  return (
    <div className="flex flex-col gap-10 p-4">
      <Typography variant="h3">Functions</Typography>
      <div className="flex max-w-full flex-wrap gap-2">
        <Suspense fallback={<CardSkeleton items={2} />}>
          <FunctionCards />
        </Suspense>
      </div>
    </div>
  );
};

const FunctionNoDataPlaceholder = () => {
  return (
    <div className="flex flex-col gap-4">
      <DeveloperFunctionNoDataPlaceholder />
    </div>
  );
};

const DeveloperFunctionNoDataPlaceholder = () => {
  return (
    <div className="mx-auto max-w-4xl">
      <div>
        Start by decorating your LLM powered functions with <code>@lilypad.trace()</code>.
      </div>
      <CodeBlock
        language="python"
        code={`import lilypad
from openai import OpenAI

lilypad.configure()
client = OpenAI()
​
@lilypad.trace(versioning="automatic")
def answer_question(question: str) -> str | None:
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": f"Answer this question: {question}"}],
    )
    return response.choices[0].message.content
    
response = answer_question("What is the capital of France?")
print(response)`}
      />
    </div>
  );
};
