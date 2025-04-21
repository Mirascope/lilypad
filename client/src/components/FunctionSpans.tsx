import { SearchBar } from "@/components/SearchBar";
import { TracesTable } from "@/components/TracesTable";
import { Route } from "@/routes/_auth/projects/$projectUuid/functions/$functionName/_workbench/$functionUuid.$tab.$.tsx";
import { SpanPublic } from "@/types/types";
import { spansByFunctionQueryOptions } from "@/utils/spans";
import { useSuspenseQuery } from "@tanstack/react-query";
import { useEffect, useState } from "react";
export const FunctionSpans = ({
  projectUuid,
  functionUuid,
  traceUuid,
}: {
  projectUuid: string;
  functionUuid: string;
  traceUuid?: string;
}) => {
  const { data: defaultData } = useSuspenseQuery(
    spansByFunctionQueryOptions(projectUuid, functionUuid)
  );

  const [displayData, setDisplayData] = useState<SpanPublic[] | undefined>(
    defaultData
  );

  useEffect(() => {
    setDisplayData(defaultData);
  }, [defaultData]);

  return (
    <div className='space-y-4'>
      <SearchBar
        projectUuid={projectUuid}
        defaultData={defaultData}
        onDataChange={setDisplayData}
      />

      <TracesTable
        data={
          displayData?.filter((data) => data.function_uuid === functionUuid) ??
          []
        }
        traceUuid={traceUuid}
        path={Route.fullPath}
      />
    </div>
  );
};
