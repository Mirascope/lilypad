import { useNavigate, useParams } from "@tanstack/react-router";
import { useSuspenseQuery } from "@tanstack/react-query";
import {
  uniqueGenerationNamesQueryOptions,
  versionsByFunctionNameQueryOptions,
} from "@/utils/generations";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectValue,
  SelectTrigger,
  SelectContent,
  SelectItem,
} from "@/components/ui/select";
import { Plus } from "lucide-react";
import { Controller, useForm, useFormContext, useWatch } from "react-hook-form";
import { useEffect } from "react";
import { GenerationPublic } from "@/types/types";
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
  newGenerationName: string;
  generationName: string;
  version: GenerationPublic | null;
};

export const SelectVersionForm = ({
  versionUuid,
}: {
  versionUuid?: string;
}) => {
  const { projectUuid, generationName: defaultFunctionName } = useParams({
    strict: false,
  });
  const navigate = useNavigate();
  const method = useForm<FunctionFormValues>({
    defaultValues: {
      newGenerationName: defaultFunctionName,
      functionName: defaultFunctionName,
      version: null,
    },
  });
  const functionName = useWatch({
    control: method.control,
    name: "generationName",
  });

  const newFunctionName = useWatch({
    control: method.control,
    name: "newGenerationName",
  });
  useEffect(() => {
    const subscription = method.watch((value, { name }) => {
      if (name === "generationName") {
        method.setValue("version", null);
        navigate({
          to: `/projects/${projectUuid}/functions/${value.generationName}`,
        });
      } else if (name === "version" && value.version) {
        navigate({
          to: `/projects/${projectUuid}/generations/${value.version.name}/versions/${value.version.uuid}`,
        });
      }
    });

    return () => subscription.unsubscribe();
  }, [method.watch]);

  const { data: versions } = useSuspenseQuery(
    versionsByFunctionNameQueryOptions(functionName, projectUuid)
  );
  const { data: uniqueGenerationNames } = useSuspenseQuery(
    uniqueGenerationNamesQueryOptions(projectUuid)
  );
  const uniqueGenerationNamesWithNew = [...uniqueGenerationNames];
  if (newFunctionName && !uniqueGenerationNames.includes(newFunctionName)) {
    uniqueGenerationNamesWithNew.push(newFunctionName);
  }
  useEffect(() => {
    const version = versions?.find((v) => v.uuid === versionUuid);
    if (!version) return;
    method.setValue("version", version);
  }, [versions, versionUuid]);
  const handleCancelClick = () => {
    method.setValue("newGenerationName", "");
  };
  const handleSaveClick = () => {
    method.setValue("generationName", newFunctionName);
  };
  const buttons = [
    <Button onClick={handleSaveClick}>Save</Button>,
    <Button onClick={handleCancelClick}>Cancel</Button>,
  ];
  const handleOpenChange = (isOpen: boolean) => {
    if (isOpen) {
      method.setValue("newGenerationName", "");
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
          <NewGenerationDialog />
        </IconDialog>
        <Controller
          control={method.control}
          name='generationName'
          render={({ field }) => (
            <Select value={field.value} onValueChange={field.onChange}>
              <SelectTrigger className='w-[200px]'>
                <SelectValue placeholder='Select a function' />
              </SelectTrigger>
              <SelectContent>
                {uniqueGenerationNamesWithNew.map((name) => (
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

const NewGenerationDialog = () => {
  const methods = useFormContext<FunctionFormValues>();
  return (
    <>
      <FormField
        control={methods.control}
        name='newGenerationName'
        rules={{
          required: "Generation Name is required",
        }}
        render={({ field }) => (
          <FormItem>
            <FormLabel>Generation Name</FormLabel>
            <FormControl>
              <Input
                {...field}
                value={field.value}
                onChange={field.onChange}
                placeholder='Enter generation name'
              />
            </FormControl>
            <FormMessage />
          </FormItem>
        )}
      />
    </>
  );
};
