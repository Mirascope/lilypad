import CardSkeleton from "@/components/CardSkeleton";
import { LilypadPanel } from "@/components/traces/LilypadPanel";
import { Typography } from "@/components/ui/typography";
import { SpanPublic } from "@/types/types";
import { Suspense, useState } from "react";

interface ComparePanelProps {
  rows: SpanPublic[];
}

export const ComparePanel = ({ rows }: ComparePanelProps) => {
  const [tab, setTab] = useState<string | undefined>(undefined);
  if (rows.length !== 2) {
    return (
      <div className="p-6 text-muted-foreground italic">
        Select exactly two rows to compare.
      </div>
    );
  }
  return (
    <div className="flex flex-col md:flex-row gap-4 grow-1 min-h-0">
      <div className="w-full md:w-1/2 flex flex-col">
        <Typography variant="h3" className="shrink-0">
          Row 1
        </Typography>
        <Suspense
          fallback={<CardSkeleton items={5} className="flex flex-col" />}
        >
          <div className="flex-1 min-h-0">
            <LilypadPanel
              spanUuid={rows[0].uuid}
              tab={tab}
              onTabChange={(tab) => setTab(tab)}
            />
          </div>
        </Suspense>
      </div>
      <div className="w-full md:w-1/2 flex flex-col">
        <Typography variant="h3" className="shrink-0">
          Row 2
        </Typography>
        <Suspense
          fallback={<CardSkeleton items={5} className="flex flex-col" />}
        >
          <div className="grow min-h-0">
            <LilypadPanel
              spanUuid={rows[1].uuid}
              tab={tab}
              onTabChange={(tab) => setTab(tab)}
            />
          </div>
        </Suspense>
      </div>
    </div>
  );
};
