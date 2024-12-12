import api from "@/api";
import { GenerationPublic } from "@/types/types";
import {
  queryOptions,
  useMutation,
  useQueryClient,
} from "@tanstack/react-query";
import { AxiosResponse } from "axios";

export const fetchGenerationByName = async (
  generationName: string,
  projectUuid?: string
) => {
  if (!projectUuid || !generationName) return [];

  return (
    await api.get<GenerationPublic[]>(
      `/projects/${projectUuid}/generations/name/${generationName}/versions`
    )
  ).data;
};

export const fetchGeneration = async (
  projectUuid: string,
  generationUuid?: string
) => {
  if (!generationUuid) return null;
  return (
    await api.get<GenerationPublic>(
      `/projects/${projectUuid}/generations/${generationUuid}`
    )
  ).data;
};

export const fetchUniqueGenerationNames = async (projectUuid?: string) => {
  if (!projectUuid) return [];
  return (await api.get<string[]>(`/projects/${projectUuid}/generations/names`))
    .data;
};
// export const createVersion = async (
//   projectUuid: string,
//   versionCreate: FunctionAndPromptVersionCreate
// ): Promise<GenerationPublic> => {
//   return (
//     await api.post<
//       FunctionAndPromptVersionCreate,
//       AxiosResponse<GenerationPublic>
//     >(`projects/${projectUuid}/versions`, versionCreate)
//   ).data;
// };

export const patchVersion = async (
  projectUuid: string,
  versionUuid: string
): Promise<GenerationPublic> => {
  return (
    await api.patch<undefined, AxiosResponse<GenerationPublic>>(
      `projects/${projectUuid}/versions/${versionUuid}/active`
    )
  ).data;
};

export const runGeneration = async (
  projectUuid: string,
  generationUuid: string,
  values: Record<string, string>
): Promise<string> => {
  return (
    await api.post<Record<string, string>, AxiosResponse<string>>(
      `projects/${projectUuid}/generations/${generationUuid}/run`,
      values
    )
  ).data;
};

export const versionsByFunctionNameQueryOptions = (
  generationName: string,
  projectUuid?: string
) =>
  queryOptions({
    queryKey: [
      "projects",
      projectUuid,
      "generations",
      generationName,
      "versions",
    ],
    queryFn: () => fetchGenerationByName(generationName, projectUuid),
    enabled: !!generationName,
  });

export const generationQueryOptions = (
  projectUuid: string,
  generationUuid?: string,
  options = {}
) =>
  queryOptions({
    queryKey: ["projects", projectUuid, "generations", generationUuid],
    queryFn: () => fetchGeneration(projectUuid, generationUuid),
    ...options,
  });

export const usePatchActiveVersion = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      projectUuid,
      generationUuid,
    }: {
      projectUuid: string;
      generationUuid: string;
    }) => await patchVersion(projectUuid, generationUuid),
    onSuccess: (newVersion, { projectUuid }) => {
      queryClient.invalidateQueries({
        queryKey: ["projects", projectUuid, "generations", newVersion.uuid],
      });
    },
  });
};

export const uniqueGenerationNamesQueryOptions = (projectUuid?: string) =>
  queryOptions({
    queryKey: ["project", projectUuid, "generations"],
    queryFn: async () => await fetchUniqueGenerationNames(projectUuid),
  });

// export const useCreateVersion = () => {
//   const queryClient = useQueryClient();

//   return useMutation({
//     mutationFn: async ({
//       projectUuid,
//       versionCreate,
//     }: {
//       projectUuid: string;
//       versionCreate: FunctionAndPromptVersionCreate;
//     }) => await createVersion(projectUuid, versionCreate),
//     onSuccess: (newVersion, { projectUuid }) => {
//       queryClient.invalidateQueries({
//         queryKey: [
//           "projects",
//           projectUuid,
//           "generations",
//           newVersion.function.name,
//           "versions",
//         ],
//       });
//     },
//   });
// };

export const useRunMutation = () => {
  return useMutation({
    mutationFn: async ({
      projectUuid,
      generationUuid,
      values,
    }: {
      projectUuid: string;
      generationUuid: string;
      values: Record<string, string>;
    }) => await runGeneration(projectUuid, generationUuid, values),
  });
};
