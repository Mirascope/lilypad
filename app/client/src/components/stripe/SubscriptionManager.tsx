import {
  cloudHostedFeatures,
  FeatureComparisonTable,
  LilypadCloudPricing,
} from "@/mirascope-ui/blocks/lilypad-pricing";
import MeterUsageProgress from "@/src/components/stripe/MeterUsageProgress";
import { Alert, AlertDescription, AlertTitle } from "@/src/components/ui/alert";
import { Button } from "@/src/components/ui/button";
import { Typography } from "@/src/components/ui/typography";
import { licenseQueryOptions } from "@/src/ee/utils/organizations";
import { Tier } from "@/src/types/types";
import { useCreateCheckoutSession, useCreateCustomerPortal } from "@/src/utils/billing";
import { formatDate } from "@/src/utils/strings";
import { userQueryOptions } from "@/src/utils/users";
import { loadStripe } from "@stripe/stripe-js";
import { useSuspenseQuery } from "@tanstack/react-query";
import { useState } from "react";

loadStripe(import.meta.env.VITE_STRIPE_PUBLIC_KEY as string).catch(() => {
  console.error("Failed to load Stripe");
});

export const StripeSubscriptionButton = ({
  buttonText,
  variant = "default",
  tier,
  disabled,
}: {
  buttonText?: string;
  variant?: "default" | "outline";
  tier: Tier;
  disabled?: boolean;
}) => {
  const [loading, setLoading] = useState(false);
  const createCheckoutSession = useCreateCheckoutSession();

  const redirectToCustomerPortal = async () => {
    setLoading(true);

    try {
      // Call your backend to create a customer portal session
      const url = await createCheckoutSession.mutateAsync({
        tier,
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
  const tier = licenseInfo?.tier;
  const billing = userOrganization?.organization.billing;
  return (
    <div className="flex flex-col gap-4">
      <Typography variant="h3">Manage Plan</Typography>
      <Typography variant="h5">Current Usage</Typography>
      <MeterUsageProgress />
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
      <LilypadCloudPricing
        hostedActions={{
          free: {
            button: <ManageSubscription />,
          },
          pro: {
            button: (
              <StripeSubscriptionButton
                tier={Tier.PRO}
                buttonText={tier === Tier.PRO ? "Current Plan" : "Change to Pro"}
                disabled={tier === Tier.PRO || !!billing?.cancel_at_period_end}
              />
            ),
          },
          team: {
            button: (
              <StripeSubscriptionButton
                tier={Tier.TEAM}
                buttonText={tier === Tier.TEAM ? "Current Plan" : "Change to Team"}
                disabled={tier === Tier.TEAM || !!billing?.cancel_at_period_end}
              />
            ),
          },
        }}
      />
      <FeatureComparisonTable features={cloudHostedFeatures} />
    </div>
  );
};
