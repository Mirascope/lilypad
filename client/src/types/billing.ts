/**
 * Types for billing-related functionality
 */

/**
 * Plan type representing a subscription plan
 */
export interface Plan {
  id: string;
  name: string;
  price: string;
  description: string;
  features: string[];
}

/**
 * Subscription status type
 */
export type SubscriptionStatus = 'none' | 'active' | 'trialing' | 'past_due' | 'canceled' | 'incomplete' | 'incomplete_expired';

/**
 * Subscription information returned from the API
 */
export interface Subscription {
  plan: string;
  status: SubscriptionStatus;
  current_period_end: number | null;
}

/**
 * Response from the setup intent API
 */
export interface SetupIntentResponse {
  clientSecret: string;
}

/**
 * Request parameters for the subscribe API
 */
export interface SubscribeRequest {
  plan: string;
  pm_id: string;
}

/**
 * Response from the subscribe API
 */
export interface SubscribeResponse {
  subscriptionId: string;
  status: SubscriptionStatus;
  clientSecret: string | null;
}

/**
 * Props for the PaymentForm component
 */
export interface PaymentFormProps {
  clientSecret: string;
  onSuccess: (paymentMethodId: string) => void;
}