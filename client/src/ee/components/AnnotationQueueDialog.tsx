import IconDialog from "@/components/IconDialog";
import { UpdateAnnotationForm } from "@/ee/components/AnnotationForm";
import { AnnotationPublic } from "@/types/types";
import { useState } from "react";

export const AnnotationQueueDialog = ({
  unannotatedRows,
}: {
  unannotatedRows: AnnotationPublic[];
}) => {
  const [open, setOpen] = useState<boolean>(false);
  const onComplete = (isLastItem: boolean) => {
    if (isLastItem) {
      return;
    }
  };
  return (
    <IconDialog
      open={open}
      onOpenChange={setOpen}
      text={"Start Annotating"}
      title={"Annotate selected traces"}
      description={`${unannotatedRows.length} annotation(s) remaining.`}
      tooltipContent={"Add annotations to your dataset."}
      buttonProps={{
        variant: "default",
        disabled: unannotatedRows.length === 0,
      }}
      dialogContentProps={{
        className: "max-w-[800px] h-screen overflow-y-auto",
      }}
    >
      <UpdateAnnotationForm
        setOpen={setOpen}
        annotation={unannotatedRows[0]}
        total={unannotatedRows.length}
        onComplete={onComplete}
      />
    </IconDialog>
  );
};
