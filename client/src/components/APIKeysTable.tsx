import { useAuth } from "@/auth";
import { DataTable } from "@/components/DataTable";
import { NotFound } from "@/components/NotFound";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Typography } from "@/components/ui/typography";
import { useToast } from "@/hooks/use-toast";
import { cn } from "@/lib/utils";
import { APIKeyCreate, APIKeyPublic } from "@/types/types";
import {
  apiKeysQueryOptions,
  useCreateApiKeyMutation,
  useDeleteApiKeyMutation,
} from "@/utils/api-keys";
import { projectsQueryOptions } from "@/utils/projects";
import { formatDate } from "@/utils/strings";
import { useSuspenseQuery } from "@tanstack/react-query";
import { ColumnDef } from "@tanstack/react-table";
import { Check, Copy, Trash } from "lucide-react";
import { Dispatch, SetStateAction, useRef, useState } from "react";
import { useForm } from "react-hook-form";
const API_MODE = "api";
const PROJECT_MODE = "project";

export const APIKeysTable = () => {
  const virtualizerRef = useRef<HTMLDivElement>(null);
  const { data } = useSuspenseQuery(apiKeysQueryOptions());
  const columns: ColumnDef<APIKeyPublic>[] = [
    {
      accessorKey: "name",
      header: "Name",
    },
    {
      accessorKey: "user.first_name",
      header: "Created By",
    },
    {
      accessorKey: "project.name",
      header: "Project",
    },
    {
      accessorKey: "prefix",
      header: "Key",
      cell: ({ row }) => <div>{row.getValue("prefix")}...</div>,
    },
    {
      accessorKey: "expires_at",
      header: "Expires",
      cell: ({ row }) => {
        return <div>{formatDate(row.getValue("expires_at"))}</div>;
      },
    },
    {
      id: "actions",
      enableHiding: false,
      cell: ({ row }) => {
        return <DeleteApiKeyButton apiKey={row.original} />;
      },
    },
  ];
  return (
    <>
      <Typography variant='h4'>API Keys</Typography>
      <DataTable<APIKeyPublic>
        columns={columns}
        data={data}
        virtualizerRef={virtualizerRef}
        defaultPanelSize={50}
        virtualizerOptions={{
          count: data.length,
          estimateSize: () => 45,
          overscan: 5,
        }}
        hideColumnButton
        customControls={() => <CreateKeyButton />}
      />
    </>
  );
};

const CreateKeyButton = () => {
  const [apiKey, setApiKey] = useState<string | null>(null);
  const [projectUuid, setProjectUuid] = useState<string | null>(null);
  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button>Create API Key</Button>
      </DialogTrigger>
      <DialogContent className={cn("max-w-[425px] overflow-x-auto")}>
        {apiKey ? (
          <CopyKeyButton
            apiKey={apiKey}
            setApiKey={setApiKey}
            projectUuid={projectUuid}
            setProjectUuid={setProjectUuid}
          />
        ) : (
          <GenerateAPIKeyForm
            setApiKey={setApiKey}
            setProjectUuid={setProjectUuid}
          />
        )}
      </DialogContent>
    </Dialog>
  );
};

const GenerateAPIKeyForm = ({
  setApiKey,
  setProjectUuid,
}: {
  setApiKey: Dispatch<SetStateAction<string | null>>;
  setProjectUuid: Dispatch<SetStateAction<string | null>>;
}) => {
  const { data: projects } = useSuspenseQuery(projectsQueryOptions());
  const { activeProject } = useAuth();
  const methods = useForm<APIKeyCreate>({
    defaultValues: { name: "", project_uuid: activeProject?.uuid || "" },
  });
  const createApiKey = useCreateApiKeyMutation();
  const onSubmit = async (data: APIKeyCreate) => {
    const generatedKey = await createApiKey.mutateAsync(data);
    setApiKey(generatedKey);
    setProjectUuid(data.project_uuid);
  };
  return (
    <Form {...methods}>
      <form onSubmit={methods.handleSubmit(onSubmit)} className='space-y-6'>
        <DialogHeader className='flex-shrink-0'>
          <DialogTitle>Create new API Key</DialogTitle>
        </DialogHeader>
        <DialogDescription>
          Generate a Lilypad API Key for your organization.
        </DialogDescription>
        <FormField
          key='name'
          control={methods.control}
          name='name'
          render={({ field }) => (
            <FormItem>
              <FormLabel>Name</FormLabel>
              <FormControl>
                <Input {...field} />
              </FormControl>
            </FormItem>
          )}
        />
        <FormField
          key='project_uuid'
          control={methods.control}
          name='project_uuid'
          render={({ field }) => (
            <FormItem>
              <FormLabel>Project</FormLabel>
              <FormControl>
                <Select value={field.value} onValueChange={field.onChange}>
                  <SelectTrigger className='w-full'>
                    <SelectValue placeholder='Select a project' />
                  </SelectTrigger>
                  <SelectContent>
                    {projects.map((project) => (
                      <SelectItem key={project.uuid} value={project.uuid}>
                        {project.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </FormControl>
            </FormItem>
          )}
        />
        <DialogFooter>
          <Button
            type='submit'
            loading={methods.formState.isSubmitting}
            className='w-full'
          >
            {methods.formState.isSubmitting ? "Generating..." : "Generate Key"}
          </Button>
        </DialogFooter>
      </form>
    </Form>
  );
};

const CopyKeyButton = ({
  apiKey,
  setApiKey,
  projectUuid,
  setProjectUuid,
}: {
  apiKey: string;
  setApiKey: Dispatch<SetStateAction<string | null>>;
  projectUuid: string | null;
  setProjectUuid: Dispatch<SetStateAction<string | null>>;
}) => {
  const { toast } = useToast();
  const [projectCopied, setProjectCopied] = useState<boolean>(false);
  const [apiCopied, setApiCopied] = useState<boolean>(false);
  const copyToClipboard = async (mode: string) => {
    let title = "";
    if (apiKey && mode === API_MODE) {
      await navigator.clipboard.writeText(apiKey);
      setApiCopied(true);
      title = "Successfully copied API key to clipboard";
    } else if (projectUuid && mode === PROJECT_MODE) {
      await navigator.clipboard.writeText(projectUuid);
      setProjectCopied(true);
      title = "Successfully copied project ID to clipboard";
    }
    if (title) {
      toast({
        title,
      });
    }
  };
  const handleCleanup = () => {
    setApiKey(null);
    setProjectUuid(null);
  };

  if (!projectUuid) return <NotFound />;
  return (
    <div className='space-y-6'>
      <DialogHeader className='flex-shrink-0'>
        <DialogTitle>API Key Created</DialogTitle>
        <DialogDescription className='space-y-4'>
          Copy your project ID and API key into your environment
          <div className='bg-muted rounded-md p-4 font-mono text-sm'>
            LILYPAD_PROJECT_ID="..."
            {"\n"}
            LILYPAD_API_KEY="..."
          </div>
        </DialogDescription>
        <p className='text-red-500'>
          WARNING: You won't be able to see your API key again.
        </p>
      </DialogHeader>
      <Alert>
        <AlertTitle>LILYPAD_PROJECT ID</AlertTitle>
        <AlertDescription className='flex items-center justify-between break-all font-mono text-sm'>
          {projectUuid}
          <Button
            size='icon'
            variant='ghost'
            onClick={() => copyToClipboard(PROJECT_MODE)}
            className='h-8 w-8'
          >
            {projectCopied ? (
              <Check className='h-4 w-4' />
            ) : (
              <Copy className='h-4 w-4' />
            )}
          </Button>
        </AlertDescription>
      </Alert>
      <Alert>
        <AlertTitle>LILYPAD_API_KEY</AlertTitle>
        <AlertDescription className='flex items-center justify-between break-all font-mono text-sm'>
          {apiKey}
          <Button
            size='icon'
            variant='ghost'
            onClick={() => copyToClipboard(API_MODE)}
            className='h-8 w-8'
          >
            {apiCopied ? (
              <Check className='h-4 w-4' />
            ) : (
              <Copy className='h-4 w-4' />
            )}
          </Button>
        </AlertDescription>
      </Alert>

      <DialogFooter>
        <DialogClose asChild>
          <Button type='button' variant='secondary' onClick={handleCleanup}>
            Close
          </Button>
        </DialogClose>
      </DialogFooter>
    </div>
  );
};

const DeleteApiKeyButton = ({ apiKey }: { apiKey: APIKeyPublic }) => {
  const { toast } = useToast();
  const deleteApiKey = useDeleteApiKeyMutation();
  const handleApiKeyDelete = async (apiKeyUuid: string) => {
    const res = await deleteApiKey.mutateAsync(apiKeyUuid);
    if (res) {
      toast({
        title: "Successfully deleted API Key",
      });
    } else {
      toast({
        title: "Failed to delete API Key",
        variant: "destructive",
      });
    }
  };
  return (
    <Dialog>
      <DialogTrigger asChild onClick={(e) => e.stopPropagation()}>
        <Button variant='outline' size='icon' className='h-8 w-8'>
          <Trash />
        </Button>
      </DialogTrigger>
      <DialogContent className={cn("max-w-[425px] overflow-x-auto")}>
        <DialogHeader className='flex-shrink-0'>
          <DialogTitle>{`Delete ${apiKey.name}`}</DialogTitle>
          <DialogDescription>
            This action is final and cannot be undone.
          </DialogDescription>
          <p>
            {"Are you sure you want to delete "}
            <b>{apiKey.name}</b>?
          </p>
        </DialogHeader>

        <DialogFooter>
          <Button
            variant='destructive'
            onClick={() => handleApiKeyDelete(apiKey.uuid)}
          >
            Delete
          </Button>
          <DialogClose asChild>
            <Button type='button' variant='secondary'>
              Close
            </Button>
          </DialogClose>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};
