// import LilypadDialog from "@/components/LilypadDialog";
// import { Button } from "@/components/ui/button";
// import { cn } from "@/lib/utils";
// import { PlanType } from "@/types/types";
// import { useCreateCheckoutSession, useCreateCustomerPortal } from "@/utils/billing";
// import { userQueryOptions } from "@/utils/users";
// import { loadStripe } from "@stripe/stripe-js";
// import { useSuspenseQuery } from "@tanstack/react-query";
// import { useState } from "react";

// loadStripe(
//   "pk_test_51RMYFER6LYGqZiYL4aomVpnpfeqGA1lxLdv32En1f2q9NkDGp1ul0d3Ryf7rlr1az5HHZTQEZIdRGBrfabueZfFj00IwUTYnky"
// );

// const PricingTier = ({
//   name,
//   price,
//   description,
//   buttonText,
//   badge,
//   variant = "default",
//   planType,
//   customButton,
//   disabled,
// }: {
//   name: string;
//   price: string;
//   description: string;
//   buttonText?: string;
//   badge?: "Open Beta" | "Closed Beta";
//   variant?: "default" | "outline";
//   planType: PlanType;
//   customButton?: React.ReactNode;
//   disabled?: boolean;
// }) => {
//   const [loading, setLoading] = useState(false);
//   const createCheckoutSession = useCreateCheckoutSession();
//   const redirectToCustomerPortal = async () => {
//     setLoading(true);

//     try {
//       // Call your backend to create a customer portal session
//       const url = await createCheckoutSession.mutateAsync({
//         plan_type: planType,
//       });
//       // Redirect to the customer portal
//       window.location.href = url;
//     } catch (error) {
//       console.error("Error redirecting to customer portal:", error);
//     } finally {
//       setLoading(false);
//     }
//   };
//   return (
//     <div className="overflow-hidden rounded-lg border border-border bg-background shadow-sm">
//       <div className={cn("bg-background px-6 py-8")}>
//         <div className="mb-2 flex items-center gap-2">
//           <h3 className={cn("text-xl font-semibold text-foreground")}>{name}</h3>
//           {badge && (
//             <span
//               className={cn(
//                 "rounded-md px-2 py-1 text-xs font-medium",
//                 badge === "Open Beta"
//                   ? "bg-primary/20 text-primary"
//                   : "bg-muted text-muted-foreground"
//               )}
//             >
//               {badge}
//             </span>
//           )}
//         </div>
//         <p className="mb-5 text-muted-foreground">{description}</p>
//         <div className="mb-6">
//           <span className="text-3xl font-bold text-foreground">{price}</span>
//           {price !== "TBD" && price !== "N/A" && (
//             <span className="ml-1 text-sm text-muted-foreground">/ month</span>
//           )}
//         </div>
//         {customButton ?? (
//           <Button
//             onClick={redirectToCustomerPortal}
//             disabled={disabled ?? loading}
//             loading={loading}
//             className="w-full"
//             variant={variant}
//           >
//             {loading ? "Loading..." : buttonText}
//           </Button>
//         )}
//       </div>
//     </div>
//   );
// };
// export const ManageSubscription = () => {
//   const [loading, setLoading] = useState(false);
//   const createCustomerPortal = useCreateCustomerPortal();
//   const redirectToCustomerPortal = async () => {
//     setLoading(true);

//     try {
//       const url = await createCustomerPortal.mutateAsync();
//       // Redirect to the customer portal
//       window.location.href = url;
//     } catch (error) {
//       console.error("Error redirecting to customer portal:", error);
//     } finally {
//       setLoading(false);
//     }
//   };

//   return (
//     <Button disabled={loading} onClick={redirectToCustomerPortal}>
//       Manage Subscription
//     </Button>
//   );
// };
// export const SubscriptionManager = () => {
//   const { data: user } = useSuspenseQuery(userQueryOptions());
//   const userOrganization = user.user_organizations?.find(
//     (userOrg) => userOrg.organization.uuid === user?.active_organization_uuid
//   );
//   const planType =
//     (userOrganization?.organization.billing?.lookup_key as PlanType) ?? PlanType.FREE;
//   const pricingTier = [
//     {
//       name: "Basic Plan",
//       price: "$0",
//       description: "Basic features for individual users.",
//       badge: "Open Beta",
//       variant: "outline",
//       planType: PlanType.FREE,
//       customButton:
//         planType === PlanType.FREE ? (
//           <Button disabled={true}>Current Plan</Button>
//         ) : (
//           <ManageSubscription />
//         ),
//     },
//     {
//       name: "Pro Plan",
//       price: "$10",
//       description: "Access to all features and priority support.",
//       buttonText: planType === PlanType.PRO ? "Current Plan" : "Change to Pro",
//       badge: "Closed Beta",
//       variant: "default",
//       planType: PlanType.PRO,
//       disabled: planType === PlanType.PRO,
//     },
//     {
//       name: "Team Plan",
//       price: "$10",
//       description: "Access to all features and priority support.",
//       buttonText: planType === PlanType.TEAM ? "Current Plan" : "Change to Team",
//       badge: "Closed Beta",
//       variant: "default",
//       planType: PlanType.TEAM,
//       disabled: planType === PlanType.TEAM,
//     },
//   ];
//   return (
//     <LilypadDialog
//       text="Manage Plan"
//       title="Change Plan"
//       description="Manage your subscription plan"
//       dialogContentProps={{ className: "max-w-[90%]" }}
//     >
//       <div className="grid grid-cols-3 gap-6">
//         {pricingTier.map((tier, index) => (
//           <PricingTier
//             key={index}
//             name={tier.name}
//             price={tier.price}
//             description={tier.description}
//             buttonText={tier.buttonText}
//             badge={tier.badge as "Open Beta" | "Closed Beta"}
//             variant={tier.variant as "default" | "outline"}
//             planType={tier.planType}
//             customButton={tier.customButton}
//             disabled={tier.disabled}
//           />
//         ))}
//       </div>
//     </LilypadDialog>
//   );
// };
