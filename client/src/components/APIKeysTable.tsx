import { useAuth } from "@/auth";
import { CodeSnippet } from "@/components/CodeSnippet";
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
  FormMessage,
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
import { environmentsQueryOptions } from "@/utils/environments";
import { projectsQueryOptions } from "@/utils/projects";
import { formatDate } from "@/utils/strings";
import { useSuspenseQuery } from "@tanstack/react-query";
import { ColumnDef } from "@tanstack/react-table";
import { PlusCircle, Trash, TriangleAlert } from "lucide-react";
import { Dispatch, SetStateAction, useRef, useState } from "react";
import { useForm } from "react-hook-form";

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
      accessorKey: "environment.name",
      header: "Environment",
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
      <div className="flex gap-2 items-center">
        <Typography variant="h4">API Keys</Typography>
        <CreateKeyButton />
      </div>
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
        <Button
          variant="ghost"
          size="iconSm"
          className="text-primary hover:text-primary/80 hover:bg-white"
        >
          <PlusCircle />
        </Button>
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
  const { data: environments } = useSuspenseQuery(environmentsQueryOptions());
  const { activeProject } = useAuth();
  const methods = useForm<APIKeyCreate>({
    defaultValues: {
      name: "",
      project_uuid: activeProject?.uuid,
      environment_uuid: environments[0]?.uuid || null,
    },
  });
  const createApiKey = useCreateApiKeyMutation();
  const onSubmit = async (data: APIKeyCreate) => {
    const generatedKey = await createApiKey.mutateAsync(data);
    setApiKey(generatedKey);
    setProjectUuid(data.project_uuid);
  };
  return (
    <Form {...methods}>
      <form onSubmit={methods.handleSubmit(onSubmit)} className="space-y-6">
        <DialogHeader className="flex-shrink-0">
          <DialogTitle>Create new API Key</DialogTitle>
        </DialogHeader>
        <DialogDescription>
          Generate a Lilypad API Key for your organization.
        </DialogDescription>
        <FormField
          key="name"
          control={methods.control}
          name="name"
          rules={{
            required: {
              value: true,
              message: "Name is required",
            },
          }}
          render={({ field }) => (
            <FormItem>
              <FormLabel>Name</FormLabel>
              <FormControl>
                <Input {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        <FormField
          key="project_uuid"
          control={methods.control}
          name="project_uuid"
          rules={{
            required: {
              value: true,
              message: "Project is required",
            },
          }}
          render={({ field }) => (
            <FormItem>
              <FormLabel>Project</FormLabel>
              <FormControl>
                <Select
                  value={field.value ?? ""}
                  onValueChange={field.onChange}
                >
                  <SelectTrigger className="w-full">
                    <SelectValue placeholder="Select a project" />
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
              <FormMessage />
            </FormItem>
          )}
        />
        <FormField
          key="environment_uuid"
          control={methods.control}
          name="environment_uuid"
          rules={{
            required: {
              value: true,
              message: "Environment is required",
            },
          }}
          render={({ field }) => (
            <FormItem>
              <FormLabel>Environment</FormLabel>
              <FormControl>
                <Select
                  value={field.value ?? ""}
                  onValueChange={field.onChange}
                >
                  <SelectTrigger className="w-full">
                    <SelectValue placeholder="Select an environment" />
                  </SelectTrigger>
                  <SelectContent>
                    {environments.map((environment) => (
                      <SelectItem
                        key={environment.uuid}
                        value={environment.uuid}
                      >
                        {environment.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        <DialogFooter>
          <Button
            type="submit"
            loading={methods.formState.isSubmitting}
            className="w-full"
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
  const handleCleanup = () => {
    setApiKey(null);
    setProjectUuid(null);
  };

  if (!projectUuid) return <NotFound />;
  return (
    <div className="space-y-6 max-w-full overflow-hidden">
      <DialogHeader className="flex-shrink-0">
        <DialogTitle>API Key Created</DialogTitle>
        <DialogDescription className="space-y-4">
          Copy your project ID and API key into your environment
        </DialogDescription>
      </DialogHeader>
      <div className="overflow-x-auto">
        <CodeSnippet
          code={`LILYPAD_PROJECT_ID="${projectUuid}"
LILYPAD_API_KEY="${apiKey}"`}
          showLineNumbers={false}
        />
      </div>
      <Alert variant="destructive">
        <TriangleAlert className="h-4 w-4" />
        <AlertTitle>Warning</AlertTitle>
        <AlertDescription>
          You won&apos;t be able to see your API key again.
        </AlertDescription>
      </Alert>
      <DialogFooter>
        <DialogClose asChild>
          <Button type="button" variant="outline" onClick={handleCleanup}>
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
        <Button variant="outlineDestructive" size="icon" className="h-8 w-8">
          <Trash />
        </Button>
      </DialogTrigger>
      <DialogContent className={cn("max-w-[425px] overflow-x-auto")}>
        <DialogHeader className="flex-shrink-0">
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
            variant="destructive"
            onClick={() => handleApiKeyDelete(apiKey.uuid)}
          >
            Delete
          </Button>
          <DialogClose asChild>
            <Button type="button" variant="secondary">
              Close
            </Button>
          </DialogClose>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};
