import CardSkeleton from "@/components/CardSkeleton";
import { CodeSnippet } from "@/components/CodeSnippet";
import { MetricCharts } from "@/components/MetricsCharts";
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
    <div className="flex rounded-md flex-col lg:flex-row gap-2 h-full p-2">
      <div className="w-full lg:w-1/2">
        {showCompare ? (
          <DiffTool
            firstCodeBlock={firstFunction.code}
            secondCodeBlock={secondFunction?.code || ""}
          />
        ) : (
          <CodeSnippet code={firstFunction.code} />
        )}
      </div>

      <div className="w-full lg:w-1/2 flex flex-col gap-2">
        {features.annotations && (
          <div
            className={`w-full h-80 ${showCompare ? "flex flex-col sm:flex-row gap-2" : ""}`}
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
