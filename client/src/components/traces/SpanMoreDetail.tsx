import CardSkeleton from "@/components/CardSkeleton";
import { LilypadMetrics, LilypadPanel } from "@/components/LilypadPanel";
import { TagPopover } from "@/components/TagPopover";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Typography } from "@/components/ui/typography";
import { SpanPublic } from "@/types/types";
import { SpanComments } from "@/utils/panel-utils";
import { spanQueryOptions } from "@/utils/spans";
import { useSuspenseQuery } from "@tanstack/react-query";
import { useNavigate } from "@tanstack/react-router";
import { Maximize2, Minimize2 } from "lucide-react";
import { Suspense, useEffect, useState } from "react";
import { toast } from "sonner";

export const SpanMoreDetails = ({
  data,
  path,
}: {
  data: SpanPublic;
  path?: string;
}) => {
  const navigate = useNavigate();
  const [isFullPage, setIsFullPage] = useState(false);
  const { data: span } = useSuspenseQuery(spanQueryOptions(data.uuid));
  const spanData: Record<string, unknown> = span.data as Record<
    string,
    unknown
  >;
  const attributes: Record<string, string> | undefined =
    spanData.attributes as Record<string, string>;
  const lilypadType = attributes?.["lilypad.type"];
  const versionNum = attributes?.[`lilypad.${lilypadType}.version`];
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

  const toggleFullPage = () => {
    setIsFullPage(!isFullPage);
  };

  return (
    <div
      className={`transition-all duration-300 ${isFullPage ? "container mx-auto py-4 max-w-screen-2xl h-full" : "h-full max-h-screen overflow-hidden"}`}
    >
      <div className="flex justify-between items-center mb-4 shrink-0">
        <div className="flex flex-col gap-1">
          <div className="flex gap-2 items-center">
            <Typography variant="h3">{span.display_name}</Typography>
            <Typography variant="span" affects="muted">
              {versionNum && `v${versionNum}`}
            </Typography>
          </div>
          <div className="flex gap-1 flex-wrap">
            {span.tags?.map((tag) => (
              <Badge pill variant="outline" size="sm" key={tag.uuid}>
                {tag.name}
              </Badge>
            ))}
            {span.project_uuid && (
              <TagPopover
                spanUuid={span.uuid}
                projectUuid={span.project_uuid}
                key="add-tag"
              />
            )}
          </div>
        </div>
        <div className="flex gap-2">
          <Button
            onClick={toggleFullPage}
            variant="outline"
            size="sm"
            className="flex gap-2 items-center"
          >
            {isFullPage ? (
              <>
                <Minimize2 className="h-4 w-4" />
                <span className="hidden sm:inline">Compact View</span>
              </>
            ) : (
              <>
                <Maximize2 className="h-4 w-4" />
                <span className="hidden sm:inline">Full View</span>
              </>
            )}
          </Button>
        </div>
      </div>

      <div
        className={`
          grid 
          ${isFullPage ? "grid-cols-1 lg:grid-cols-3 gap-6" : "grid-cols-1"} 
          h-[calc(100%-3rem)] overflow-auto
        `}
      >
        <div
          className={`
            ${isFullPage ? "lg:col-span-2" : ""} 
            overflow-y-auto pb-4
          `}
        >
          <LilypadPanel spanUuid={data.uuid} />
        </div>

        {(isFullPage || window.innerWidth >= 1024) && (
          <div
            className={`
              ${isFullPage ? "lg:block" : "hidden lg:block"} 
              space-y-6
            `}
          >
            <LilypadMetrics span={span} />
            <Suspense fallback={<CardSkeleton items={1} />}>
              <SpanComments data={data} />
            </Suspense>
          </div>
        )}
      </div>
    </div>
  );
};
