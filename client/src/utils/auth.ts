import api from "@/api";
import { LoginType, LoginResponse, UserSession } from "@/types/types";
import {
  queryOptions,
  useMutation,
  useQueryClient,
} from "@tanstack/react-query";

export const postLogin = async (loginType: LoginType, deviceCode?: string) => {
  return (
    await api.post<LoginResponse>(
      `/auth/login/${loginType}${deviceCode ? `?deviceCode=${deviceCode}` : ""}`
    )
  ).data;
};

export const fetchCallbackCode = async (code: string, deviceCode?: string) => {
  const params = new URLSearchParams({ code });
  if (deviceCode) {
    params.append("deviceCode", deviceCode);
  }
  return (await api.get<UserSession>(`/auth/callback?${params.toString()}`))
    .data;
};

export const updateActiveOrganization = async (organizationId: string) => {
  return (await api.put<UserSession>(`/auth/organizations/${organizationId}`))
    .data;
};

export const useLoginMutation = () => {
  return useMutation({
    mutationFn: async ({
      loginType,
      deviceCode,
    }: {
      loginType: LoginType;
      deviceCode?: string;
    }) => await postLogin(loginType, deviceCode),
  });
};

export const useUpdateActiveOrganizationMutation = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ organizationId }: { organizationId: string }) =>
      await updateActiveOrganization(organizationId),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["user"] });
    },
  });
};

export const callbackCodeQueryOptions = (code: string, deviceCode?: string) =>
  queryOptions({
    queryKey: ["user"],
    queryFn: () => fetchCallbackCode(code, deviceCode),
  });
