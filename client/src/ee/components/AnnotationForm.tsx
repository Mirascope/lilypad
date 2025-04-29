import CardSkeleton from "@/components/CardSkeleton";
import { FailButton } from "@/components/FailButton";
import { SuccessButton } from "@/components/SuccessButton";
import { Button } from "@/components/ui/button";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Textarea } from "@/components/ui/textarea";
import {
  useDeleteAnnotationMutation,
  useUpdateAnnotationMutation,
} from "@/ee/utils/annotations";
import { AnnotationPublic, AnnotationUpdate, Label } from "@/types/types";
import { userQueryOptions } from "@/utils/users";
import { useSuspenseQuery } from "@tanstack/react-query";
import { Suspense } from "react";
import {
  SubmitHandler,
  useForm,
  useFormContext,
  UseFormReturn,
} from "react-hook-form";
import { toast } from "sonner";
interface BaseAnnotation {
  data?: Record<string, any> | null;
}

interface AnnotationFormFieldsProps<T extends BaseAnnotation> {
  spanUuid: string;
  methods: UseFormReturn<T>;
  onSubmit: SubmitHandler<T>;
  renderButtons: () => React.ReactNode;
}

export const AnnotationFormFields = <T extends BaseAnnotation>({
  methods,
  onSubmit,
  renderButtons,
}: AnnotationFormFieldsProps<T>) => {
  return (
    <Form {...methods}>
      <form
        className="flex flex-col gap-2"
        onSubmit={methods.handleSubmit(onSubmit)}
      >
        <Suspense fallback={<CardSkeleton />}>
          <AnnotationFields />
        </Suspense>
        {renderButtons()}
      </form>
    </Form>
  );
};

const AnnotationFields = () => {
  const methods = useFormContext<AnnotationUpdate>();
  return (
    <>
      <FormField
        key="label"
        control={methods.control}
        rules={{
          validate: (value) => {
            if (value === null) {
              return "Label is required";
            }
            return true;
          },
        }}
        name="label"
        render={({ field }) => {
          return (
            <FormItem>
              <FormLabel>Label</FormLabel>
              <FormControl>
                <div className="flex gap-2">
                  <SuccessButton
                    variant={field.value === Label.PASS ? "success" : "outline"}
                    onClick={() => field.onChange(Label.PASS)}
                  >
                    Pass
                  </SuccessButton>
                  <FailButton
                    variant={
                      field.value === Label.FAIL ? "destructive" : "outline"
                    }
                    onClick={() => field.onChange(Label.FAIL)}
                  >
                    Fail
                  </FailButton>
                </div>
              </FormControl>
              <FormMessage />
            </FormItem>
          );
        }}
      />
      <FormField
        key="reasoning"
        control={methods.control}
        name="reasoning"
        render={({ field }) => {
          return (
            <FormItem>
              <FormLabel>Reasoning (Optional)</FormLabel>
              <FormControl>
                <Textarea {...field} value={field.value ?? ""} />
              </FormControl>
            </FormItem>
          );
        }}
      />
    </>
  );
};

export const UpdateAnnotationForm = ({
  annotation,
  spanUuid,
  onSubmit,
}: {
  annotation: AnnotationPublic;
  spanUuid: string;
  onSubmit: () => void;
}) => {
  const { data: user } = useSuspenseQuery(userQueryOptions());
  const methods = useForm<AnnotationUpdate>({
    defaultValues: {
      reasoning: annotation.reasoning ?? "",
      label: annotation.label,
      data: annotation.data,
    },
  });
  const updateAnnotation = useUpdateAnnotationMutation();
  const deleteAnnotation = useDeleteAnnotationMutation();
  const isLoading = methods.formState.isSubmitting;
  const renderButtons = () => {
    return (
      <div className="flex justify-between gap-2">
        <Button type="submit" loading={isLoading}>
          {isLoading ? "Annotating..." : "Annotate"}
        </Button>
        <Button
          type="button"
          variant="outlineDestructive"
          onClick={() => {
            deleteAnnotation
              .mutateAsync({
                projectUuid: annotation.project_uuid,
                annotationUuid: annotation.uuid,
              })
              .catch(() => toast.error("Failed to delete annotation"));
            toast.success("Annotation deleted");
            onSubmit();
          }}
        >
          {isLoading ? "Deleting..." : "Remove Annotation"}
        </Button>
      </div>
    );
  };
  const handleSubmit = async (data: AnnotationUpdate) => {
    data.assigned_to = user.uuid;
    if (!annotation.project_uuid || !annotation.uuid) {
      toast.error("Failed to update annotation.");
      return;
    }
    await updateAnnotation
      .mutateAsync({
        projectUuid: annotation.project_uuid,
        annotationUuid: annotation.uuid,
        annotationUpdate: data,
      })
      .catch(() => {
        toast.error("Failed to update annotation");
      });
    toast.success("Annotation submitted");
    methods.reset();
    onSubmit();
  };

  return (
    <AnnotationFormFields<AnnotationUpdate>
      spanUuid={spanUuid}
      methods={methods}
      onSubmit={handleSubmit}
      renderButtons={renderButtons}
    />
  );
};
