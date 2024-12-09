import api from "@/api";
import { SettingsPublic } from "@/types/types";
import { queryOptions } from "@tanstack/react-query";

export const getSettings = async () => {
  return (await api.get<SettingsPublic>(`/settings`)).data;
};

export const settingsQueryOptions = () =>
  queryOptions({
    queryKey: ["settings"],
    queryFn: getSettings,
  });
