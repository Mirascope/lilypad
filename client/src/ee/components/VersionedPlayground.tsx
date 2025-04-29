import LilypadDialog from "@/components/LilypadDialog";
import { Button } from "@/components/ui/button";
import { Combobox } from "@/components/ui/combobox";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Typography } from "@/components/ui/typography";
import { useToast } from "@/hooks/use-toast";
import { FunctionPublic } from "@/types/types";
import {
  functionsByNameQueryOptions,
  uniqueLatestVersionFunctionNamesQueryOptions,
  useArchiveFunctionMutation,
} from "@/utils/functions";
import { useSuspenseQuery } from "@tanstack/react-query";
import { Outlet, useNavigate } from "@tanstack/react-router";
import { GitCompare, Trash } from "lucide-react";
import { useState } from "react";

interface VersionedPlaygroundProps {
  projectUuid: string;
  functionName?: string;
  functions?: FunctionPublic[];
  functionUuid?: string;
  secondFunctionUuid?: string;
  isCompare: boolean;
}
export const VersionedPlayground = ({
  projectUuid,
  functionName,
  functions,
  functionUuid,
  secondFunctionUuid,
  isCompare,
}: VersionedPlaygroundProps) => {
  const { data: functionNames } = useSuspenseQuery(
    uniqueLatestVersionFunctionNamesQueryOptions(projectUuid)
  );
  const { toast } = useToast();
  const [compareMode, setCompareMode] = useState<boolean>(isCompare);
  const navigate = useNavigate();
  const fn = functions?.find((f) => f.uuid === functionUuid) ?? null;
  const archiveFunction = useArchiveFunctionMutation();
  const handleNewFunctionClick = (newFunctionName: string) => {
    navigate({
      to: `/projects/${projectUuid}/playground/${newFunctionName}`,
    }).catch(() =>
      toast({
        title: "Failed to navigate",
      })
    );
  };

  const handleArchive = async () => {
    if (!fn || !functionName) return;
    await archiveFunction.mutateAsync({
      projectUuid,
      functionUuid: fn.uuid,
      functionName,
    });
    navigate({ to: `/projects/${projectUuid}/playground` }).catch(() =>
      toast({
        title: "Failed to navigate",
      })
    );
  };

  return (
    <div className="w-full p-6 flex flex-col gap-1">
      <Typography variant="h3">Playground</Typography>
      <div className="flex gap-2">
        <Combobox
          popoverText="Select or create a new playground"
          helperText="Search for a playground..."
          emptyText="Type to create a new function"
          items={functionNames.map((fn) => ({
            value: fn.name,
            label: fn.name,
          }))}
          value={functionName ?? ""}
          onChange={(value: string) => {
            handleNewFunctionClick(value);
          }}
        />
      </div>
      <div className="flex gap-2 items-center">
        <Button
          variant="outline"
          size="icon"
          disabled={!fn}
          onClick={() => {
            if (!compareMode) {
              navigate({
                to: `/projects/${projectUuid}/playground/${functionName}/compare/$firstFunctionUuid/$secondFunctionUuid`,
                params: {
                  firstFunctionUuid: functionUuid,
                  secondFunctionUuid,
                },
              }).catch(() =>
                toast({
                  title: "Failed to navigate",
                })
              );
            } else {
              navigate({
                to: `/projects/${projectUuid}/playground/${functionName}/${functionUuid}`,
              }).catch(() =>
                toast({
                  title: "Failed to navigate",
                })
              );
            }
            setCompareMode((prevCompareMode) => !prevCompareMode);
          }}
        >
          <GitCompare />
        </Button>
        <SelectFunction
          projectUuid={projectUuid}
          functionName={functionName}
          firstFunctionUuid={functionUuid}
          secondFunctionUuid={secondFunctionUuid}
          compareMode={compareMode}
          isFirstFunction={true}
        />
        {fn && !isCompare && functionName && (
          <LilypadDialog
            icon={<Trash />}
            title={`Delete ${fn.name} v${fn.version_num}`}
            description=""
            dialogContentProps={{
              className: "max-w-[600px]",
            }}
            buttonProps={{
              variant: "outlineDestructive",
              className: "w-9 h-9",
            }}
            dialogButtons={[
              <Button
                key="delete-function"
                type="button"
                variant="destructive"
                onClick={handleArchive}
              >
                Delete
              </Button>,
              <Button
                key="cancel-delete-button"
                type="button"
                variant="outline"
              >
                Cancel
              </Button>,
            ]}
          >
            {`Are you sure you want to delete ${fn.name} v${fn.version_num}?`}
          </LilypadDialog>
        )}
      </div>
      {functionName && functionUuid && compareMode && (
        <div className="flex gap-2 items-center">
          <div className="w-10 h-10"></div>
          <SelectFunction
            projectUuid={projectUuid}
            functionName={functionName}
            firstFunctionUuid={functionUuid}
            secondFunctionUuid={secondFunctionUuid}
            compareMode={compareMode}
            isFirstFunction={false}
          />
        </div>
      )}
      <Outlet />
    </div>
  );
};

interface SelectFunctionProps {
  projectUuid: string;
  functionName?: string;
  firstFunctionUuid?: string;
  secondFunctionUuid?: string;
  compareMode?: boolean;
  isFirstFunction?: boolean;
}
const SelectFunction = ({
  projectUuid,
  functionName,
  firstFunctionUuid,
  secondFunctionUuid,
  compareMode,
  isFirstFunction,
}: SelectFunctionProps) => {
  const { toast } = useToast();
  const navigate = useNavigate();
  const { data: functions } = useSuspenseQuery(
    functionsByNameQueryOptions(functionName ?? "", projectUuid)
  );
  return (
    <Select
      disabled={!functionName}
      value={(isFirstFunction ? firstFunctionUuid : secondFunctionUuid) ?? ""}
      onValueChange={(uuid) => {
        if (compareMode) {
          navigate({
            to: `/projects/${projectUuid}/playground/${functionName}/compare/$firstFunctionUuid/$secondFunctionUuid`,
            params: {
              firstFunctionUuid: isFirstFunction ? uuid : firstFunctionUuid,
              secondFunctionUuid: isFirstFunction ? secondFunctionUuid : uuid,
            },
          }).catch(() =>
            toast({
              title: "Failed to navigate",
            })
          );
        } else {
          navigate({
            to: `/projects/${projectUuid}/playground/${functionName}/${uuid}`,
          }).catch(() =>
            toast({
              title: "Failed to navigate",
            })
          );
        }
      }}
    >
      <SelectTrigger className="w-[200px]">
        <SelectValue placeholder="Select a version" />
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
