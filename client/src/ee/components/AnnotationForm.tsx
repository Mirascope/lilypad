import CardSkeleton from "@/components/CardSkeleton";
import LilypadDialog from "@/components/LilypadDialog";
import { LilypadPanel } from "@/components/LilypadPanel";
import { Button } from "@/components/ui/button";
import { DropdownMenuItem } from "@/components/ui/dropdown-menu";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { labelNodeDefinition } from "@/ee/components/LabelNode";
import {
  AnnotationCreate,
  AnnotationPublic,
  AnnotationUpdate,
} from "@/ee/types/types";
import {
  useCreateAnnotationsMutation,
  useUpdateAnnotationMutation,
} from "@/ee/utils/annotations";
import { useToast } from "@/hooks/use-toast";
import { Label } from "@/types/types";
import { spanQueryOptions } from "@/utils/spans";
import { safelyParseJSON } from "@/utils/strings";
import { userQueryOptions } from "@/utils/users";
import { useSuspenseQuery } from "@tanstack/react-query";
import { JsonData, JsonEditor } from "json-edit-react";
import { MessageSquareText } from "lucide-react";
import { Dispatch, SetStateAction, Suspense, useState } from "react";
import {
  SubmitHandler,
  useForm,
  useFormContext,
  UseFormReturn,
} from "react-hook-form";
interface BaseAnnotation {
  label?: Label | null;
  reasoning?: string | null;
  data?: Record<string, any> | null;
}

interface AnnotationFormFieldsProps<T extends BaseAnnotation> {
  spanUuid: string;
  methods: UseFormReturn<T>;
  onSubmit: SubmitHandler<T>;
  renderButtons: () => React.ReactNode;
}

const AnnotationFormFields = <T extends BaseAnnotation>({
  spanUuid,
  methods,
  onSubmit,
  renderButtons,
}: AnnotationFormFieldsProps<T>) => {
  return (
    <>
      <Suspense fallback={<CardSkeleton />}>
        <LilypadPanel
          spanUuid={spanUuid}
          showJsonArgs
          dataProps={{ collapsed: true }}
        />
      </Suspense>
      <Form {...methods}>
        <form
          className='flex flex-col gap-2'
          onSubmit={methods.handleSubmit(onSubmit)}
        >
          <Suspense fallback={<CardSkeleton />}>
            <AnnotationFields spanUuid={spanUuid} />
          </Suspense>
          {renderButtons()}
        </form>
      </Form>
    </>
  );
};

const AnnotationFields = ({ spanUuid }: { spanUuid: string }) => {
  const { data: span } = useSuspenseQuery(spanQueryOptions(spanUuid));
  const output = safelyParseJSON(span.output ?? "") || span.output;
  const methods = useFormContext<AnnotationCreate>();
  return (
    <FormField
      key='data'
      control={methods.control}
      rules={{
        validate: (value) => {
          if (!value) {
            return "Annotation is required";
          }
          if (Object.values(value).some((val) => val.label === null)) {
            return "All fields must be annotated with a label";
          }
          return true;
        },
      }}
      name='data'
      render={({ field }) => (
        <FormItem>
          <FormLabel>Annotation</FormLabel>
          <FormControl>
            <JsonEditor
              data={field.value as JsonData}
              rootName=''
              restrictEdit={({ key, parentData }) => {
                if (
                  (parentData as { exact: boolean })?.exact === true &&
                  key === "label"
                ) {
                  return true;
                }
                return false;
              }}
              restrictDelete={({ key }) => {
                if (
                  ["label", "exact", "reasoning", "idealOutput"].includes(
                    key as string
                  )
                ) {
                  return true;
                }
                return false;
              }}
              restrictTypeSelection={({ key }) => {
                if (["label", "exact", "reasoning"].includes(key as string)) {
                  return true;
                }
                return false;
              }}
              onUpdate={({ newData }) => {
                field.onChange(newData);
              }}
              onEdit={({ newValue, name, currentData, newData, path }) => {
                if (["exact", "idealOutput"].includes(name as string)) {
                  // Get the parent object that contains both exact and idealOutput
                  const parentPath = path.slice(0, -1);
                  const parentObj = parentPath.reduce(
                    (obj, key) => (obj as any)[key],
                    currentData
                  );
                  const originalOutput = parentPath.reduce(
                    (obj, key) => (obj as Record<string, any>)?.[key],
                    output
                  );

                  // Check conditions based on which field is being edited
                  const shouldUpdateLabelToPass =
                    (name === "exact" &&
                      newValue === true &&
                      (parentObj as { idealOutput: any }).idealOutput ===
                        originalOutput) ||
                    (name === "idealOutput" &&
                      (parentObj as { exact: boolean }).exact === true &&
                      newValue === originalOutput);

                  const shouldUpdateLabelToFail =
                    (name === "exact" &&
                      newValue === true &&
                      (parentObj as { idealOutput: any }).idealOutput !==
                        originalOutput) ||
                    (name === "idealOutput" &&
                      (parentObj as { exact: boolean }).exact === true &&
                      newValue !== originalOutput);

                  if (shouldUpdateLabelToPass || shouldUpdateLabelToFail) {
                    // Create a new data object with the updated label
                    const labelPath = [...parentPath, "label"];
                    let current = newData;
                    // iterate through the path except for the last key
                    for (let i = 0; i < labelPath.length - 1; i++) {
                      if (
                        !(current as Record<string, JsonData>)[labelPath[i]]
                      ) {
                        (current as Record<string, JsonData>)[labelPath[i]] =
                          {};
                      }
                      current = (current as Record<string, JsonData>)[
                        labelPath[i]
                      ];
                    }
                    // set the value at the final key based on the condition
                    (current as Record<string, JsonData>)[
                      labelPath[labelPath.length - 1]
                    ] = shouldUpdateLabelToPass ? Label.PASS : Label.FAIL;
                    field.onChange(newData);
                    return ["value", newData];
                  }
                }
                field.onChange(newData);
                return true;
              }}
              customNodeDefinitions={[labelNodeDefinition]}
            />
          </FormControl>
          <FormMessage />
        </FormItem>
      )}
    />
  );
};
export const CreateAnnotationDialog = ({ spanUuid }: { spanUuid: string }) => {
  const { data: span } = useSuspenseQuery(spanQueryOptions(spanUuid));
  const [open, setOpen] = useState<boolean>(false);
  const output = safelyParseJSON(span.output ?? "") || span.output;
  const jsonOutput = typeof output === "string" ? { output } : output;
  const transformedOutput = Object.entries(jsonOutput ?? {}).reduce<
    Record<string, any>
  >((acc, [key, value]) => {
    acc[key] = {
      idealOutput: value,
      reasoning: "",
      exact: false,
      label: null,
    };
    return acc;
  }, {});
  const methods = useForm<AnnotationCreate>({
    defaultValues: {
      data: transformedOutput,
    },
  });
  const { toast } = useToast();
  const { data: user } = useSuspenseQuery(userQueryOptions());
  const createAnnotation = useCreateAnnotationsMutation();
  const isLoading = methods.formState.isSubmitting;
  const renderButtons = () => {
    return (
      <Button type='submit' loading={isLoading}>
        {isLoading ? "Adding annotation..." : "Annotate"}
      </Button>
    );
  };
  const onSubmit = async (data: AnnotationCreate) => {
    data.span_uuid = span.uuid;
    data.assigned_to = [user.uuid];
    data.generation_uuid = span.generation_uuid;
    if (data.data) {
      const values = Object.values(data.data);
      data.label = values.every((value) => value.label === Label.PASS)
        ? Label.PASS
        : Label.FAIL;
    }
    if (!span.project_uuid) {
      toast({
        title: "Failed to create annotation, unknown project",
        variant: "destructive",
      });
      return;
    }
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
    setOpen(false);
  };
  return (
    <LilypadDialog
      open={open}
      onOpenChange={(open) => {
        methods.reset();
        setOpen(open);
      }}
      customTrigger={
        <DropdownMenuItem
          className='flex items-center gap-2'
          onSelect={(e) => e.preventDefault()}
        >
          <MessageSquareText className='w-4 h-4' />
          <span className='font-medium'>Annotate</span>
        </DropdownMenuItem>
      }
      text={"Start Annotating"}
      title={"Annotate trace"}
      description={`Annotate this trace to add to your dataset.`}
      buttonProps={{
        variant: "default",
      }}
      dialogContentProps={{
        className: "max-w-[800px] max-h-screen overflow-y-auto",
        onEscapeKeyDown: (e) => e.preventDefault(),
        onPointerDownOutside: (e) => e.preventDefault(),
      }}
    >
      <AnnotationFormFields<AnnotationCreate>
        spanUuid={span.uuid}
        methods={methods}
        onSubmit={onSubmit}
        renderButtons={renderButtons}
      />
    </LilypadDialog>
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
  const { data: span } = useSuspenseQuery(
    spanQueryOptions(annotation.span.uuid)
  );
  const { data: user } = useSuspenseQuery(userQueryOptions());
  const output = safelyParseJSON(span.output ?? "") || span.output;
  const jsonOutput = typeof output === "string" ? { output } : output;
  const transformedOutput = Object.entries(jsonOutput ?? {}).reduce<
    Record<string, any>
  >((acc, [key, value]) => {
    acc[key] = {
      idealOutput: value,
      reasoning: "",
      exact: false,
      label: null,
    };
    return acc;
  }, {});
  const methods = useForm<AnnotationUpdate>({
    defaultValues: {
      reasoning: annotation.reasoning || "",
      label: annotation.label,
      data: transformedOutput,
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
    if (data.data) {
      const values = Object.values(data.data);
      data.label = values.every((value) => value.label === Label.PASS)
        ? Label.PASS
        : Label.FAIL;
    }
    data.assigned_to = user.uuid;
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
      spanUuid={annotation.span.uuid}
      methods={methods}
      onSubmit={onSubmit}
      renderButtons={renderButtons}
    />
  );
};
