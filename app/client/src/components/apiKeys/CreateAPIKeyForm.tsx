import { useAuth } from "@/auth";
import { APIKeyCreate } from "@/types/types";
import { useCreateApiKeyMutation } from "@/utils/api-keys";
import { environmentsQueryOptions } from "@/utils/environments";
import { projectsQueryOptions } from "@/utils/projects";
import { useSuspenseQuery } from "@tanstack/react-query";
import { Dispatch, SetStateAction } from "react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

interface APIKeyFormProps {
  setApiKey: Dispatch<SetStateAction<string | null>>;
  setProjectUuid: Dispatch<SetStateAction<string | null>>;
  onSuccess?: () => void;
  className?: string;
}

export const CreateAPIKeyForm = ({
  setApiKey,
  setProjectUuid,
  onSuccess,
  className,
}: APIKeyFormProps) => {
  const { data: projects } = useSuspenseQuery(projectsQueryOptions());
  const { data: environments } = useSuspenseQuery(environmentsQueryOptions());
  const { activeProject } = useAuth();
  const createApiKey = useCreateApiKeyMutation();

  const methods = useForm<APIKeyCreate>({
    defaultValues: {
      name: "",
      project_uuid: activeProject?.uuid,
      environment_uuid: environments[0]?.uuid || null,
    },
  });

  const onSubmit = async (data: APIKeyCreate) => {
    try {
      const generatedKey = await createApiKey.mutateAsync(data);
      setApiKey(generatedKey);
      setProjectUuid(data.project_uuid);
      toast.success("Successfully created API key");
      onSuccess?.();
    } catch (error) {
      toast.error("Failed to create API key");
    }
  };

  return (
    <Form {...methods}>
      <form onSubmit={methods.handleSubmit(onSubmit)} className={`space-y-6 ${className}`}>
        <FormField
          key="name"
          control={methods.control}
          name="name"
          rules={{
            required: {
              value: true,
              message: "Name is required",
            },
          }}
          render={({ field }) => (
            <FormItem>
              <FormLabel>Name</FormLabel>
              <FormControl>
                <Input {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        <FormField
          key="project_uuid"
          control={methods.control}
          name="project_uuid"
          rules={{
            required: {
              value: true,
              message: "Project is required",
            },
          }}
          render={({ field }) => (
            <FormItem>
              <FormLabel>Project</FormLabel>
              <FormControl>
                <Select value={field.value ?? ""} onValueChange={field.onChange}>
                  <SelectTrigger className="w-full">
                    <SelectValue placeholder="Select a project" />
                  </SelectTrigger>
                  <SelectContent>
                    {projects.map((project) => (
                      <SelectItem key={project.uuid} value={project.uuid}>
                        {project.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        <FormField
          key="environment_uuid"
          control={methods.control}
          name="environment_uuid"
          rules={{
            required: {
              value: true,
              message: "Environment is required",
            },
          }}
          render={({ field }) => (
            <FormItem>
              <FormLabel>Environment</FormLabel>
              <FormControl>
                <Select value={field.value ?? ""} onValueChange={field.onChange}>
                  <SelectTrigger className="w-full">
                    <SelectValue placeholder="Select an environment" />
                  </SelectTrigger>
                  <SelectContent>
                    {environments.map((environment) => (
                      <SelectItem key={environment.uuid} value={environment.uuid}>
                        {environment.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        <div className="flex justify-end">
          <Button type="submit" loading={methods.formState.isSubmitting} className="w-full">
            {methods.formState.isSubmitting ? "Generating..." : "Generate Key"}
          </Button>
        </div>
      </form>
    </Form>
  );
};
