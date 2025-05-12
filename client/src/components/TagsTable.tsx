import { DataTable } from "@/components/DataTable";
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
  FormDescription,
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
import { TagPublic } from "@/types/types";
import { projectsQueryOptions } from "@/utils/projects";
import { formatDate } from "@/utils/strings";
import {
  tagsQueryOptions,
  useCreateTagMutation,
  useDeleteTagMutation,
  useUpdateTagMutation,
} from "@/utils/tags";
import { useSuspenseQuery } from "@tanstack/react-query";
import { useNavigate } from "@tanstack/react-router";
import { ColumnDef } from "@tanstack/react-table";
import { PencilLine, Trash, TriangleAlert } from "lucide-react";
import { useRef } from "react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";

export const TagsTable = () => {
  const virtualizerRef = useRef<HTMLDivElement>(null);
  const { data } = useSuspenseQuery(tagsQueryOptions());
  const { data: projects } = useSuspenseQuery(projectsQueryOptions());
  const projectsMap = projects.reduce(
    (acc, key) => {
      acc[key.uuid] = key.name;
      return acc;
    },
    {} as Record<string, string>
  );
  const columns: ColumnDef<TagPublic>[] = [
    {
      accessorKey: "name",
      header: "Name",
    },
    {
      accessorKey: "project_uuid",
      header: "Project ID",
      cell: ({ row }) => {
        const projectUuid: string = row.getValue("project_uuid");
        const projectName = projectsMap[projectUuid];
        return <div>{projectName || "-"}</div>;
      },
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
          <div className="flex gap-1">
            <EditTagButton
              tagUuid={row.original.uuid}
              defaultTagFormData={{
                name: row.original.name,
                project_uuid: row.original.project_uuid,
              }}
            />
            <DeleteTagButton tag={row.original} />
          </div>
        );
      },
    },
  ];

  return (
    <div className="flex flex-col gap-1">
      <div>
        <CreateTagButton />
      </div>
      <DataTable<TagPublic>
        columns={columns}
        data={data}
        virtualizerRef={virtualizerRef}
        virtualizerOptions={{
          count: data.length,
          estimateSize: () => 45,
          overscan: 5,
        }}
        hideColumnButton
      />
    </div>
  );
};

interface DeleteTagFormValues {
  tagName: string;
}

const DeleteTagButton = ({ tag }: { tag: TagPublic }) => {
  const methods = useForm<DeleteTagFormValues>({
    defaultValues: {
      tagName: "",
    },
  });
  const deleteTag = useDeleteTagMutation();
  const navigate = useNavigate();

  const onSubmit = async () => {
    await deleteTag.mutateAsync(tag.uuid).catch(() => {
      toast.error("Failed to delete tag");
      return;
    });
    toast.success("Successfully deleted tag");
    navigate({
      to: "/settings/$",
      params: { _splat: "tags" },
    }).catch(() => {
      toast.error("Failed to navigate after deletion.");
    });
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
            <DialogHeader className="shrink-0">
              <DialogTitle>{`Delete ${tag.name}`}</DialogTitle>
            </DialogHeader>
            <DialogDescription>
              {`Deleting ${tag.name} will remove this tag from all associated resources.`}
            </DialogDescription>
            <Alert variant="destructive">
              <TriangleAlert className="h-4 w-4 " />
              <div className="flex flex-col gap-2">
                <AlertTitle>WARNING</AlertTitle>
                <AlertDescription>This action is final.</AlertDescription>
              </div>
            </Alert>
            <FormField
              key="tagName"
              control={methods.control}
              name="tagName"
              rules={{
                required: "Tag name is required",
                validate: (value) =>
                  value === tag.name || "Tag name doesn't match",
              }}
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Tag Name</FormLabel>
                  <FormControl>
                    <Input {...field} />
                  </FormControl>
                  <FormDescription>
                    Please type &quot;{tag.name}&quot; to confirm deletion
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
                {methods.formState.isSubmitting ? "Deleting..." : "Delete Tag"}
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
};

interface TagFormData {
  name: string;
  project_uuid?: string | null;
}

interface TagFormProps {
  mode: "create" | "edit";
  initialData?: TagFormData;
  onSubmit: (data: TagFormData) => Promise<void>;
  trigger: React.ReactNode;
  title: string;
  description: string;
  submitButtonText: string;
  submittingText: string;
}

const TagForm = ({
  mode,
  initialData,
  onSubmit,
  trigger,
  title,
  description,
  submitButtonText,
  submittingText,
}: TagFormProps) => {
  const methods = useForm<TagFormData>({
    defaultValues: initialData ?? { name: "", project_uuid: null },
  });
  const { data: projects } = useSuspenseQuery(projectsQueryOptions());

  const handleSubmit = async (data: TagFormData) => {
    try {
      await onSubmit(data);
      toast.success(
        `Successfully ${mode === "create" ? "created" : "updated"} tag`
      );
      methods.reset();
    } catch (error) {
      toast.error(`Failed to ${mode === "create" ? "create" : "update"} tag`);
    }
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
            <DialogHeader className="shrink-0">
              <DialogTitle>{title}</DialogTitle>
              <DialogDescription>{description}</DialogDescription>
            </DialogHeader>

            <FormField
              control={methods.control}
              name="name"
              rules={{ required: "Tag name is required", minLength: 1 }}
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
              control={methods.control}
              name="project_uuid"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Project (Optional)</FormLabel>
                  <FormControl>
                    <Select
                      value={field.value ?? ""}
                      onValueChange={(value) =>
                        field.onChange(value === "<none>" ? null : value)
                      }
                    >
                      <SelectTrigger className="w-full">
                        <SelectValue placeholder="Select a project" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="<none>">None</SelectItem>
                        {projects.map((project) => (
                          <SelectItem key={project.uuid} value={project.uuid}>
                            {project.name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </FormControl>
                  <FormDescription>
                    Associate this tag with a project
                  </FormDescription>
                  <FormMessage />
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

export const CreateTagButton = () => {
  const createTag = useCreateTagMutation();
  const handleCreate = async (data: TagFormData) => {
    await createTag.mutateAsync(data);
  };

  return (
    <TagForm
      mode="create"
      onSubmit={handleCreate}
      trigger={<Button>Create Tag</Button>}
      title="Create a new tag"
      description="Create a new tag to organize your resources."
      submitButtonText="Create Tag"
      submittingText="Creating..."
    />
  );
};

export const EditTagButton = ({
  tagUuid,
  defaultTagFormData,
}: {
  tagUuid: string;
  defaultTagFormData: TagFormData;
}) => {
  const updateTag = useUpdateTagMutation();
  const handleEdit = async (data: TagFormData) => {
    await updateTag.mutateAsync({
      tagUuid,
      tagUpdate: data,
    });
  };
  return (
    <TagForm
      mode="edit"
      initialData={defaultTagFormData}
      onSubmit={handleEdit}
      trigger={
        <Button variant="outline" size="icon" className="h-8 w-8">
          <PencilLine />
        </Button>
      }
      title="Edit tag"
      description="Update your tag details."
      submitButtonText="Save Changes"
      submittingText="Saving..."
    />
  );
};

export default TagForm;
