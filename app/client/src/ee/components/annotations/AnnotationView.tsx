import { UpdateAnnotationForm } from "@/src/ee/components/AnnotationForm";
import { AnnotationPublic } from "@/src/types/types";
import { useNavigate } from "@tanstack/react-router";
import { toast } from "sonner";

export const AnnotationView = ({
  annotation,
  path,
}: {
  annotation: AnnotationPublic;
  path?: string;
}) => {
  const navigate = useNavigate();
  const handleSubmit = () => {
    if (path) {
      navigate({
        to: path,
        replace: true,
        params: { _splat: "next" },
      }).catch(() => {
        toast.error("Failed to navigate");
      });
    }
  };
  return (
    <div className="shrink-0">
      <UpdateAnnotationForm
        annotation={annotation}
        spanUuid={annotation.span_uuid}
        onSubmit={handleSubmit}
      />
    </div>
  );
};
