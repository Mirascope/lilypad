import { Token } from "@/assets/TokenIcon";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { SpanMoreDetails } from "@/types/types";
import { LilypadPanelTab } from "@/utils/panel-utils";
import { spanQueryOptions } from "@/utils/spans";
import { useSuspenseQuery } from "@tanstack/react-query";
import JsonView from "@uiw/react-json-view";

import React from "react";

export const LilypadMetrics = ({ span }: { span: SpanMoreDetails }) => {
  const metricSections = [
    {
      show:
        span.cost !== undefined &&
        span.input_tokens !== undefined &&
        span.output_tokens !== undefined,
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
        <div className="font-bold">
          {(span.duration_ms! / 1_000_000_000).toFixed(3)}s
        </div>
      ),
    },
    // Provider section
    {
      show: span.provider !== undefined,
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

  // Filter out sections that shouldn't be shown
  const visibleSections = metricSections.filter((section) => section.show);

  // If there are no visible sections, don't render the card at all
  if (visibleSections.length === 0) {
    return null;
  }

  return (
    <Card className="w-full">
      <div className="flex h-full">
        {visibleSections.map((section, index) => (
          <React.Fragment key={section.title}>
            <div className="flex-1 p-2 flex justify-center">
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
              <div className="py-2 flex items-center">
                <Separator
                  orientation="vertical"
                  className="h-full bg-accent"
                />
              </div>
            )}
          </React.Fragment>
        ))}
      </div>
    </Card>
  );
};

export const LilypadPanel = ({
  spanUuid,
  showMetrics = true,
}: {
  spanUuid: string;
  showMetrics?: boolean;
}) => {
  const { data: span } = useSuspenseQuery(spanQueryOptions(spanUuid));
  return (
    <div className="flex flex-col gap-4 h-full">
      {showMetrics && <LilypadMetrics span={span} />}
      {span.arg_values && (
        <div className="shrink-0">
          <Card variant="primary">
            <CardHeader>
              <CardTitle>{"Inputs"}</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="bg-primary-foreground p-2 text-card-foreground relative rounded-lg border shadow-sm overflow-x-auto">
                <JsonView value={span.arg_values} />
              </div>
            </CardContent>
          </Card>
        </div>
      )}
      <div className="flex-1 min-h-0">
        <LilypadPanelTab span={span} />
      </div>
    </div>
  );
};
