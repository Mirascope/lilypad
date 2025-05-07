import { Token } from "@/assets/TokenIcon";
import { CollapsibleCard } from "@/components/CollapsibleCard";
import { TagPopover } from "@/components/TagPopover";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { Typography } from "@/components/ui/typography";
import { SpanMoreDetails } from "@/types/types";
import {
  LilypadPanelTab,
  MessagesContainer,
  renderEventsContainer,
} from "@/utils/panel-utils";
import { spanQueryOptions } from "@/utils/spans";
import { useSuspenseQuery } from "@tanstack/react-query";
import JsonView from "@uiw/react-json-view";

import React from "react";

const LilypadMetrics = ({ span }: { span: SpanMoreDetails }) => {
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

export const LilypadPanel = ({ spanUuid }: { spanUuid: string }) => {
  const { data: span } = useSuspenseQuery(spanQueryOptions(spanUuid));
  const data: Record<string, unknown> = span.data as Record<string, unknown>;
  const attributes: Record<string, string> | undefined =
    data.attributes as Record<string, string>;
  const lilypadType = attributes?.["lilypad.type"];
  const versionNum = attributes?.[`lilypad.${lilypadType}.version`];
  span.input_tokens = 100;
  span.output_tokens = 253;
  span.cost = 0.00001;
  return (
    <div className="flex flex-col gap-4">
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
      <LilypadMetrics span={span} />

      {span.events &&
        span.events.length > 0 &&
        renderEventsContainer(span.events)}
      {span.template && (
        <CollapsibleCard title="Prompt Template" content={span.template} />
      )}
      {span.messages.length > 0 && (
        <MessagesContainer messages={span.messages} />
      )}
      <div className="flex gap-4 flex-wrap">
        {span.arg_values && (
          <Card className="w-[calc(50%-0.5rem)] grow">
            <CardHeader>
              <CardTitle>{"Input"}</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="bg-primary-foreground p-2 text-card-foreground relative rounded-lg border shadow-sm overflow-x-auto">
                <JsonView value={span.arg_values} />
              </div>
            </CardContent>
          </Card>
        )}
      </div>
      <LilypadPanelTab span={span} />
    </div>
  );
};
