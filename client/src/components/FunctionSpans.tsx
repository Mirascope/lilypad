import { SearchBar } from "@/components/SearchBar";
import { TracesTable } from "@/components/TracesTable";
import { Route } from "@/routes/_auth/projects/$projectUuid/functions/$functionName/_workbench/$functionUuid.$tab.$.tsx";
import { SpanPublic } from "@/types/types";
import { spansByFunctionQueryOptions } from "@/utils/spans";
import { useSuspenseQuery } from "@tanstack/react-query";
import { useState } from "react";
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

  const [displayData, setDisplayData] = useState<SpanPublic[] | null>(null);

  return (
    <div className='space-y-4'>
      <SearchBar
        projectUuid={projectUuid}
        onDataChange={setDisplayData}
        filterFunction={(data) =>
          data.filter((item) => item.function_uuid === functionUuid)
        }
      />
      <TracesTable
        data={displayData ?? defaultData}
        traceUuid={traceUuid}
        path={Route.fullPath}
        projectUuid={projectUuid}
      />
    </div>
  );
};
