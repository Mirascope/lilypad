import { FailButton } from "@/components/FailButton";
import { SuccessButton } from "@/components/SuccessButton";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
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
  SpanMoreDetails,
  SpanPublic,
} from "@/types/types";
import { renderCardOutput } from "@/utils/panel-utils";
import { userQueryOptions } from "@/utils/users";
import { useSuspenseQuery } from "@tanstack/react-query";
import JsonView from "@uiw/react-json-view";
import { MessageSquareText } from "lucide-react";
import { Dispatch, SetStateAction, useState } from "react";
import { Path, SubmitHandler, useForm, UseFormReturn } from "react-hook-form";
interface BaseAnnotation {
  label?: Label | null;
  reasoning?: string | null;
}

interface AnnotationFormFieldsProps<T extends BaseAnnotation> {
  span?: SpanMoreDetails;
  methods: UseFormReturn<T>;
  onSubmit: SubmitHandler<T>;
  renderButtons: () => React.ReactNode;
}

const AnnotationFormFields = <T extends BaseAnnotation>({
  span,
  methods,
  onSubmit,
  renderButtons,
}: AnnotationFormFieldsProps<T>) => {
  return (
    <>
      {span && (
        <>
          {span.arg_values && (
            <Card>
              <CardHeader>
                <CardTitle>{"Input"}</CardTitle>
              </CardHeader>
              <CardContent className='flex flex-col'>
                <JsonView value={span.arg_values} />
              </CardContent>
            </Card>
          )}
          {renderCardOutput(span.output)}
        </>
      )}
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
                      variant={
                        field.value === Label.PASS ? "success" : "outline"
                      }
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
          {renderButtons()}
        </form>
      </Form>
    </>
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
  const isLoading = methods.formState.isSubmitting;
  const renderButtons = () => {
    return (
      <Button type='submit' loading={isLoading} className='w-full'>
        {isLoading ? "Staging..." : "Annotate"}
      </Button>
    );
  };
  const onSubmit = async (data: AnnotationCreate) => {
    data.span_uuid = span.uuid;
    data.assigned_to = user.uuid;
    data.generation_uuid = span.generation_uuid;
    console.log(data);
    try {
      const res = await createAnnotation.mutateAsync({
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
    setOpen(false);
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
          onSubmit={onSubmit}
          renderButtons={renderButtons}
        />
      </DialogContent>
    </Dialog>
  );
};

export const UpdateAnnotationForm = ({
  setOpen,
  annotation,
  total,
  onComplete,
}: {
  setOpen: Dispatch<SetStateAction<boolean>>;
  annotation: AnnotationPublic;
  total: number;
  onComplete: (isLastItem: boolean) => void;
}) => {
  const methods = useForm<AnnotationUpdate>({
    defaultValues: {
      reasoning: annotation.reasoning || "",
      label: annotation.label,
    },
  });
  const { toast } = useToast();
  const isLastItem = total === 1;
  const updateAnnotation = useUpdateAnnotationMutation();
  const isLoading = methods.formState.isSubmitting;
  const renderButtons = () => {
    const buttonText = isLastItem ? "Save & Finish" : "Save & Next";
    return (
      <div className='flex gap-2 w-full'>
        <Button
          type='button'
          variant='outline'
          loading={isLoading}
          onClick={() => setOpen(false)}
          className='flex-1'
        >
          Cancel
        </Button>
        <Button type='submit' loading={isLoading} className='flex-1'>
          {isLoading ? "Saving..." : buttonText}
        </Button>
      </div>
    );
  };
  const onSubmit = async (data: AnnotationUpdate) => {
    const res = await updateAnnotation.mutateAsync({
      projectUuid: annotation.project_uuid,
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
    methods.reset();
    onComplete(isLastItem);
    if (isLastItem) {
      setOpen(false);
    }
  };

  return (
    <AnnotationFormFields<AnnotationUpdate>
      span={annotation.span}
      methods={methods}
      onSubmit={onSubmit}
      renderButtons={renderButtons}
    />
  );
};
