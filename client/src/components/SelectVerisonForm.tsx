import { useNavigate, useParams } from "@tanstack/react-router";
import { useSuspenseQuery } from "@tanstack/react-query";
import {
  uniquePromptNamesQueryOptions,
  promptsByNameQueryOptions,
} from "@/utils/prompts";
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
import { PromptPublic } from "@/types/types";
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
  newPromptName: string;
  promptName: string;
  version: PromptPublic | null;
};

export const SelectVersionForm = ({ promptUuid }: { promptUuid?: string }) => {
  const { projectUuid, promptName: defaultPromptName } = useParams({
    strict: false,
  });
  const navigate = useNavigate();
  const method = useForm<FunctionFormValues>({
    defaultValues: {
      newPromptName: defaultPromptName,
      promptName: defaultPromptName,
      version: null,
    },
  });
  const promptName = useWatch({
    control: method.control,
    name: "promptName",
  });

  const newPromptName = useWatch({
    control: method.control,
    name: "newPromptName",
  });
  useEffect(() => {
    const subscription = method.watch((value, { name }) => {
      if (name === "promptName") {
        method.setValue("version", null);
        navigate({
          to: `/projects/${projectUuid}/prompts/${value.promptName}`,
        });
      } else if (name === "version" && value.version) {
        navigate({
          to: `/projects/${projectUuid}/prompts/${value.version.name}/versions/${value.version.uuid}`,
        });
      }
    });

    return () => subscription.unsubscribe();
  }, [method.watch]);

  const { data: prompts } = useSuspenseQuery(
    promptsByNameQueryOptions(promptName, projectUuid)
  );
  const { data: uniquePromptNames } = useSuspenseQuery(
    uniquePromptNamesQueryOptions(projectUuid)
  );
  const uniquePromptNamesWithNew = [...uniquePromptNames];
  if (newPromptName && !uniquePromptNames.includes(newPromptName)) {
    uniquePromptNamesWithNew.push(newPromptName);
  }
  useEffect(() => {
    const prompt = prompts?.find((prompt) => prompt.uuid === promptUuid);
    if (!prompt) return;
    method.setValue("version", prompt);
  }, [prompts, promptUuid]);
  const handleCancelClick = () => {
    method.setValue("newPromptName", "");
  };
  const handleSaveClick = () => {
    method.setValue("promptName", newPromptName);
  };
  const buttons = [
    <Button onClick={handleSaveClick}>Save</Button>,
    <Button onClick={handleCancelClick}>Cancel</Button>,
  ];
  const handleOpenChange = (isOpen: boolean) => {
    if (isOpen) {
      method.setValue("newPromptName", "");
    }
  };
  return (
    <Form {...method}>
      <div className='flex gap-2'>
        <IconDialog
          onOpenChange={handleOpenChange}
          icon={<Plus />}
          title='Add a new prompt'
          description='Start by naming your prompt'
          buttonProps={{ variant: "default" }}
          tooltipContent='Create a new prompt'
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
          name='promptName'
          render={({ field }) => (
            <Select value={field.value} onValueChange={field.onChange}>
              <SelectTrigger className='w-[200px]'>
                <SelectValue placeholder='Select a prompt' />
              </SelectTrigger>
              <SelectContent>
                {uniquePromptNamesWithNew.map((name) => (
                  <SelectItem key={name} value={name}>
                    {name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          )}
        />
        {prompts && prompts.length > 0 ? (
          <Controller
            control={method.control}
            name='version'
            render={({ field }) => (
              <Select
                value={JSON.stringify(field.value)}
                onValueChange={(value) => field.onChange(JSON.parse(value))}
                disabled={!promptName || !prompts}
              >
                <SelectTrigger className='w-[100px]'>
                  <SelectValue placeholder='version' />
                </SelectTrigger>
                <SelectContent>
                  {prompts.map((prompt, i) => (
                    <SelectItem
                      key={prompt.uuid}
                      value={JSON.stringify(prompt)}
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
        name='newPromptName'
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
