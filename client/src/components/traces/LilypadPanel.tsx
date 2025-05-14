import { JsonView } from "@/components/JsonView";
import { SpanMetrics } from "@/components/traces/SpanMetrics";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { LilypadPanelTab } from "@/utils/panel-utils";
import { spanQueryOptions } from "@/utils/spans";
import { useSuspenseQuery } from "@tanstack/react-query";

export const LilypadPanel = ({
  spanUuid,
  showMetrics = true,
  tab,
  onTabChange,
}: {
  spanUuid: string;
  showMetrics?: boolean;
  tab?: string;
  onTabChange?: (tab: string) => void;
}) => {
  const { data: span } = useSuspenseQuery(spanQueryOptions(spanUuid));
  return (
    <div className="flex flex-col gap-4 h-full">
      {showMetrics && <SpanMetrics span={span} />}
      {span.arg_values && (
        <div className="shrink-0">
          <Card variant="primary">
            <CardHeader>
              <CardTitle>{"Inputs"}</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="rounded-md bg-background">
                <JsonView value={span.arg_values} />
              </div>
            </CardContent>
          </Card>
        </div>
      )}
      <div className="flex-1 min-h-0">
        <LilypadPanelTab span={span} tab={tab} onTabChange={onTabChange} />
      </div>
    </div>
  );
};
