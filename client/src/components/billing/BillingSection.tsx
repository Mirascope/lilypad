import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { toast } from "sonner";
import api from "@/api";
import { userQueryOptions } from "@/utils/users";
import { useMutation, useSuspenseQuery } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { Elements, PaymentElement, useElements, useStripe } from "@stripe/react-stripe-js";
import { loadStripe } from "@stripe/stripe-js";
import { Loader2 } from "lucide-react";
import { PaymentFormProps, Plan, SetupIntentResponse, SubscribeRequest, SubscribeResponse, Subscription } from "@/types/billing";

// Initialize Stripe
const stripePromise = loadStripe(import.meta.env.VITE_STRIPE_PUBLIC_KEY as string);

// Plan details
const plans: Plan[] = [
  {
    id: "free",
    name: "Free",
    price: "$0",
    description: "For individuals and small teams",
    features: [
      "2 Users",
      "30K spans / month",
      "30 Day Data Retention",
    ],
  },
  {
    id: "pro",
    name: "Pro",
    price: "$49/month",
    description: "For growing teams",
    features: [
      "10 Users",
      "100K spans / month",
      "90 Day Data Retention",
    ],
  },
  {
    id: "team",
    name: "Team",
    price: "$199/month",
    description: "For larger teams",
    features: [
      "Unlimited Users",
      "1M spans / month",
      "180 Day Data Retention",
    ],
  },
];

// Payment form component
const PaymentForm = ({ onSuccess }: PaymentFormProps) => {
  const stripe = useStripe();
  const elements = useElements();
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!stripe || !elements) {
      return;
    }

    setIsLoading(true);

    try {
      const { error, paymentIntent } = await stripe.confirmPayment({
        elements,
        confirmParams: {
          return_url: window.location.origin + "/settings/$",
        },
        redirect: "if_required",
      });

      if (error) {
        toast.error(error.message);
      } else if (paymentIntent && paymentIntent.status === "succeeded") {
        toast.success("Your subscription has been updated");
        onSuccess(paymentIntent.payment_method as string);
      }
    } catch (error: unknown) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
      toast.error(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <form onSubmit={e => { void handleSubmit(e); }}>
      <PaymentElement />
      <Button 
        type="submit" 
        className="mt-4 w-full" 
        disabled={!stripe || isLoading}
      >
        {isLoading ? (
          <>
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            Processing...
          </>
        ) : (
          "Pay now"
        )}
      </Button>
    </form>
  );
};

// Subscription management component
export const BillingSection = () => {
  useSuspenseQuery(userQueryOptions());
  const [selectedPlan, setSelectedPlan] = useState<string | null>(null);
  const [clientSecret, setClientSecret] = useState<string>("");
  const [currentSubscription, setCurrentSubscription] = useState<Subscription | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  // Fetch current subscription
  useEffect(() => {
    const fetchSubscription = async () => {
      try {
        const response = await api.get<Subscription>("/api/billing/subscription");
        setCurrentSubscription(response.data);
      } catch {
        toast.error("Failed to fetch subscription. Please try again later");
      } finally {
        setIsLoading(false);
      }
    };

    void fetchSubscription();
  }, []);

  // Create setup intent mutation
  const setupIntentMutation = useMutation({
    mutationFn: async () => {
      const response = await api.post<SetupIntentResponse>("/api/billing/setup-intent");
      return response.data;
    },
  });

  // Subscribe mutation
  const subscribeMutation = useMutation({
    mutationFn: async ({ plan, paymentMethodId }: { plan: string; paymentMethodId: string }) => {
      const response = await api.post<SubscribeResponse>("/api/billing/subscribe", {
        plan,
        pm_id: paymentMethodId,
      } as SubscribeRequest);
      return response.data;
    },
  });

  // Handle plan selection
  const handleSelectPlan = async (planId: string) => {
    if (planId === currentSubscription?.plan) {
      toast.info(`You are already subscribed to the ${planId} plan`);
      return;
    }

    setSelectedPlan(planId);

    try {
      const { clientSecret } = await setupIntentMutation.mutateAsync();
      setClientSecret(clientSecret);
    } catch {
      toast.error("Failed to set up payment. Please try again later");
    }
  };

  // Handle successful payment
  const handlePaymentSuccess = async (paymentMethodId: string) => {
    try {
      await subscribeMutation.mutateAsync({
        plan: selectedPlan!,
        paymentMethodId,
      });

      // Refresh subscription data
      const response = await api.get<Subscription>("/api/billing/subscription");
      setCurrentSubscription(response.data);

      setSelectedPlan(null);
      setClientSecret("");

      toast.success(`You are now subscribed to the ${selectedPlan} plan`);
    } catch {
      toast.error("Failed to update subscription. Please try again later");
    }
  };

  if (isLoading) {
    return (
      <div className="flex justify-center items-center p-8">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold tracking-tight">Billing</h2>
        <p className="text-muted-foreground">
          Manage your subscription and payment methods
        </p>
      </div>

      {currentSubscription && (
        <Card>
          <CardHeader>
            <CardTitle>Current Subscription</CardTitle>
            <CardDescription>
              Your current plan and billing details
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="font-medium">Plan:</span>
                <span className="capitalize">{currentSubscription.plan}</span>
              </div>
              <div className="flex justify-between">
                <span className="font-medium">Status:</span>
                <span className="capitalize">{currentSubscription.status}</span>
              </div>
              {currentSubscription.current_period_end && (
                <div className="flex justify-between">
                  <span className="font-medium">Next billing date:</span>
                  <span>
                    {new Date(currentSubscription.current_period_end * 1000).toLocaleDateString()}
                  </span>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      <Tabs defaultValue="plans">
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="plans">Plans</TabsTrigger>
          <TabsTrigger value="payment" disabled={!selectedPlan}>
            Payment
          </TabsTrigger>
        </TabsList>

        <TabsContent value="plans" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-3">
            {plans.map((plan) => (
              <Card 
                key={plan.id} 
                className={`${
                  currentSubscription?.plan === plan.id 
                    ? "border-primary" 
                    : ""
                }`}
              >
                <CardHeader>
                  <CardTitle>{plan.name}</CardTitle>
                  <CardDescription>{plan.description}</CardDescription>
                </CardHeader>
                <CardContent>
                  <p className="text-2xl font-bold">{plan.price}</p>
                  <ul className="mt-4 space-y-2">
                    {plan.features.map((feature, index) => (
                      <li key={index} className="flex items-center">
                        <span className="mr-2">✓</span>
                        {feature}
                      </li>
                    ))}
                  </ul>
                </CardContent>
                <CardFooter>
                  <Button 
                    className="w-full" 
                    onClick={() => { void handleSelectPlan(plan.id); }}
                    disabled={
                      currentSubscription?.plan === plan.id ||
                      subscribeMutation.isPending
                    }
                    variant={
                      currentSubscription?.plan === plan.id 
                        ? "outline" 
                        : "default"
                    }
                  >
                    {currentSubscription?.plan === plan.id
                      ? "Current Plan"
                      : "Select Plan"}
                  </Button>
                </CardFooter>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="payment">
          {clientSecret && (
            <Card>
              <CardHeader>
                <CardTitle>Payment Information</CardTitle>
                <CardDescription>
                  Enter your payment details to subscribe to the {
                    plans.find(p => p.id === selectedPlan)?.name
                  } plan
                </CardDescription>
              </CardHeader>
              <CardContent>
                <Elements 
                  stripe={stripePromise} 
                  options={{ clientSecret }}
                >
                  <PaymentForm 
                    clientSecret={clientSecret} 
                    onSuccess={(paymentMethodId) => { void handlePaymentSuccess(paymentMethodId); }}
                  />
                </Elements>
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
};
