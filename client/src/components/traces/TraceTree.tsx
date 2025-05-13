import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Typography } from "@/components/ui/typography";
import { cn } from "@/lib/utils";
import { SpanPublic } from "@/types/types";
import { formatRelativeTime } from "@/utils/strings";
import { useNavigate } from "@tanstack/react-router";
import { ChevronDown, ChevronRight } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

interface SpanTreeProps {
  span: SpanPublic;
  projectUuid: string;
  currentSpanUuid: string;
  level: number;
}

export const TraceTree = ({
  span,
  projectUuid,
  currentSpanUuid,
  level,
}: SpanTreeProps) => {
  const navigate = useNavigate();
  const [expanded, setExpanded] = useState(true);
  const isCurrentSpan = span.uuid === currentSpanUuid;
  const hasChildren = span.child_spans && span.child_spans.length > 0;

  const handleSpanClick = () => {
    if (isCurrentSpan) return;

    navigate({
      to: "/projects/$projectUuid/traces/detail/$spanUuid",
      params: { projectUuid, spanUuid: span.uuid },
    }).catch(() => toast.error("Failed to navigate"));
  };

  // Get version number if available
  const versionNum = span.function?.version_num;

  return (
    <div className="w-full">
      <div
        className={cn(
          "flex items-center py-2 px-1 rounded-md transition-colors hover:bg-accent/50 cursor-pointer",
          isCurrentSpan && "bg-accent font-medium"
        )}
        style={{ paddingLeft: `${level * 1.5}rem` }}
        onClick={handleSpanClick}
      >
        {hasChildren ? (
          <Button
            variant="ghost"
            size="sm"
            className="p-0 size-6 mr-2 shrink-0"
            onClick={(e) => {
              e.stopPropagation();
              setExpanded(!expanded);
            }}
          >
            {expanded ? (
              <ChevronDown className="h-4 w-4" />
            ) : (
              <ChevronRight className="h-4 w-4" />
            )}
          </Button>
        ) : (
          <div className="w-6 mr-2 shrink-0" />
        )}

        <div className="flex flex-col min-w-0 w-full ">
          <div className="flex items-center gap-2 w-full">
            <span className="truncate font-medium max-w-full">
              {span.display_name ?? span.span_id}
            </span>
            {versionNum && (
              <Typography
                variant="span"
                className="text-xs whitespace-nowrap shrink-0"
              >
                v{versionNum}
              </Typography>
            )}
            {span.duration_ms && (
              <Badge variant="neutral" size="sm" className="shrink-0">
                {(span.duration_ms / 1_000_000_000).toFixed(3)}s
              </Badge>
            )}
          </div>

          <div className="flex gap-2 flex-wrap mt-1 items-center">
            {span.tags && span.tags.length > 0 && (
              <Badge variant="neutral" size="sm" className="shrink-0">
                {span.tags[0].name}
                {span.tags.length > 1 && (
                  <span className="ml-1">+{span.tags.length - 1}</span>
                )}
              </Badge>
            )}

            {span.status && span.status !== "UNSET" && (
              <Badge variant="destructive" size="sm" className="shrink-0">
                {span.status}
              </Badge>
            )}

            <Typography variant="span" className="text-xs shrink-0">
              {formatRelativeTime(span.created_at)}
            </Typography>
          </div>
        </div>
      </div>

      {expanded && hasChildren && (
        <div>
          {span.child_spans.map((child) => (
            <TraceTree
              key={child.uuid}
              span={child}
              projectUuid={projectUuid}
              currentSpanUuid={currentSpanUuid}
              level={level + 1}
            />
          ))}
        </div>
      )}
    </div>
  );
};
