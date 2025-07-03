import CardSkeleton from "@/src/components/CardSkeleton";
import { CodeBlock } from "@/src/components/code-block";
import { MetricCharts } from "@/src/components/MetricsCharts";
import { AnnotationMetrics } from "@/src/ee/components/AnnotationMetrics";
import { DiffTool } from "@/src/ee/components/DiffTool";
import { useFeatureAccess } from "@/src/hooks/use-featureaccess";
import { FunctionPublic } from "@/src/types/types";
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
    <div className="flex h-full flex-col gap-2 rounded-md p-2 lg:flex-row">
      <div className="w-full shrink-0 overflow-auto lg:w-1/2">
        {showCompare ? (
          <DiffTool
            language="python"
            baseCodeBlock={firstFunction.code}
            incomingCodeBlock={secondFunction.code}
          />
        ) : (
          <CodeBlock language="python" code={firstFunction.code} />
        )}
      </div>

      <div className="flex w-full flex-col gap-2 lg:w-1/2">
        {features.annotations && (
          <div className={`h-80 w-full ${showCompare ? "flex flex-col gap-2 sm:flex-row" : ""}`}>
            <AnnotationMetrics
              projectUuid={projectUuid}
              functionUuid={firstFunction.uuid}
              title={
                showCompare ? `${firstFunction.name} v${firstFunction.version_num}` : undefined
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
