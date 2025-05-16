import { Token } from "@/assets/TokenIcon";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { SpanMoreDetails } from "@/types/types";

import { Fragment, useEffect, useRef, useState } from "react";

export const SpanMetrics = ({ span }: { span: SpanMoreDetails }) => {
  const [isCompact, setIsCompact] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!containerRef.current) return;

    const observer = new ResizeObserver((entries) => {
      for (const entry of entries) {
        setIsCompact(entry.contentRect.width < 350);
      }
    });

    observer.observe(containerRef.current);

    return () => {
      if (containerRef.current) {
        observer.unobserve(containerRef.current);
      }
    };
  }, []);
  const metricSections = [
    {
      show: span.cost !== 0 && (span.input_tokens ?? span.output_tokens),
      title: "Cost and Tokens",
      content: (
        <>
          <div className="font-bold">${span.cost?.toFixed(5)}</div>
          <p className="text-xs text-muted-foreground">
            <span>{span.input_tokens}</span>
            <span className="mx-1">&#8594;</span>
            <span>{span.output_tokens}</span>
            <span className="mx-1">=</span>
            <span className="inline-flex items-center gap-1">
              {(span.input_tokens ?? 0) + (span.output_tokens ?? 0)}
              <Token className="h-3.5 w-3.5" />
            </span>
          </p>
        </>
      ),
    },
    // Duration section
    {
      show: span.duration_ms !== undefined,
      title: "Duration",
      content: (
        <div className="font-bold">{span.duration_ms! / 1_000_000_000}s</div>
      ),
    },
    // Provider section
    {
      show: span.provider !== undefined && span.provider !== "unknown",
      title: "Provider",
      content: (
        <>
          <div className="font-bold">{span.provider}</div>
          {span.model && (
            <p className="text-xs text-muted-foreground">{span.model}</p>
          )}
        </>
      ),
    },
  ];

  const visibleSections = metricSections.filter((section) => section.show);

  if (visibleSections.length === 0) {
    return null;
  }

  return (
    <Card className="w-full" ref={containerRef}>
      <div className={`flex ${isCompact ? "flex-col" : "flex-row"} h-full`}>
        {visibleSections.map((section, index) => (
          <Fragment key={section.title}>
            <div
              className={`flex-1 p-2 flex ${isCompact ? "justify-start pl-4" : "justify-center"}`}
            >
              <div className="text-left">
                <CardHeader className="px-0 py-1">
                  <CardTitle className="text-sm font-medium">
                    {section.title}
                  </CardTitle>
                </CardHeader>
                <CardContent className="px-0 pt-0 pb-1">
                  {section.content}
                </CardContent>
              </div>
            </div>

            {index < visibleSections.length - 1 && (
              <div
                className={`flex justify-center ${isCompact ? "py-1" : "py-2"}`}
              >
                {isCompact ? (
                  <Separator orientation="horizontal" className="w-4/5" />
                ) : (
                  <Separator orientation="vertical" className="h-full" />
                )}
              </div>
            )}
          </Fragment>
        ))}
      </div>
    </Card>
  );
};
