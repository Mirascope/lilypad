import CardSkeleton from "@/components/CardSkeleton";
import { CodeSnippet } from "@/components/CodeSnippet";
import { MetricCharts } from "@/components/MetricsCharts";
import { Label } from "@/components/ui/label";
import { AnnotationMetrics } from "@/ee/components/AnnotationMetrics";
import { DiffTool } from "@/ee/components/DiffTool";
import { useFeatureAccess } from "@/hooks/use-featureaccess";
import { FunctionPublic } from "@/types/types";
import { Suspense } from "react";

interface FunctionOverviewUIProps {
  projectUuid: string;
  firstFunction: FunctionPublic;
  secondFunction?: FunctionPublic;
  isCompare?: boolean;
}

export const FunctionOverviewUI = ({
  projectUuid,
  firstFunction,
  secondFunction,
  isCompare = false,
}: FunctionOverviewUIProps) => {
  const features = useFeatureAccess();
  const showCompare = isCompare && secondFunction;

  return (
    <div className="p-2 flex flex-col lg:flex-row gap-4 h-full overflow-auto">
      {/* Code Section - 100% on small screens, 50% on large screens */}
      <div className="w-full lg:w-1/2">
        <Label>Code</Label>
        {showCompare ? (
          <DiffTool
            firstCodeBlock={firstFunction.code}
            secondCodeBlock={secondFunction?.code || ""}
          />
        ) : (
          <CodeSnippet code={firstFunction.code} />
        )}
      </div>

      {/* Metrics Section - 100% on small screens, 50% on large screens */}
      <div className="w-full lg:w-1/2 flex flex-col gap-4">
        {/* Annotation Metrics */}
        {features.annotations && (
          <div
            className={`w-full h-80 ${showCompare ? "flex flex-col sm:flex-row gap-4" : ""}`}
          >
            <AnnotationMetrics
              projectUuid={projectUuid}
              functionUuid={firstFunction.uuid}
              title={
                showCompare
                  ? `${firstFunction.name} v${firstFunction.version_num}`
                  : undefined
              }
              description={showCompare ? "Annotation Pass Rate" : undefined}
              className={showCompare ? "flex-1" : "h-full"}
            />

            {showCompare && secondFunction && (
              <AnnotationMetrics
                projectUuid={projectUuid}
                functionUuid={secondFunction.uuid}
                title={`${secondFunction.name} v${secondFunction.version_num}`}
                description={"Annotation Pass Rate"}
                className="flex-1"
              />
            )}
          </div>
        )}

        {/* Metric Charts */}
        <div className="flex-1">
          <Suspense fallback={<CardSkeleton />}>
            <MetricCharts
              firstFunction={firstFunction}
              secondFunction={showCompare ? secondFunction : undefined}
              projectUuid={projectUuid}
            />
          </Suspense>
        </div>
      </div>
    </div>
  );
};
