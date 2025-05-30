import api from "@/api";
// import { StripeCheckoutSession } from "@/types/types";
import { useMutation } from "@tanstack/react-query";

export const createCustomerPortal = async () => {
  return (await api.post<string>(`/stripe/customer-portal`)).data;
};

// export const createCheckoutSession = async (checkoutSession: StripeCheckoutSession) => {
//   return (await api.post<string>(`/stripe/create-checkout-session`, checkoutSession)).data;
// };

// export const useCreateCheckoutSession = () => {
//   return useMutation({
//     mutationFn: (checkoutSession: StripeCheckoutSession) => createCheckoutSession(checkoutSession),
//   });
// };

export const useCreateCustomerPortal = () => {
  return useMutation({
    mutationFn: () => createCustomerPortal(),
  });
};
