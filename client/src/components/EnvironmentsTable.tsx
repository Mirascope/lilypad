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
  FormField,
  FormItem,
  FormLabel,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Switch } from "@/components/ui/switch";
import { Textarea } from "@/components/ui/textarea";
import { Typography } from "@/components/ui/typography";
import { useToast } from "@/hooks/use-toast";
import { cn } from "@/lib/utils";
import { EnvironmentCreate, EnvironmentPublic } from "@/types/types";
import {
  environmentsQueryOptions,
  useCreateEnvironmentMutation,
  useDeleteEnvironmentMutation,
} from "@/utils/environments";
import { formatDate } from "@/utils/strings";
import { useSuspenseQuery } from "@tanstack/react-query";
import { ColumnDef } from "@tanstack/react-table";
import { PlusCircle, Trash } from "lucide-react";
import { useRef } from "react";
import { useForm } from "react-hook-form";

export const EnvironmentsTable = () => {
  const virtualizerRef = useRef<HTMLDivElement>(null);
  const { data } = useSuspenseQuery(environmentsQueryOptions());
  const columns: ColumnDef<EnvironmentPublic>[] = [
    {
      accessorKey: "name",
      header: "Name",
    },
    {
      accessorKey: "description",
      header: "Description",
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
        return <DeleteEnvironmentButton environment={row.original} />;
      },
    },
  ];

  return (
    <>
      <div className="flex gap-2 items-center">
        <Typography variant="h4">Environment</Typography>
        <CreateEnvironmentButton />
      </div>
      <DataTable<EnvironmentPublic>
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

const CreateEnvironmentButton = () => {
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
        <CreateEnvironmentForm />
      </DialogContent>
    </Dialog>
  );
};

const CreateEnvironmentForm = () => {
  const { toast } = useToast();
  const methods = useForm<EnvironmentCreate>({
    defaultValues: { name: "", description: "", is_default: false },
  });
  const createEnvironment = useCreateEnvironmentMutation();

  const onSubmit = async (data: EnvironmentCreate) => {
    try {
      await createEnvironment.mutateAsync(data);
      toast({
        title: "Environment created successfully",
      });
      methods.reset();
    } catch (error) {
      toast({
        title: "Failed to create environment",
        variant: "destructive",
      });
    }
  };

  return (
    <Form {...methods}>
      <form onSubmit={methods.handleSubmit(onSubmit)} className="space-y-6">
        <DialogHeader className="flex-shrink-0">
          <DialogTitle>Create new Environment</DialogTitle>
        </DialogHeader>
        <DialogDescription>
          Create an environment for your organization
        </DialogDescription>
        <FormField
          key="name"
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
        <FormField
          key="description"
          control={methods.control}
          name="description"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Description</FormLabel>
              <FormControl>
                <Textarea {...field} value={field.value ?? ""} />
              </FormControl>
            </FormItem>
          )}
        />
        <FormField
          key="is_default"
          control={methods.control}
          name="is_default"
          render={({ field }) => (
            <FormItem className="flex flex-row items-center justify-between rounded-lg border p-3">
              <div className="space-y-0.5">
                <FormLabel>Default Environment</FormLabel>
                <FormDescription>
                  Set as default environment for new API keys
                </FormDescription>
              </div>
              <FormControl>
                <Switch
                  checked={field.value}
                  onCheckedChange={field.onChange}
                />
              </FormControl>
            </FormItem>
          )}
        />
        <DialogFooter>
          <DialogClose asChild>
            <Button type="button" variant="secondary">
              Cancel
            </Button>
          </DialogClose>
          <Button type="submit" loading={methods.formState.isSubmitting}>
            {methods.formState.isSubmitting
              ? "Creating..."
              : "Create Environment"}
          </Button>
        </DialogFooter>
      </form>
    </Form>
  );
};

const DeleteEnvironmentButton = ({
  environment,
}: {
  environment: EnvironmentPublic;
}) => {
  const { toast } = useToast();
  const deleteEnvironment = useDeleteEnvironmentMutation();

  const handleEnvironmentDelete = async (environmentUuid: string) => {
    try {
      await deleteEnvironment.mutateAsync(environmentUuid);
      toast({
        title: "Successfully deleted environment",
      });
    } catch (error) {
      toast({
        title: "Failed to delete environment",
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
          <DialogTitle>{`Delete ${environment.name}`}</DialogTitle>
          <DialogDescription>
            This action is final and cannot be undone.
          </DialogDescription>
          <p>
            {"Are you sure you want to delete "}
            <b>{environment.name}</b>?
          </p>
        </DialogHeader>

        <DialogFooter>
          <Button
            variant="destructive"
            onClick={() => handleEnvironmentDelete(environment.uuid)}
          >
            Delete
          </Button>
          <DialogClose asChild>
            <Button type="button" variant="secondary">
              Cancel
            </Button>
          </DialogClose>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

// Missing FormDescription import
const FormDescription = ({ children }: { children: React.ReactNode }) => (
  <p className="text-sm text-muted-foreground">{children}</p>
);
