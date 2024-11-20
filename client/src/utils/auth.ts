import api from "@/api";
import { LoginType, LoginResponse, UserSession } from "@/types/types";
import { queryOptions, useMutation } from "@tanstack/react-query";

export const postLogin = async (loginType: LoginType) => {
  return (await api.post<LoginResponse>(`/auth/login/${loginType}`)).data;
};

export const fetchCallbackCode = async (code: string) => {
  return (await api.get<UserSession>(`/auth/callback?code=${code}`)).data;
};

export const useLoginMutation = () => {
  return useMutation({
    mutationFn: async ({ loginType }: { loginType: LoginType }) =>
      await postLogin(loginType),
  });
};

export const callbackCodeQueryOptions = (code: string) =>
  queryOptions({
    queryKey: ["callback", "code"],
    queryFn: () => fetchCallbackCode(code),
  });
