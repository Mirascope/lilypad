import api from "@/src/api";
import { EventSummaryResponse, StripeCheckoutSession } from "@/src/types/types";
import { queryOptions, useMutation } from "@tanstack/react-query";

export const fetchEventSummaries = async () =>
  (await api.get<EventSummaryResponse>("/stripe/event-summaries")).data;

export const createCustomerPortal = async () => {
  return (await api.post<string>(`/stripe/customer-portal`)).data;
};

export const createCheckoutSession = async (checkoutSession: StripeCheckoutSession) => {
  return (await api.post<string>(`/stripe/create-checkout-session`, checkoutSession)).data;
};

export const eventSummariesQueryOptions = () =>
  queryOptions({
    queryKey: ["event-summaries"],
    queryFn: fetchEventSummaries,
  });

export const useCreateCheckoutSession = () => {
  return useMutation({
    mutationFn: (checkoutSession: StripeCheckoutSession) => createCheckoutSession(checkoutSession),
  });
};

export const useCreateCustomerPortal = () => {
  return useMutation({
    mutationFn: () => createCustomerPortal(),
  });
};
