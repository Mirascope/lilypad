import { AddComment, CommentCards } from "@/components/Comment";
import { LilypadPanel } from "@/components/LilypadPanel";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { AnnotationsTable } from "@/ee/components/AnnotationsTable";
import { SpanPublic } from "@/types/types";
import { commentsBySpanQueryOptions } from "@/utils/comments";
import { useSuspenseQuery } from "@tanstack/react-query";
import { useNavigate } from "@tanstack/react-router";
import { MessageSquareMore, NotebookPen } from "lucide-react";
import { useEffect, useState } from "react";
import { toast } from "sonner";
export const TraceMoreDetails = ({
  data,
  path,
}: {
  data: SpanPublic;
  path?: string;
}) => {
  const navigate = useNavigate();
  const [showComments, setShowComments] = useState(false);
  const [showAnnotations, setShowAnnotations] = useState<boolean>(false);
  const { data: spanComments } = useSuspenseQuery(
    commentsBySpanQueryOptions(data.uuid)
  );
  useEffect(() => {
    if (path) {
      navigate({
        to: path,
        replace: true,
        params: { _splat: data.uuid },
      }).catch(() => {
        toast.error("Failed to navigate");
      });
    }
  }, [data, navigate, path]);

  const filteredAnnotations = data.annotations.filter(
    (annotation) => annotation.label
  );
  return (
    <div className="flex flex-col gap-2 h-full max-h-screen overflow-hidden">
      <div className="flex justify-end gap-2 p-2 shrink-0">
        <Button
          size="icon"
          className="h-8 w-8 relative"
          variant="outline"
          onClick={() => setShowComments(!showComments)}
        >
          <MessageSquareMore />
          {spanComments.length > 0 && (
            <div className="absolute -top-2 -right-2 bg-primary text-primary-foreground text-xs rounded-full h-5 w-5 flex items-center justify-center font-medium">
              {spanComments.length > 9 ? "9+" : spanComments.length}
            </div>
          )}
        </Button>
        <Button
          size="icon"
          className="h-8 w-8 relative"
          variant="outline"
          onClick={() => setShowAnnotations(!showAnnotations)}
        >
          <NotebookPen />
          {filteredAnnotations.length > 0 && (
            <div className="absolute -top-2 -right-2 bg-primary text-primary-foreground text-xs rounded-full h-5 w-5 flex items-center justify-center font-medium">
              {filteredAnnotations.length > 9
                ? "9+"
                : filteredAnnotations.length}
            </div>
          )}
        </Button>
      </div>

      <div className="flex-1 overflow-auto pb-4">
        {/* Comments section with max height and scrolling */}
        {showComments && (
          <div className="mb-4">
            <div className="max-h-64 overflow-y-auto mb-4">
              <CommentCards spanUuid={data.uuid} />
            </div>
            <Separator />
            <div className="mt-4">
              <AddComment spanUuid={data.uuid} />
            </div>
          </div>
        )}

        {/* Annotations section with max height and scrolling */}
        {showAnnotations && (
          <div className="mb-4 max-h-64 overflow-y-auto">
            <AnnotationsTable data={filteredAnnotations} />
          </div>
        )}

        <LilypadPanel spanUuid={data.uuid} />
      </div>
      <Button>Open in full page</Button>
    </div>
  );
};
