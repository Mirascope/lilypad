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
      <div className="text-muted-foreground p-6 italic">Select exactly two rows to compare.</div>
    );
  }
  return (
    <div className="flex min-h-0 grow-1 flex-col gap-4 md:flex-row">
      <div className="flex w-full flex-col md:w-1/2">
        <Typography variant="h3" className="shrink-0">
          Row 1
        </Typography>
        <Suspense fallback={<CardSkeleton items={5} className="flex flex-col" />}>
          <div className="min-h-0 flex-1">
            <LilypadPanel spanUuid={rows[0].uuid} tab={tab} onTabChange={(tab) => setTab(tab)} />
          </div>
        </Suspense>
      </div>
      <div className="flex w-full flex-col md:w-1/2">
        <Typography variant="h3" className="shrink-0">
          Row 2
        </Typography>
        <Suspense fallback={<CardSkeleton items={5} className="flex flex-col" />}>
          <div className="min-h-0 grow">
            <LilypadPanel spanUuid={rows[1].uuid} tab={tab} onTabChange={(tab) => setTab(tab)} />
          </div>
        </Suspense>
      </div>
    </div>
  );
};
