import { SearchBar } from "@/components/SearchBar";
import { TracesTable } from "@/components/TracesTable";
import { SpanPublic } from "@/types/types";
import { spansByFunctionQueryOptions } from "@/utils/spans";
import { useSuspenseQueries } from "@tanstack/react-query";
import { useState } from "react";

export const CompareTracesTable = ({
  projectUuid,
  firstFunctionUuid,
  secondFunctionUuid,
}: {
  projectUuid: string;
  firstFunctionUuid: string;
  secondFunctionUuid?: string;
}) => {
  const data = useSuspenseQueries({
    queries: [firstFunctionUuid, secondFunctionUuid]
      .filter((uuid) => uuid !== undefined)
      .map((uuid) => ({
        ...spansByFunctionQueryOptions(projectUuid, uuid),
      })),
  });
  const defaultData = data.map((result) => result.data).flat();
  const [displayData, setDisplayData] = useState<SpanPublic[] | null>(null);
  return (
    <div className='py-2'>
      <SearchBar
        projectUuid={projectUuid}
        onDataChange={setDisplayData}
        filterFunction={(data) =>
          data.filter(
            (item) =>
              item.function_uuid === firstFunctionUuid ||
              item.function_uuid === secondFunctionUuid
          )
        }
      />
      <TracesTable
        data={displayData ?? defaultData}
        projectUuid={projectUuid}
      />
    </div>
  );
};
