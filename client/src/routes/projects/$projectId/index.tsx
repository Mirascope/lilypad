import api from "@/api";
import {
  Select,
  SelectValue,
  SelectTrigger,
  SelectContent,
  SelectItem,
} from "@/components/ui/select";
import { ProjectPublic, VersionPublic } from "@/types/types";
import { useQuery } from "@tanstack/react-query";
import { createFileRoute, Outlet, useParams } from "@tanstack/react-router";
import { useMemo } from "react";
import { Controller, FormProvider, useForm, useWatch } from "react-hook-form";
export const Route = createFileRoute("/projects/$projectId/")({
  component: () => <Project />,
});

type ProjectForm = {
  function_name: string;
  hash: string;
};

export const Project = () => {
  const { projectId } = useParams({ from: Route.id });
  const {
    data: project,
    isLoading,
    error,
  } = useQuery<ProjectPublic>({
    queryKey: ["project", projectId],
    queryFn: async () => (await api.get(`/projects/${projectId}`)).data,
  });
  const method = useForm<ProjectForm>();
  const functionName = useWatch({
    control: method.control,
    name: "function_name",
  });
  const {
    data: versions,
    isVersionsLoading,
    errorVersion,
  } = useQuery<VersionPublic>({
    queryKey: ["project", projectId, "versions"],
    queryFn: async () =>
      (
        await api.get(
          `/projects/${projectId}/llm-fns/${functionName}    /versions`
        )
      ).data,
    enabled: !!project && !!functionName,
  });

  const uniqueFunctionNames = Array.from(
    new Set(project?.llm_fns?.map((fn) => fn.function_name) ?? [])
  );

  if (isLoading) return <div>Loading...</div>;
  if (error) return <div>{error.message}</div>;
  if (!project) return <div>Project not found</div>;
  return (
    <div>
      <FormProvider {...method}>
        <Controller
          control={method.control}
          name='function_name'
          render={({ field }) => (
            <Select value={field.value} onValueChange={field.onChange}>
              <SelectTrigger className='w-full'>
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
      </FormProvider>
      <Outlet />
    </div>
  );
};
