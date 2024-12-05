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
import {
  Controller,
  FormProvider,
  useForm,
  useFormContext,
  useWatch,
} from "react-hook-form";
import { useEffect } from "react";
import { VersionPublic } from "@/types/types";
import { IconDialog } from "@/components/IconDialog";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
type FunctionFormValues = {
  newFunctionName: string;
  functionName: string;
  version: VersionPublic | null;
};

export const SelectVersionForm = ({
  versionUuid,
}: {
  versionUuid?: string;
}) => {
  const { projectUuid, functionName: defaultFunctionName } = useParams({
    strict: false,
  });
  const navigate = useNavigate();
  const method = useForm<FunctionFormValues>({
    defaultValues: {
      newFunctionName: defaultFunctionName,
      functionName: defaultFunctionName,
      version: null,
    },
  });
  const functionName = useWatch({
    control: method.control,
    name: "functionName",
  });

  const newFunctionName = useWatch({
    control: method.control,
    name: "newFunctionName",
  });
  useEffect(() => {
    const subscription = method.watch((value, { name }) => {
      if (name === "functionName") {
        method.setValue("version", null);
        navigate({
          to: `/projects/${projectUuid}/functions/${value.functionName}`,
        });
      } else if (name === "version" && value.version) {
        navigate({
          to: `/projects/${projectUuid}/functions/${value.version.function_name}/versions/${value.version.uuid}`,
        });
      }
    });

    return () => subscription.unsubscribe();
  }, [method.watch]);

  const { data: versions } = useSuspenseQuery(
    versionsByFunctionNameQueryOptions(functionName, projectUuid)
  );
  const { data: uniqueFunctionNames } = useSuspenseQuery(
    uniqueFunctionNamesQueryOptions(projectUuid)
  );
  const uniqueFunctionNamesWithNew = [...uniqueFunctionNames];
  if (newFunctionName && !uniqueFunctionNames.includes(newFunctionName)) {
    uniqueFunctionNamesWithNew.push(newFunctionName);
  }
  useEffect(() => {
    const version = versions?.find((v) => v.uuid === versionUuid);
    if (!version) return;
    method.setValue("version", version);
  }, [versions, versionUuid]);
  const handleCancelClick = () => {
    method.setValue("newFunctionName", "");
  };
  const handleSaveClick = () => {
    method.setValue("functionName", newFunctionName);
  };
  const buttons = [
    <Button onClick={handleSaveClick}>Save</Button>,
    <Button onClick={handleCancelClick}>Cancel</Button>,
  ];
  const handleOpenChange = (isOpen: boolean) => {
    if (isOpen) {
      method.setValue("newFunctionName", "");
    }
  };
  return (
    <Form {...method}>
      <div className='flex gap-2'>
        <IconDialog
          onOpenChange={handleOpenChange}
          icon={<Plus />}
          title='Add a new function'
          description='Start by naming your function'
          buttonProps={{ variant: "default" }}
          tooltipContent='Create a new function'
          tooltipProps={{
            className: "bg-slate-500",
            side: "top",
            sideOffset: 10,
          }}
          dialogButtons={buttons}
        >
          <NewFunctionDialog />
        </IconDialog>
        <Controller
          control={method.control}
          name='functionName'
          render={({ field }) => (
            <Select value={field.value} onValueChange={field.onChange}>
              <SelectTrigger className='w-[200px]'>
                <SelectValue placeholder='Select a function' />
              </SelectTrigger>
              <SelectContent>
                {uniqueFunctionNamesWithNew.map((name) => (
                  <SelectItem key={name} value={name}>
                    {name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          )}
        />
        {versions && versions.length > 0 ? (
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
                  {versions.map((version, i) => (
                    <SelectItem
                      key={version.uuid}
                      value={JSON.stringify(version)}
                    >
                      v{i + 1}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}
          />
        ) : null}
      </div>
    </Form>
  );
};

const NewFunctionDialog = () => {
  const methods = useFormContext<FunctionFormValues>();
  return (
    <>
      <FormField
        control={methods.control}
        name='newFunctionName'
        rules={{
          required: "Function Name is required",
        }}
        render={({ field }) => (
          <FormItem>
            <FormLabel>Function Name</FormLabel>
            <FormControl>
              <Input
                {...field}
                value={field.value}
                onChange={field.onChange}
                placeholder='Enter function name'
              />
            </FormControl>
            <FormMessage />
          </FormItem>
        )}
      />
    </>
  );
};
