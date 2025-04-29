import { DataTable } from "@/components/DataTable";
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
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Typography } from "@/components/ui/typography";
import { ProjectPublic } from "@/types/types";
import {
  projectsQueryOptions,
  useCreateProjectMutation,
  useDeleteProjectMutation,
  useUpdateProjectMutation,
} from "@/utils/projects";
import { formatDate } from "@/utils/strings";
import { useSuspenseQuery } from "@tanstack/react-query";
import { useNavigate } from "@tanstack/react-router";
import { ColumnDef } from "@tanstack/react-table";
import { Copy, PencilLine, PlusCircle, Trash } from "lucide-react";
import { useRef } from "react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";

export const ProjectsTable = () => {
  const virtualizerRef = useRef<HTMLDivElement>(null);
  const { data } = useSuspenseQuery(projectsQueryOptions());
  const handleProjectCopy = (project: ProjectPublic) => {
    navigator.clipboard.writeText(project.uuid);
    toast.success(
      `Successfully copied Project ID to clipboard for project ${project.name}`
    );
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
        return <div>{formatDate(row.getValue("created_at"))}</div>;
      },
    },
    {
      id: "actions",
      enableHiding: false,
      cell: ({ row }) => {
        return (
          <>
            <Button
              variant="outline"
              size="icon"
              className="h-8 w-8"
              onClick={() => handleProjectCopy(row.original)}
            >
              <Copy />
            </Button>
            <EditProjectButton
              projectUuid={row.original.uuid}
              defaultProjectFormData={{ name: row.original.name }}
            />
            <DeleteProjectButton project={row.original} />
          </>
        );
      },
    },
  ];
  return (
    <>
      <div className="flex gap-2 items-center">
        <Typography variant="h4">Projects</Typography>
        <CreateProjectButton />
      </div>
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
      />
    </>
  );
};

interface DeleteProjectFormValues {
  projectName: string;
}

const DeleteProjectButton = ({ project }: { project: ProjectPublic }) => {
  const methods = useForm<DeleteProjectFormValues>({
    defaultValues: {
      projectName: "",
    },
  });
  const deleteProject = useDeleteProjectMutation();
  const navigate = useNavigate();
  const onSubmit = async () => {
    await deleteProject
      .mutateAsync(project.uuid)
      .catch(() => toast.error("Failed to delete project. Please try again."));
    toast.success("Successfully deleted project");
    navigate({
      to: "/projects",
    }).catch(() => toast.error("Failed to navigate after deletion."));
  };

  return (
    <Dialog>
      <DialogTrigger asChild onClick={(e) => e.stopPropagation()}>
        <Button variant="outlineDestructive" size="icon" className="h-8 w-8">
          <Trash />
        </Button>
      </DialogTrigger>
      <DialogContent
        className={"max-w-[425px] overflow-x-auto"}
        onClick={(e) => e.stopPropagation()}
      >
        <Form {...methods}>
          <form onSubmit={methods.handleSubmit(onSubmit)} className="space-y-6">
            <DialogHeader className="flex-shrink-0">
              <DialogTitle>{`Delete ${project.name}`}</DialogTitle>
            </DialogHeader>
            <DialogDescription>
              {`Deleting ${project.name} will delete all resources tied to this project.`}
            </DialogDescription>
            <p className="text-red-500">WARNING: This action is final.</p>
            <FormField
              key="projectName"
              control={methods.control}
              name="projectName"
              rules={{
                required: "Project name is required",
                validate: (value) =>
                  value === project.name || "Project name doesn't match",
              }}
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Project Name</FormLabel>
                  <FormControl>
                    <Input {...field} />
                  </FormControl>
                  <FormDescription>
                    Please type &quot;{project.name}&quot; to confirm deletion
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />
            <DialogFooter>
              <Button
                type="submit"
                variant="destructive"
                loading={methods.formState.isSubmitting}
                className="w-full"
              >
                {methods.formState.isSubmitting
                  ? "Deleting..."
                  : "Delete Project"}
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
};

interface ProjectFormData {
  name: string;
}

interface ProjectFormProps {
  mode: "create" | "edit";
  initialData?: ProjectFormData;
  onSubmit: (data: ProjectFormData) => Promise<void>;
  trigger: React.ReactNode;
  title: string;
  description: string;
  submitButtonText: string;
  submittingText: string;
}

const ProjectForm = ({
  mode,
  initialData,
  onSubmit,
  trigger,
  title,
  description,
  submitButtonText,
  submittingText,
}: ProjectFormProps) => {
  const methods = useForm<ProjectFormData>({
    defaultValues: initialData ?? { name: "" },
  });

  const handleSubmit = async (data: ProjectFormData) => {
    await onSubmit(data).catch(() =>
      toast.error(
        `Failed to ${mode === "create" ? "create" : "update"} project`
      )
    );
    toast.success(
      `Successfully ${mode === "create" ? "created" : "updated"} project`
    );
    methods.reset();
  };

  return (
    <Dialog>
      <DialogTrigger asChild onClick={(e) => e.stopPropagation()}>
        {trigger}
      </DialogTrigger>
      <DialogContent
        className="max-w-md overflow-x-auto"
        onClick={(e) => e.stopPropagation()}
      >
        <Form {...methods}>
          <form
            onSubmit={methods.handleSubmit(handleSubmit)}
            className="space-y-6"
          >
            <DialogHeader className="flex-shrink-0">
              <DialogTitle>{title}</DialogTitle>
              <DialogDescription>{description}</DialogDescription>
            </DialogHeader>

            <FormField
              control={methods.control}
              name="name"
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
                  type="submit"
                  disabled={methods.formState.isSubmitting}
                  className="w-full"
                >
                  {methods.formState.isSubmitting
                    ? submittingText
                    : submitButtonText}
                </Button>
              </DialogClose>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
};

export const CreateProjectButton = () => {
  const createProject = useCreateProjectMutation();
  const handleCreate = async (data: ProjectFormData) => {
    await createProject.mutateAsync(data);
  };

  return (
    <ProjectForm
      mode="create"
      onSubmit={handleCreate}
      trigger={
        <Button
          variant="ghost"
          size="iconSm"
          className="text-primary hover:text-primary/80 hover:bg-white"
        >
          <PlusCircle />
        </Button>
      }
      title="Create a new project"
      description="Create a new project for your organization."
      submitButtonText="Create Project"
      submittingText="Creating..."
    />
  );
};

export const EditProjectButton = ({
  projectUuid,
  defaultProjectFormData,
}: {
  projectUuid: string;
  defaultProjectFormData: ProjectFormData;
}) => {
  const updateProject = useUpdateProjectMutation();
  const handleEdit = async (data: ProjectFormData) => {
    await updateProject.mutateAsync({
      projectUuid,
      projectUpdate: data,
    });
  };
  return (
    <ProjectForm
      mode="edit"
      initialData={defaultProjectFormData}
      onSubmit={handleEdit}
      trigger={
        <Button variant="outline" size="icon" className="h-8 w-8">
          <PencilLine />
        </Button>
      }
      title="Edit project"
      description="Update your project details."
      submitButtonText="Save Changes"
      submittingText="Saving..."
    />
  );
};

export default ProjectForm;
