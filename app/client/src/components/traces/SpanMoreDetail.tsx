import { FunctionTitle } from "@/src/components/traces/FunctionTitle";
import { LilypadPanel } from "@/src/components/traces/LilypadPanel";
import { Button } from "@/src/components/ui/button";
import { Typography } from "@/src/components/ui/typography";
import { SpanMoreDetails, SpanPublic } from "@/src/types/types";
import { spanQueryOptions } from "@/src/utils/spans";
import { useSuspenseQuery } from "@tanstack/react-query";
import { useParams } from "@tanstack/react-router";
import { Maximize2 } from "lucide-react";

export const SpanMoreDetail = ({
  data,
  handleFullView,
}: {
  data: SpanPublic;
  handleFullView: (span: SpanMoreDetails) => void;
}) => {
  const { projectUuid } = useParams({ strict: false });
  if (!projectUuid) {
    throw new Error("LilypadPanel requires an active project");
  }
  const { data: span } = useSuspenseQuery(spanQueryOptions(projectUuid, data.uuid));

  if (!span.project_uuid) {
    return (
      <div className="flex h-full items-center justify-center">
        <Typography variant="h4" affects="muted">
          This span is not part of a project
        </Typography>
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col overflow-auto">
      <div className="mb-4 flex shrink-0 items-center justify-between">
        <FunctionTitle span={span} />
        <div className="flex gap-2">
          <Button
            onClick={() => handleFullView(span)}
            variant="outline"
            size="sm"
            className="flex items-center gap-2"
          >
            <Maximize2 className="h-4 w-4" />
            <span className="hidden sm:inline">Full View</span>
          </Button>
        </div>
      </div>
      <div className="min-h-0 flex-1 overflow-hidden">
        <LilypadPanel spanUuid={data.uuid} showMetrics={false} />
      </div>
    </div>
  );
};
