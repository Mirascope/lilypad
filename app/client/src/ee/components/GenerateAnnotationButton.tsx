import { baseURL } from "@/src/api";
import { Button } from "@/src/components/ui/button";
import { useEventSource } from "@/src/hooks/use-eventsource";
import { AnnotationUpdate } from "@/src/types/types";
import { spanQueryOptions } from "@/src/utils/spans";
import { useSuspenseQuery } from "@tanstack/react-query";
import { useParams } from "@tanstack/react-router";
import { useEffect } from "react";
import { useFormContext } from "react-hook-form";

export const GenerateAnnotationButton = ({ spanUuid }: { spanUuid: string }) => {
  const { projectUuid } = useParams({ strict: false });
  if (!projectUuid) {
    throw new Error("Generating annotations requires an active project");
  }
  const { data: span } = useSuspenseQuery(spanQueryOptions(projectUuid, spanUuid));
  const methods = useFormContext<AnnotationUpdate>();
  const url = `${baseURL}/ee/projects/${span.project_uuid}/spans/${spanUuid}/generate-annotation`;
  const { data, startConnection, stopConnection, isConnected, status } = useEventSource(url);
  // Handle function completion if needed
  useEffect(() => {
    if (data.length > 0) {
      const lastEvent = data[data.length - 1];
      methods.setValue("data", lastEvent.results);
      // Check if we have a completion condition (depends on your API's response format)
      if (lastEvent.status === "completed" || lastEvent.done === true) {
        stopConnection();
      }
    }
  }, [data, stopConnection]);

  return (
    <Button onClick={() => startConnection()} disabled={isConnected || status === "connecting"}>
      {isConnected ? "Generating..." : "Generate Annotation"}
    </Button>
  );
};
