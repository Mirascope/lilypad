import { baseURL } from "@/api";
import { Button } from "@/components/ui/button";
import { useEventSource } from "@/hooks/use-eventsource";
import { AnnotationUpdate } from "@/types/types";
import { spanQueryOptions } from "@/utils/spans";
import { useSuspenseQuery } from "@tanstack/react-query";
import { useEffect } from "react";
import { useFormContext } from "react-hook-form";

export const GenerateAnnotationButton = ({ spanUuid }: { spanUuid: string }) => {
  const { data: span } = useSuspenseQuery(spanQueryOptions(spanUuid));
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
