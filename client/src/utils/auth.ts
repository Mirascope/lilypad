import api from "@/api";
import { DeviceCodeTable, UserPublic } from "@/types/types";
import {
  queryOptions,
  useMutation,
  useQueryClient,
} from "@tanstack/react-query";

export const fetchCallbackCode = async (code?: string, deviceCode?: string) => {
  if (!code) {
    return null;
  }
  const params = new URLSearchParams({ code });
  if (deviceCode) {
    params.append("deviceCode", deviceCode);
  }
  return (
    await api.get<UserPublic>(`/auth/github/callback?${params.toString()}`)
  ).data;
};

export const updateActiveOrganization = async (organizationUuid: string) => {
  return (await api.put<UserPublic>(`/users/${organizationUuid}`)).data;
};

export const postDeviceCode = async (deviceCode: string) => {
  return (await api.post<DeviceCodeTable>(`/device-codes/${deviceCode}`)).data;
};

export const useUpdateActiveOrganizationMutation = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ organizationUuid }: { organizationUuid: string }) =>
      await updateActiveOrganization(organizationUuid),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["user"] });
    },
  });
};

export const useDeviceCodeMutation = () => {
  return useMutation({
    mutationFn: async ({ deviceCode }: { deviceCode: string }) =>
      await postDeviceCode(deviceCode),
  });
};

export const callbackCodeQueryOptions = (code?: string, deviceCode?: string) =>
  queryOptions({
    queryKey: ["user"],
    queryFn: () => fetchCallbackCode(code, deviceCode),
    enabled: Boolean(code),
  });
