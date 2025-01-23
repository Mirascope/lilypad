import { CodeSnippet } from "@/components/CodeSnippet";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
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
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Separator } from "@/components/ui/separator";
import { ToastVariants } from "@/components/ui/toast";
import { Typography } from "@/components/ui/typography";
import { useToast } from "@/hooks/use-toast";
import { PromptPublic } from "@/types/types";
import {
  uniqueLatestVersionPromptNamesQueryOptions,
  useArchivePromptByNameMutation,
} from "@/utils/prompts";
import { FormattedText } from "@/utils/strings";
import { useSuspenseQuery } from "@tanstack/react-query";
import {
  createFileRoute,
  useNavigate,
  useParams,
} from "@tanstack/react-router";
import { MoreHorizontal, Plus, Trash } from "lucide-react";
import { Suspense, useState } from "react";
import { useForm } from "react-hook-form";

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
  const { toast } = useToast();
  const archivePromptName = useArchivePromptByNameMutation();
  const handleClick = () => {
    navigate({
      to: `/projects/${projectUuid}/prompts/${prompt.name}/versions/${prompt.uuid}`,
    });
  };
  const handleArchive = async () => {
    let title = `Successfully deleted prompt ${prompt.name}`;
    let variant: ToastVariants = "default";
    try {
      await archivePromptName.mutateAsync({
        projectUuid,
        promptName: prompt.name,
      });
    } catch (e) {
      title = `Failed to delete prompt ${prompt.name}. Delete generations that use ${prompt.name}.`;
      variant = "destructive";
    }
    toast({ title, variant });
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
          {prompt.name}
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
                      <span className='font-medium'>Delete prompt</span>
                    </DropdownMenuItem>
                  </DialogTrigger>
                  <DialogContent className={"max-w-[425px] overflow-x-auto"}>
                    <DialogTitle>{`Delete Prompt ${prompt.name}`}</DialogTitle>
                    <DialogDescription>
                      {`Deleting ${prompt.name} will delete all versions of this prompt.`}
                    </DialogDescription>
                    <DialogFooter>
                      <DialogClose asChild>
                        <Button variant='destructive' onClick={handleArchive}>
                          Delete Prompt
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
  console.log(data);
  if (data.length === 0) {
    return (
      <div className='p-4 flex flex-col md:items-center gap-2'>
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
      <DialogContent className={"max-w-[425px] overflow-x-auto"}>
        <PromptNoDataPlaceholder />
      </DialogContent>
    </Dialog>
  );
};
type CreatePromptFormValues = {
  name: string;
};
const PromptNoDataPlaceholder = () => {
  const { projectUuid } = useParams({ from: Route.id });
  const methods = useForm<CreatePromptFormValues>({
    defaultValues: {
      name: "",
    },
  });
  const navigate = useNavigate();
  const onSubmit = (data: CreatePromptFormValues) => {
    navigate({
      to: `/projects/${projectUuid}/prompts/${data.name}`,
    });
  };
  return (
    <Form {...methods}>
      <Typography variant='h3'>Create a new prompt</Typography>
      <form
        className='flex flex-col gap-2'
        onSubmit={methods.handleSubmit(onSubmit)}
      >
        <FormField
          key='name'
          control={methods.control}
          name='name'
          rules={{
            required: "Prompt name is required",
            validate: (value) => {
              const pythonFunctionNameRegex = /^[a-zA-Z_][a-zA-Z0-9_]*$/;
              return (
                pythonFunctionNameRegex.test(value) ||
                "Prompt name must be a valid Python function name."
              );
            },
          }}
          render={({ field }) => (
            <FormItem>
              <FormLabel>Prompt Name</FormLabel>
              <FormControl>
                <Input {...field} placeholder='Enter prompt name' />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        <Button type='submit'>Get Started</Button>
      </form>
    </Form>
  );
};
