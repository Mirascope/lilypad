import api from "@/src/api";
import { SettingsPublic } from "@/src/types/types";
import { queryOptions } from "@tanstack/react-query";

export const getSettings = async () => {
  return (await api.get<SettingsPublic>(`/settings`)).data;
};

export const settingsQueryOptions = () =>
  queryOptions({
    queryKey: ["settings"],
    queryFn: getSettings,
  });
