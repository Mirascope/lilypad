import { Badge } from "@/src/components/ui/badge";
import { Button } from "@/src/components/ui/button";
import { Typography } from "@/src/components/ui/typography";
import { cn } from "@/src/lib/utils";
import { SpanPublic } from "@/src/types/types";
import { formatRelativeTime } from "@/src/utils/strings";
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

export const TraceTree = ({ span, projectUuid, currentSpanUuid, level }: SpanTreeProps) => {
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
          "flex cursor-pointer items-center rounded-md px-1 py-2 transition-colors hover:bg-accent/50",
          isCurrentSpan && "bg-accent font-medium"
        )}
        style={{ paddingLeft: `${level * 1.5}rem` }}
        onClick={handleSpanClick}
      >
        {hasChildren ? (
          <Button
            variant="ghost"
            size="sm"
            className="mr-2 size-6 shrink-0 p-0"
            onClick={(e) => {
              e.stopPropagation();
              setExpanded(!expanded);
            }}
          >
            {expanded ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
          </Button>
        ) : (
          <div className="mr-2 w-6 shrink-0" />
        )}

        <div className="flex w-full min-w-0 flex-col">
          <div className="flex w-full items-center gap-2">
            <span className="max-w-full truncate font-medium">
              {span.display_name ?? span.span_id}
            </span>
            {versionNum && (
              <Typography variant="span" className="shrink-0 text-xs whitespace-nowrap">
                v{versionNum}
              </Typography>
            )}
            {span.duration_ms && (
              <Badge variant="neutral" size="sm" className="shrink-0">
                {(span.duration_ms / 1_000_000_000).toFixed(3)}s
              </Badge>
            )}
          </div>

          <div className="mt-1 flex flex-wrap items-center gap-2">
            {span.tags && span.tags.length > 0 && (
              <Badge variant="neutral" size="sm" className="shrink-0">
                {span.tags[0].name}
                {span.tags.length > 1 && <span className="ml-1">+{span.tags.length - 1}</span>}
              </Badge>
            )}

            {span.status && span.status !== "UNSET" && (
              <Badge variant="destructive" size="sm" className="shrink-0">
                {span.status}
              </Badge>
            )}

            <Typography variant="span" className="shrink-0 text-xs">
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
