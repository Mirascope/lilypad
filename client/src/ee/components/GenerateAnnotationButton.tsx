import { baseURL } from "@/api";
import { Button } from "@/components/ui/button";
import { AnnotationCreate } from "@/ee/types/types";
import { useEventSource } from "@/hooks/use-eventsource";
import { spanQueryOptions } from "@/utils/spans";
import { useSuspenseQuery } from "@tanstack/react-query";
import { useEffect } from "react";
import { useFormContext } from "react-hook-form";

export const GenerateAnnotationButton = ({
  spanUuid,
}: {
  spanUuid: string;
}) => {
  const { data: span } = useSuspenseQuery(spanQueryOptions(spanUuid));
  const methods = useFormContext<AnnotationCreate>();
  const url = `${baseURL}/ee/projects/${span.project_uuid}/spans/${spanUuid}/generate`;
  const { data, startConnection, stopConnection, isConnected, status } =
    useEventSource(url);
  // Handle generation completion if needed
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
    <Button
      onClick={() => startConnection()}
      disabled={isConnected || status === "connecting"}
    >
      {isConnected ? "Generating..." : "Generate Annotation"}
    </Button>
  );
};
