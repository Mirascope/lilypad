import { FormCombobox } from "@/src/components/FormCombobox";
import { Button } from "@/src/components/ui/button";
import { DialogClose, DialogFooter } from "@/src/components/ui/dialog";
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
} from "@/src/components/ui/form";
import { useCreateAnnotationsMutation } from "@/src/ee/utils/annotations";
import { AnnotationCreate, SpanMoreDetails, SpanPublic } from "@/src/types/types";
import { usersByOrganizationQueryOptions } from "@/src/utils/users";
import { useSuspenseQuery } from "@tanstack/react-query";
import { useForm, useFormContext } from "react-hook-form";
import { toast } from "sonner";
export const QueueForm = ({ spans }: { spans: SpanPublic[] | SpanMoreDetails[] }) => {
  const { data: users } = useSuspenseQuery(usersByOrganizationQueryOptions());
  const methods = useForm<AnnotationCreate>();
  const createAnnotation = useCreateAnnotationsMutation();
  const onSubmit = async (data: AnnotationCreate) => {
    const mappedUsers = users.reduce(
      (acc, user) => ({
        ...acc,
        [user.uuid]: user.first_name,
      }),
      {} as Record<string, string>
    );
    const assignedToNames = data.assigned_to?.map((assignedTo) => mappedUsers[assignedTo]);
    const annotationsCreate: AnnotationCreate[] = spans.map((span) => ({
      ...data,
      span_uuid: span.uuid,
      function_uuid: span.function_uuid,
    }));
    await createAnnotation
      .mutateAsync({
        projectUuid: spans[0].project_uuid,
        annotationsCreate,
      })
      .catch(() => toast.error("Failed to assign annotation"));
    if (!assignedToNames) {
      toast.success("Annotation created");
    } else {
      const assignedToNamesStr = assignedToNames.join(", ");
      toast.success(`Annotation created for ${assignedToNamesStr}`);
    }
  };
  return (
    <Form {...methods}>
      <form className="flex flex-col gap-2" onSubmit={methods.handleSubmit(onSubmit)}>
        <SelectUsers />
        <DialogFooter>
          <DialogClose asChild>
            <Button type="submit" loading={methods.formState.isSubmitting}>
              {methods.formState.isSubmitting ? "Adding to queue..." : "Add to queue"}
            </Button>
          </DialogClose>
          <DialogClose asChild>
            <Button type="button" variant="outline" loading={methods.formState.isSubmitting}>
              Cancel
            </Button>
          </DialogClose>
        </DialogFooter>
      </form>
    </Form>
  );
};

export const SelectUsers = () => {
  const { data: users } = useSuspenseQuery(usersByOrganizationQueryOptions());
  const methods = useFormContext<AnnotationCreate>();
  return (
    <FormField
      key="assignedTo"
      control={methods.control}
      name={"assigned_to"}
      render={() => (
        <FormItem>
          <FormLabel className="flex items-center gap-2">Assign To</FormLabel>
          <FormDescription>Leave empty to allow anyone to annotate</FormDescription>
          <FormControl>
            <FormCombobox<AnnotationCreate>
              items={users.map((user) => ({
                value: user.uuid,
                label: user.first_name,
              }))}
              disableAdd
              popoverText="Select users..."
              emptyText="No user found."
              control={methods.control}
              name={"assigned_to"}
              helperText="Assign users"
            />
          </FormControl>
        </FormItem>
      )}
    />
  );
};
