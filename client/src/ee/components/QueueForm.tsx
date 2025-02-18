import CardSkeleton from "@/components/CardSkeleton";
import { FormCombobox } from "@/components/FormCombobox";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { DropdownMenuItem } from "@/components/ui/dropdown-menu";
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
} from "@/components/ui/form";
import { AnnotationCreate } from "@/ee/types/types";
import { useCreateAnnotationsMutation } from "@/ee/utils/annotations";
import { useToast } from "@/hooks/use-toast";
import { SpanPublic } from "@/types/types";
import { usersByOrganizationQueryOptions } from "@/utils/users";
import { useSuspenseQuery } from "@tanstack/react-query";
import { Users } from "lucide-react";
import { Dispatch, SetStateAction, Suspense, useState } from "react";
import { useForm, useFormContext } from "react-hook-form";

export const QueueDialog = ({ spans }: { spans: SpanPublic[] }) => {
  const [open, setOpen] = useState<boolean>(false);
  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <DropdownMenuItem
          className='flex items-center gap-2'
          onSelect={(e) => e.preventDefault()}
        >
          <Users className='w-4 h-4' />
          <span className='font-medium'>Add to annotation queue</span>
        </DropdownMenuItem>
      </DialogTrigger>
      <DialogContent className={"max-w-[425px] overflow-x-auto"}>
        <DialogTitle>{`Add to queue`}</DialogTitle>
        <DialogDescription>{`Add this trace to your queue.`}</DialogDescription>
        <Suspense fallback={<CardSkeleton items={1} />}>
          <QueueForm spans={spans} setOpen={setOpen} />
        </Suspense>
      </DialogContent>
    </Dialog>
  );
};
interface UserMap {
  [key: string]: string;
}
export const QueueForm = ({
  spans,
  setOpen,
}: {
  spans: SpanPublic[];
  setOpen: Dispatch<SetStateAction<boolean>>;
}) => {
  const { data: users } = useSuspenseQuery(usersByOrganizationQueryOptions());
  const { toast } = useToast();
  const methods = useForm<AnnotationCreate>();
  const createAnnotation = useCreateAnnotationsMutation();
  const onSubmit = async (data: AnnotationCreate) => {
    const mappedUsers: UserMap = users.reduce(
      (acc, user) => ({
        ...acc,
        [user.uuid]: user.first_name,
      }),
      {}
    );
    const assignedToNames = data.assigned_to?.map(
      (assignedTo) => mappedUsers[assignedTo]
    );
    const annotationsCreate: AnnotationCreate[] = spans.map((span) => ({
      ...data,
      span_uuid: span.uuid,
      generation_uuid: span.generation_uuid,
    }));
    try {
      await createAnnotation.mutateAsync({
        projectUuid: spans[0].project_uuid,
        annotationsCreate,
      });
      if (!assignedToNames) {
        toast({
          title: "Annotation created",
        });
      } else {
        const assignedToNamesStr = assignedToNames.join(", ");
        toast({
          title: `Assigned annotation(s) to ${assignedToNamesStr}.`,
        });
      }
      setOpen(false);
    } catch (e: unknown) {
      if (
        e &&
        typeof e === "object" &&
        "response" in e &&
        e.response &&
        typeof e.response === "object" &&
        "data" in e.response &&
        e.response.data &&
        typeof e.response.data === "object" &&
        "detail" in e.response.data &&
        typeof e.response.data.detail === "string"
      ) {
        toast({
          title: `Failed to assign annotation: ${e.response.data.detail}`,
          variant: "destructive",
        });
      } else {
        toast({
          title: "Failed to assign annotation: Unknown error",
          variant: "destructive",
        });
      }
    }
  };
  return (
    <Form {...methods}>
      <form
        className='flex flex-col gap-2'
        onSubmit={methods.handleSubmit(onSubmit)}
      >
        <SelectUsers />
        <Button
          type='submit'
          loading={methods.formState.isSubmitting}
          className='w-full'
        >
          {methods.formState.isSubmitting
            ? "Adding to queue..."
            : "Add to queue"}
        </Button>
      </form>
    </Form>
  );
};

export const SelectUsers = () => {
  const { data: users } = useSuspenseQuery(usersByOrganizationQueryOptions());
  const methods = useFormContext<AnnotationCreate>();
  return (
    <FormField
      key='assignedTo'
      control={methods.control}
      name={"assigned_to"}
      render={() => (
        <FormItem>
          <FormLabel className='flex items-center gap-2'>Assign To</FormLabel>
          <FormDescription>
            Leave empty to allow anyone to annotate
          </FormDescription>
          <FormControl>
            <FormCombobox<AnnotationCreate>
              items={users.map((user) => ({
                value: user.uuid,
                label: user.first_name,
              }))}
              disableAdd
              popoverText='Select users...'
              emptyText='No user found.'
              control={methods.control}
              name={"assigned_to"}
              helperText='Assign users'
            />
          </FormControl>
        </FormItem>
      )}
    />
  );
};
