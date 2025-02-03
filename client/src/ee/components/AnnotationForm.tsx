import { FailButton } from "@/components/FailButton";
import { SuccessButton } from "@/components/SuccessButton";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { DropdownMenuItem } from "@/components/ui/dropdown-menu";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
} from "@/components/ui/form";
import { Textarea } from "@/components/ui/textarea";
import {
  useCreateAnnotationsMutation,
  useUpdateAnnotationMutation,
} from "@/ee/utils/annotations";
import { useToast } from "@/hooks/use-toast";
import {
  AnnotationCreate,
  AnnotationPublic,
  AnnotationUpdate,
  Label,
  SpanPublic,
} from "@/types/types";
import { userQueryOptions } from "@/utils/users";
import { useSuspenseQuery } from "@tanstack/react-query";
import { MessageSquareText } from "lucide-react";
import { Dispatch, SetStateAction, useState } from "react";
import { Path, SubmitHandler, useForm, UseFormReturn } from "react-hook-form";
interface BaseAnnotation {
  label?: Label | null;
  reasoning?: string | null;
}

interface AnnotationFormFieldsProps<T extends BaseAnnotation> {
  methods: UseFormReturn<T>;
  submitButtonText: string;
  isSubmitting: boolean;
  onSubmit: SubmitHandler<T>;
  setOpen: Dispatch<SetStateAction<boolean>>;
}

const AnnotationFormFields = <T extends BaseAnnotation>({
  methods,
  submitButtonText,
  isSubmitting,
  onSubmit,
  setOpen,
}: AnnotationFormFieldsProps<T>) => {
  return (
    <Form {...methods}>
      <form
        className='flex flex-col gap-2'
        onSubmit={methods.handleSubmit(onSubmit)}
      >
        <FormField
          key='label'
          control={methods.control}
          name={"label" as Path<T>}
          rules={{
            required: "Label is required",
          }}
          render={({ field }) => (
            <FormItem>
              <FormLabel>Label</FormLabel>
              <FormControl>
                <div className='flex gap-4'>
                  <SuccessButton
                    onClick={() => field.onChange(Label.PASS)}
                    variant={field.value === Label.PASS ? "success" : "outline"}
                  >
                    Pass
                  </SuccessButton>
                  <FailButton
                    onClick={() => field.onChange(Label.FAIL)}
                    variant={
                      field.value === Label.FAIL ? "destructive" : "outline"
                    }
                  >
                    Fail
                  </FailButton>
                </div>
              </FormControl>
            </FormItem>
          )}
        />
        <FormField
          key='reasoning'
          control={methods.control}
          name={"reasoning" as Path<T>}
          render={({ field }) => (
            <FormItem>
              <FormLabel>Reason</FormLabel>
              <FormControl>
                <Textarea
                  placeholder='(Optional) Reason for label'
                  {...field}
                  value={field.value || ""}
                />
              </FormControl>
            </FormItem>
          )}
        />
        <DialogClose
          asChild
          onClick={async (e) => {
            e.preventDefault();
            if (await methods.trigger()) {
              setOpen(false);
            }
          }}
        >
          <Button type='submit' loading={isSubmitting} className='w-full'>
            {isSubmitting ? "Staging..." : submitButtonText}
          </Button>
        </DialogClose>
      </form>
    </Form>
  );
};

export const CreateAnnotationDialog = ({ span }: { span: SpanPublic }) => {
  const [open, setOpen] = useState<boolean>(false);
  const methods = useForm<AnnotationCreate>({
    defaultValues: {
      reasoning: "",
    },
  });
  const { toast } = useToast();
  const { data: user } = useSuspenseQuery(userQueryOptions());
  const createAnnotation = useCreateAnnotationsMutation();
  const onSubmit = async (data: AnnotationCreate) => {
    data.span_uuid = span.uuid;
    data.assigned_to = user.uuid;
    try {
      await createAnnotation.mutateAsync({
        projectUuid: span.project_uuid,
        annotationsCreate: [data],
      });
      toast({
        title: "Annotation created",
      });
    } catch (e) {
      toast({
        title: "Failed to create annotation",
        variant: "destructive",
      });
    }
  };
  return (
    <Dialog
      open={open}
      onOpenChange={(open) => {
        methods.reset();
        setOpen(open);
      }}
    >
      <DialogTrigger asChild>
        <DropdownMenuItem
          className='flex items-center gap-2'
          onSelect={(e) => e.preventDefault()}
        >
          <MessageSquareText className='w-4 h-4' />
          <span className='font-medium'>Annotate</span>
        </DropdownMenuItem>
      </DialogTrigger>
      <DialogContent className={"max-w-[425px] overflow-x-auto"}>
        <DialogTitle>{`Annotate`}</DialogTitle>
        <DialogDescription>
          {`Annotate this trace to add to your dataset.`}
        </DialogDescription>
        <AnnotationFormFields<AnnotationCreate>
          methods={methods}
          submitButtonText='Annotate'
          isSubmitting={methods.formState.isSubmitting}
          onSubmit={onSubmit}
          setOpen={setOpen}
        />
      </DialogContent>
    </Dialog>
  );
};

// Update Form Component
export const UpdateAnnotationForm = ({
  span,
  annotation,
}: {
  span: SpanPublic;
  annotation: AnnotationPublic;
}) => {
  const methods = useForm<AnnotationUpdate>({
    defaultValues: {
      reasoning: annotation.reasoning || "",
      label: annotation.label,
    },
  });
  const [open, setOpen] = useState<boolean>(false);
  const { toast } = useToast();
  const updateAnnotation = useUpdateAnnotationMutation();

  const onSubmit = async (data: AnnotationUpdate) => {
    const res = await updateAnnotation.mutateAsync({
      projectUuid: span.project_uuid,
      annotationUuid: annotation.uuid,
      annotationUpdate: data,
    });
    if (res) {
      toast({
        title: "Annotation updated",
      });
    } else {
      toast({
        title: "Failed to update annotation",
        variant: "destructive",
      });
    }
  };

  return (
    <AnnotationFormFields<AnnotationUpdate>
      methods={methods}
      submitButtonText='Update'
      isSubmitting={methods.formState.isSubmitting}
      onSubmit={onSubmit}
      setOpen={setOpen}
    />
  );
};
