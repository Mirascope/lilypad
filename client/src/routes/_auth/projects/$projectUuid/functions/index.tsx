import CardSkeleton from "@/components/CardSkeleton";
import { CodeSnippet } from "@/components/CodeSnippet";
import { LilypadLoading } from "@/components/LilypadLoading";
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
import { FunctionTab } from "@/types/functions";
import { FunctionPublic } from "@/types/types";
import {
  fetchFunctionsByName,
  functionKeys,
  uniqueLatestVersionFunctionNamesQueryOptions,
  useArchiveFunctionByNameMutation,
} from "@/utils/functions";
import { FormattedText } from "@/utils/strings";
import { useQueryClient, useSuspenseQuery } from "@tanstack/react-query";
import {
  createFileRoute,
  useNavigate,
  useParams,
} from "@tanstack/react-router";
import { MoreHorizontal, Trash } from "lucide-react";
import { Suspense, useState } from "react";
import { toast } from "sonner";

export const Route = createFileRoute("/_auth/projects/$projectUuid/functions/")(
  {
    component: () => (
      <Suspense fallback={<LilypadLoading />}>
        <FunctionsList />
      </Suspense>
    ),
  }
);

const FunctionCards = () => {
  const { projectUuid } = useParams({ from: Route.id });
  const { data } = useSuspenseQuery(
    uniqueLatestVersionFunctionNamesQueryOptions(projectUuid)
  );
  if (data.length === 0) {
    return <FunctionNoDataPlaceholder />;
  }
  return (
    <>
      {data.map((fn) => (
        <FunctionCard key={fn.uuid} fn={fn} />
      ))}
    </>
  );
};
const FunctionCard = ({ fn }: { fn: FunctionPublic }) => {
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
      className={`w-full lg:max-w-[400px] transition-all duration-200 ${hover ? "shadow-lg" : ""}`}
    >
      <CardHeader
        className="px-6 py-4 cursor-pointer"
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
        <CardTitle className="flex justify-between items-center">
          {fn.name}
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
                      <Trash className="w-4 h-4" />
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
        <CardDescription>Latest Version: v{fn.version_num}</CardDescription>
      </CardHeader>
      <Separator />
      <CardContent className="p-0 m-6 overflow-auto max-h-[100px]">
        <CodeSnippet code={fn.code} />
      </CardContent>
      <CardFooter className="flex flex-col gap-2 items-start">
        <div className="flex flex-col gap-2 w-full">
          <h3 className="text-sm font-medium text-gray-500">Template</h3>
          {fn.is_versioned && fn.prompt_template ? (
            <FormattedText
              template={fn.prompt_template ?? ""}
              values={fn.arg_types}
            />
          ) : (
            <Typography affects="muted">No template</Typography>
          )}
        </div>
      </CardFooter>
    </Card>
  );
};
const FunctionsList = () => {
  return (
    <div className="p-4 flex flex-col lg:items-center gap-2">
      <Typography variant="h2">Functions</Typography>
      <div className="flex gap-2 max-w-full flex-wrap">
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
    <div className="max-w-4xl mx-auto">
      <div>
        Start by decorating your LLM powered functions with{" "}
        <code>@lilypad.trace()</code>.
      </div>
      <CodeSnippet
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
