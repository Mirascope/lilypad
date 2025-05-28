import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { FunctionTab } from "@/types/functions";
import { functionsByNameQueryOptions } from "@/utils/functions";
import { useSuspenseQuery } from "@tanstack/react-query";
import { useNavigate } from "@tanstack/react-router";
import { toast } from "sonner";

export const SelectFunction = ({
  compareMode,
  isFirstFunction,
  projectUuid,
  functionName,
  firstFunctionUuid,
  secondFunctionUuid,
  tab,
  onSecondFunctionChange,
}: {
  compareMode?: boolean;
  projectUuid: string;
  isFirstFunction?: boolean;
  functionName: string;
  firstFunctionUuid: string;
  secondFunctionUuid?: string;
  tab: FunctionTab;
  onSecondFunctionChange?: (uuid: string) => void;
}) => {
  const { data: functions } = useSuspenseQuery(
    functionsByNameQueryOptions(functionName, projectUuid)
  );
  const navigate = useNavigate();
  return (
    <Select
      value={(isFirstFunction ? firstFunctionUuid : secondFunctionUuid) ?? ""}
      onValueChange={(uuid: string) => {
        if (compareMode) {
          if (isFirstFunction) {
            navigate({
              to: `/projects/${projectUuid}/functions/${functionName}/${uuid}/${tab}`,
            }).catch(() => toast.error("Failed to navigate"));
          } else {
            // For second function selection
            if (onSecondFunctionChange) {
              onSecondFunctionChange(uuid);
            } else {
              navigate({
                to: `/projects/${projectUuid}/functions/${functionName}/compare/${firstFunctionUuid}/${uuid}/${tab}`,
              }).catch(() => toast.error("Failed to navigate"));
            }
          }
        } else {
          navigate({
            to: `/projects/${projectUuid}/functions/${functionName}/${uuid}/${tab}`,
          }).catch(() => toast.error("Failed to navigate"));
        }
      }}
    >
      <SelectTrigger className="w-[70px]">
        <SelectValue placeholder="" />
      </SelectTrigger>
      <SelectContent>
        {functions.map((fn) => (
          <SelectItem
            key={fn.uuid}
            value={fn.uuid}
            disabled={
              (!isFirstFunction && fn.uuid === firstFunctionUuid) ||
              (isFirstFunction && fn.uuid === secondFunctionUuid)
            }
          >
            v{fn.version_num}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
};
