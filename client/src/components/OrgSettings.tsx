import { useAuth } from "@/auth";
import { DataTable } from "@/components/DataTable";
import { NotFound } from "@/components/NotFound";
import { SettingsLayout } from "@/components/SettingsLayout";
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
import {
  APIKeyCreate,
  APIKeyPublic,
  ProjectCreate,
  ProjectPublic,
} from "@/types/types";
import {
  apiKeysQueryOptions,
  useCreateApiKeyMutation,
  useDeleteApiKeyMutation,
} from "@/utils/api-keys";
import {
  projectsQueryOptions,
  useCreateProjectMutation,
} from "@/utils/projects";
import { useSuspenseQuery } from "@tanstack/react-query";
import { ColumnDef } from "@tanstack/react-table";
import { Check, Copy, KeyRound, Trash } from "lucide-react";
import { Dispatch, SetStateAction, Suspense, useRef, useState } from "react";
import { useForm } from "react-hook-form";
export const OrgSettings = () => {
  const { user } = useAuth();
  if (!user) return <NotFound />;
  const activeUserOrg = user.user_organizations?.find(
    (userOrg) => userOrg.organization_uuid === user.active_organization_uuid
  );
  if (!activeUserOrg) return <NotFound />;
  return (
    <SettingsLayout
      title={`${activeUserOrg.organization.name}'s Keys`}
      icon={KeyRound}
    >
      <Suspense fallback={<div>Loading...</div>}>
        <ProjectsTable />
        <APIKeysTable />
      </Suspense>
    </SettingsLayout>
  );
};

const ProjectsTable = () => {
  const virtualizerRef = useRef<HTMLDivElement>(null);
  const { data } = useSuspenseQuery(projectsQueryOptions());
  const { toast } = useToast();
  const handleProjectCopy = (project: ProjectPublic) => {
    navigator.clipboard.writeText(project.uuid);
    toast({
      title: `Successfully copied Project ID to clipboard for project ${project.name}`,
    });
  };
  const columns: ColumnDef<ProjectPublic>[] = [
    {
      accessorKey: "name",
      header: "Name",
    },
    {
      accessorKey: "created_at",
      header: "Created",
      cell: ({ row }) => {
        const createdDate = new Date(row.getValue("created_at") + "Z");
        const formattedCreatedDate = new Intl.DateTimeFormat("en-US", {
          year: "numeric",
          month: "short",
          day: "numeric",
          hour: "numeric",
          minute: "numeric",
          hour12: true,
        }).format(createdDate);
        return <div>{formattedCreatedDate}</div>;
      },
    },
    {
      id: "actions",
      enableHiding: false,
      cell: ({ row }) => {
        return (
          <Button
            variant='outline'
            size='icon'
            className='h-8 w-8'
            onClick={() => handleProjectCopy(row.original)}
          >
            <Copy />
          </Button>
        );
      },
    },
  ];
  return (
    <>
      <Typography variant='h4'>Projects</Typography>
      <DataTable<ProjectPublic>
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
        customControls={<CreateProjectButton />}
      />
    </>
  );
};

const APIKeysTable = () => {
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
        const expireDate = new Date(row.getValue("expires_at") + "Z");
        const formattedExpireDate = new Intl.DateTimeFormat("en-US", {
          year: "numeric",
          month: "short",
          day: "numeric",
          hour: "numeric",
          minute: "numeric",
          hour12: true,
        }).format(expireDate);
        return <div>{formattedExpireDate}</div>;
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
        customControls={<CreateKeyButton />}
      />
    </>
  );
};

const CreateProjectButton = () => {
  const { toast } = useToast();
  const methods = useForm<ProjectCreate>({
    defaultValues: { name: "" },
  });
  const createProject = useCreateProjectMutation();
  const onSubmit = async (data: ProjectCreate) => {
    const generatedKey = await createProject.mutateAsync(data);
    if (generatedKey) {
      toast({
        title: "Successfully created project",
      });
    }
  };
  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button>Create Project</Button>
      </DialogTrigger>
      <DialogContent className={cn("max-w-[425px] overflow-x-auto")}>
        <Form {...methods}>
          <form onSubmit={methods.handleSubmit(onSubmit)} className='space-y-6'>
            <DialogHeader className='flex-shrink-0'>
              <DialogTitle>Create a new project</DialogTitle>
            </DialogHeader>
            <DialogDescription>
              Create a new project for your organization.
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
            <DialogFooter>
              <DialogClose asChild>
                <Button
                  type='submit'
                  loading={methods.formState.isSubmitting}
                  className='w-full'
                >
                  {methods.formState.isSubmitting
                    ? "Creating..."
                    : "Create Project"}
                </Button>
              </DialogClose>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
};

const CreateKeyButton = () => {
  const [apiKey, setApiKey] = useState<string | null>(null);
  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button>Create API Key</Button>
      </DialogTrigger>
      <DialogContent className={cn("max-w-[425px] overflow-x-auto")}>
        {apiKey ? (
          <CopyKeyButton apiKey={apiKey} setApiKey={setApiKey} />
        ) : (
          <GenerateAPIKeyForm setApiKey={setApiKey} />
        )}
      </DialogContent>
    </Dialog>
  );
};

const API_MODE = "api";
const PROJECT_MODE = "project";
const GenerateAPIKeyForm = ({
  setApiKey,
}: {
  setApiKey: Dispatch<SetStateAction<string | null>>;
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
}: {
  apiKey: string;
  setApiKey: Dispatch<SetStateAction<string | null>>;
}) => {
  const { toast } = useToast();
  const { activeProject } = useAuth();
  const [projectCopied, setProjectCopied] = useState<boolean>(false);
  const [apiCopied, setApiCopied] = useState<boolean>(false);
  const copyToClipboard = async (mode: string) => {
    let title = "";
    if (apiKey && mode === API_MODE) {
      await navigator.clipboard.writeText(apiKey);
      setApiCopied(true);
      title = "Successfully copied API key to clipboard";
    } else if (activeProject && mode === PROJECT_MODE) {
      await navigator.clipboard.writeText(activeProject.name);
      setProjectCopied(true);
      title = "Successfully copied project to clipboard";
    }
    if (title) {
      toast({
        title,
      });
    }
  };
  const handleCleanup = () => {
    setApiKey(null);
  };
  if (!activeProject) return <NotFound />;
  return (
    <div className='space-y-6'>
      <DialogHeader className='flex-shrink-0'>
        <DialogTitle>API Key Created</DialogTitle>
        <DialogDescription className='space-y-4'>
          <p>Copy your project name and API key into your environment.</p>
          <div className='bg-muted rounded-md p-4 font-mono text-sm'>
            LILYPAD_PROJECT="..."
            {"\n"}
            LILYPAD_API_KEY="..."
          </div>
          <p className='text-red-500'>
            WARNING: You won't be able to see your API key again.
          </p>
        </DialogDescription>
      </DialogHeader>
      <Alert>
        <AlertTitle>LILYPAD_PROJECT</AlertTitle>
        <AlertDescription className='flex items-center justify-between break-all font-mono text-sm'>
          {activeProject.name}
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
