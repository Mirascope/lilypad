import { Button } from "@/components/ui/button";
import { userQueryOptions } from "@/utils/users";
import { loadStripe } from "@stripe/stripe-js";
import { useSuspenseQuery } from "@tanstack/react-query";
import { useMemo, useState } from "react";

loadStripe(
  "pk_test_51RMYFER6LYGqZiYL4aomVpnpfeqGA1lxLdv32En1f2q9NkDGp1ul0d3Ryf7rlr1az5HHZTQEZIdRGBrfabueZfFj00IwUTYnky"
);

export const SubscriptionManager = () => {
  const [loading, setLoading] = useState(false);
  const { data: user } = useSuspenseQuery(userQueryOptions());

  const activeOrganization = useMemo(
    () =>
      user.user_organizations?.find(
        (userOrg) => userOrg.organization_uuid === user.active_organization_uuid
      ),
    [user]
  );
  console.log(activeOrganization);
  const redirectToCustomerPortal = async () => {
    setLoading(true);

    try {
      // Call your backend to create a customer portal session
      const response = await fetch("/api/create-customer-portal-session", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          customerId:
            activeOrganization?.organization.billing.stripe_customer_id,
          // Include customer ID if needed
          // customerId: 'cus_...'
        }),
      });

      const { url } = await response.json();

      // Redirect to the customer portal
      window.location.href = url;
    } catch (error) {
      console.error("Error redirecting to customer portal:", error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="subscription-manager">
      <h2>Manage Your Subscription</h2>
      <Button
        onClick={redirectToCustomerPortal}
        disabled={loading}
        className="portal-button"
      >
        {loading ? "Loading..." : "Manage Subscription"}
      </Button>
    </div>
  );
};
