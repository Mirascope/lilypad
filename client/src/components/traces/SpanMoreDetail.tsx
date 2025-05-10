import { LilypadPanel } from "@/components/LilypadPanel";
import { FunctionTitle } from "@/components/traces/FunctionTitle";
import { Button } from "@/components/ui/button";
import { Typography } from "@/components/ui/typography";
import { SpanMoreDetails, SpanPublic } from "@/types/types";
import { spanQueryOptions } from "@/utils/spans";
import { useSuspenseQuery } from "@tanstack/react-query";
import { Maximize2 } from "lucide-react";

export const SpanMoreDetail = ({
  data,
  handleFullView,
}: {
  data: SpanPublic;
  handleFullView: (span: SpanMoreDetails) => void;
}) => {
  const { data: span } = useSuspenseQuery(spanQueryOptions(data.uuid));

  if (!span.project_uuid) {
    return (
      <div className="flex items-center justify-center h-full">
        <Typography variant="h4" affects="muted">
          This span is not part of a project
        </Typography>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full overflow-auto">
      <div className="flex justify-between items-center mb-4 shrink-0">
        <FunctionTitle span={span} />
        <div className="flex gap-2">
          <Button
            onClick={() => handleFullView(span)}
            variant="outline"
            size="sm"
            className="flex gap-2 items-center"
          >
            <Maximize2 className="h-4 w-4" />
            <span className="hidden sm:inline">Full View</span>
          </Button>
        </div>
      </div>
      <div className="flex-1 overflow-hidden">
        <LilypadPanel spanUuid={data.uuid} showMetrics={false} />
      </div>
    </div>
  );
};
