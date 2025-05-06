import CardSkeleton from "@/components/CardSkeleton";
import { LilypadPanel } from "@/components/LilypadPanel";
import { LlmPanel } from "@/components/LlmPanel";
import { Button } from "@/components/ui/button";
import { Scope, SpanPublic } from "@/types/types";
import { Suspense } from "react";

interface ComparePanelProps {
  rows: SpanPublic[];
  onClose: () => void;
}

export const ComparePanel = ({ rows, onClose }: ComparePanelProps) => {
  if (rows.length !== 2) {
    return (
      <div className="p-6 text-muted-foreground italic">
        Select exactly two rows to compare.
      </div>
    );
  }

  return (
    <div className="p-4 border rounded-md overflow-auto">
      <Button variant="outline" size="sm" onClick={onClose} className="mb-4">
        Go back
      </Button>
      <h2 className="text-lg font-semibold mb-2">Compare Details</h2>
      <div className="flex flex-col md:flex-row gap-4">
        <div className="w-full md:w-1/2">
          <h3 className="text-lg font-semibold">Row 1</h3>
          <Suspense
            fallback={<CardSkeleton items={5} className="flex flex-col" />}
          >
            {rows[0].scope === Scope.LILYPAD ? (
              <LilypadPanel spanUuid={rows[0].uuid} />
            ) : (
              <LlmPanel spanUuid={rows[0].uuid} />
            )}
          </Suspense>
        </div>
        <div className="w-full md:w-1/2">
          <h3 className="text-lg font-semibold">Row 2</h3>
          <Suspense
            fallback={<CardSkeleton items={5} className="flex flex-col" />}
          >
            {rows[1].scope === Scope.LILYPAD ? (
              <LilypadPanel spanUuid={rows[1].uuid} />
            ) : (
              <LlmPanel spanUuid={rows[1].uuid} />
            )}
          </Suspense>
        </div>
      </div>
    </div>
  );
};
