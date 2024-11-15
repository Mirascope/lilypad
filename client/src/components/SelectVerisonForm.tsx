import { useNavigate, useParams } from "@tanstack/react-router";
import { useSuspenseQuery } from "@tanstack/react-query";
import { versionsByFunctionNameQueryOptions } from "@/utils/versions";
import { uniqueFunctionNamesQueryOptions } from "@/utils/functions";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectValue,
  SelectTrigger,
  SelectContent,
  SelectItem,
} from "@/components/ui/select";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { Plus } from "lucide-react";
import { Controller, FormProvider, useForm, useWatch } from "react-hook-form";
import { useEffect } from "react";
import { VersionPublic } from "@/types/types";

type FunctionFormValues = {
  functionName: string;
  version: VersionPublic | null;
};

export const SelectVersionForm = () => {
  const {
    projectId,
    functionName: defaultFunctionName,
    versionId,
  } = useParams({
    strict: false,
  });
  const navigate = useNavigate();
  const method = useForm<FunctionFormValues>({
    defaultValues: {
      functionName: defaultFunctionName,
      version: null,
    },
  });
  const functionName = useWatch({
    control: method.control,
    name: "functionName",
  });

  useEffect(() => {
    const subscription = method.watch((value, { name, type }) => {
      if (name === "functionName") {
        method.setValue("version", null);
        navigate({
          to: `/projects/${projectId}/functions/${value.functionName}`,
        });
      } else if (name === "version" && value.version) {
        navigate({
          to: `/projects/${projectId}/functions/${functionName}/versions/${value.version.id}`,
        });
      }
    });

    return () => subscription.unsubscribe();
  }, [method.watch]);

  const { data: versions } = useSuspenseQuery(
    versionsByFunctionNameQueryOptions(Number(projectId), functionName)
  );
  const { data: uniqueFunctionNames } = useSuspenseQuery(
    uniqueFunctionNamesQueryOptions(Number(projectId))
  );
  useEffect(() => {
    const version = versions?.find((v) => v.id === Number(versionId));
    if (!version) return;
    method.setValue("version", version);
  }, [versions, versionId]);
  return (
    <FormProvider {...method}>
      <div className='flex gap-2'>
        <Tooltip>
          <TooltipTrigger asChild>
            <Button
              size='icon'
              onClick={() =>
                navigate({ to: `/projects/${projectId}/functions` })
              }
            >
              <Plus />
            </Button>
          </TooltipTrigger>
          <TooltipContent className='bg-slate-500'>
            <p>Create a new function</p>
          </TooltipContent>
        </Tooltip>
        <Controller
          control={method.control}
          name='functionName'
          render={({ field }) => (
            <Select value={field.value} onValueChange={field.onChange}>
              <SelectTrigger className='w-[200px]'>
                <SelectValue placeholder='Select a function' />
              </SelectTrigger>
              <SelectContent>
                {uniqueFunctionNames.map((name) => (
                  <SelectItem key={name} value={name}>
                    {name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          )}
        />
        <Controller
          control={method.control}
          name='version'
          render={({ field }) => (
            <Select
              value={JSON.stringify(field.value)}
              onValueChange={(value) => field.onChange(JSON.parse(value))}
              disabled={!functionName || !versions}
            >
              <SelectTrigger className='w-[100px]'>
                <SelectValue placeholder='version' />
              </SelectTrigger>
              <SelectContent>
                {versions?.map((version, i) => (
                  <SelectItem key={version.id} value={JSON.stringify(version)}>
                    v{i + 1}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          )}
        />
      </div>
    </FormProvider>
  );
};
