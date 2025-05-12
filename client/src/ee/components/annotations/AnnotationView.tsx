import { UpdateAnnotationForm } from "@/ee/components/AnnotationForm";
import { AnnotationPublic } from "@/types/types";
import { useNavigate } from "@tanstack/react-router";
import { useEffect } from "react";
import { toast } from "sonner";

export const AnnotationView = ({
  annotation,
  path,
}: {
  annotation: AnnotationPublic;
  path?: string;
}) => {
  const navigate = useNavigate();
  useEffect(() => {
    if (path) {
      navigate({
        to: path,
        replace: true,
        params: { _splat: annotation.uuid },
      }).catch(() => {
        toast.error("Failed to navigate");
      });
    }
  }, [annotation, navigate, path]);
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
    <div className="shrink-0 p-2">
      <UpdateAnnotationForm
        annotation={annotation}
        spanUuid={annotation.span_uuid}
        onSubmit={handleSubmit}
      />
    </div>
  );
};
