import { LilypadPricing } from "@/mirascope-ui/blocks/lilypad-pricing";
import { Alert, AlertDescription, AlertTitle } from "@/src/components/ui/alert";
import { Button } from "@/src/components/ui/button";
import { Typography } from "@/src/components/ui/typography";
import { licenseQueryOptions } from "@/src/ee/utils/organizations";
import { PlanType } from "@/src/types/types";
import { tier, useCreateCheckoutSession, useCreateCustomerPortal } from "@/src/utils/billing";
import { formatDate } from "@/src/utils/strings";
import { userQueryOptions } from "@/src/utils/users";
import { loadStripe } from "@stripe/stripe-js";
import { useSuspenseQuery } from "@tanstack/react-query";
import { useState } from "react";

loadStripe(
  "pk_test_51RMYFER6LYGqZiYL4aomVpnpfeqGA1lxLdv32En1f2q9NkDGp1ul0d3Ryf7rlr1az5HHZTQEZIdRGBrfabueZfFj00IwUTYnky"
);

export const StripeSubscriptionButton = ({
  buttonText,
  variant = "default",
  planType,
  disabled,
}: {
  buttonText?: string;
  variant?: "default" | "outline";
  planType: PlanType;
  disabled?: boolean;
}) => {
  const [loading, setLoading] = useState(false);
  const createCheckoutSession = useCreateCheckoutSession();

  const redirectToCustomerPortal = async () => {
    setLoading(true);

    try {
      // Call your backend to create a customer portal session
      const url = await createCheckoutSession.mutateAsync({
        plan_type: planType,
      });
      // Redirect to the customer portal
      window.location.href = url;
    } catch (error) {
      console.error("Error redirecting to customer portal:", error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Button
      onClick={redirectToCustomerPortal}
      disabled={disabled ?? loading}
      loading={loading}
      className="w-full"
      variant={variant}
    >
      {loading ? "Loading..." : buttonText}
    </Button>
  );
};
export const ManageSubscription = () => {
  const [loading, setLoading] = useState(false);
  const createCustomerPortal = useCreateCustomerPortal();
  const redirectToCustomerPortal = async () => {
    setLoading(true);

    try {
      const url = await createCustomerPortal.mutateAsync();
      // Redirect to the customer portal
      window.location.href = url;
    } catch (error) {
      console.error("Error redirecting to customer portal:", error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Button disabled={loading} onClick={redirectToCustomerPortal}>
      Manage Subscription
    </Button>
  );
};
export const SubscriptionManager = () => {
  const { data: user } = useSuspenseQuery(userQueryOptions());
  const userOrganization = user.user_organizations?.find(
    (userOrg) => userOrg.organization.uuid === user?.active_organization_uuid
  );
  const { data: licenseInfo } = useSuspenseQuery(licenseQueryOptions());
  const planType = tier[licenseInfo.tier] ?? "Free";
  const billing = userOrganization?.organization.billing;
  return (
    <div className="flex flex-col gap-4">
      <Typography variant="h3">Manage Plan</Typography>
      {billing?.cancel_at_period_end && (
        <Alert variant="warning">
          <AlertTitle>Subscription Cancelled</AlertTitle>
          <AlertDescription>
            Your subscription is set to cancel at the end of the current billing period{" "}
            {billing.subscription_current_period_end &&
              formatDate(billing.subscription_current_period_end)}
          </AlertDescription>
        </Alert>
      )}
      <LilypadPricing
        actions={{
          hosted: {
            free: {
              customButton: <ManageSubscription />,
              variant: "default",
            },
            pro: {
              customButton: (
                <StripeSubscriptionButton
                  planType={PlanType.PRO}
                  buttonText={planType === "Pro" ? "Current Plan" : "Change to Pro"}
                  disabled={planType === "Pro" || !!billing?.cancel_at_period_end}
                />
              ),
              variant: "default",
            },
            team: {
              customButton: (
                <StripeSubscriptionButton
                  planType={PlanType.TEAM}
                  buttonText={planType === "Team" ? "Current Plan" : "Change to Team"}
                  disabled={planType === "Team" || !!billing?.cancel_at_period_end}
                />
              ),
              variant: "default",
            },
          },
          selfHosted: {
            free: {
              buttonText: "Download",
              buttonLink: "/download",
              variant: "default",
            },
            pro: {
              buttonText: "Get License",
              buttonLink: "/pricing/self-hosted-pro",
              variant: "default",
            },
            team: {
              buttonText: "Request Demo",
              buttonLink: "/demo",
              variant: "outline",
            },
          },
        }}
      />
    </div>
  );
};
