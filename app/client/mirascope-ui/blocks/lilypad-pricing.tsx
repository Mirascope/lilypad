import { cn } from "@/mirascope-ui/lib/utils";
import { ButtonLink } from "@/mirascope-ui/ui/button-link";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/mirascope-ui/ui/tabs";
import { Check, X } from "lucide-react";

// Feature row component for displaying features with the same value across tiers
const FeatureRow = ({
  feature,
  free,
  pro,
  team,
}: {
  feature: string;
  free: string | boolean;
  pro: string | boolean;
  team: string | boolean;
}) => {
  // If all tiers have the exact same value (and it's not a boolean)
  const allSameNonBoolean = free === pro && pro === team && typeof free === "string" && free !== "";

  return (
    <div className="grid min-h-[48px] grid-cols-4 items-center gap-4 border-b border-border py-3">
      <div className="text-lg font-medium text-foreground">{feature}</div>

      {allSameNonBoolean ? (
        <div className="col-span-3 text-center text-lg whitespace-pre-line">{free}</div>
      ) : (
        <>
          <div className="text-center">
            {typeof free === "boolean" ? (
              <div className="flex justify-center">
                {free ? (
                  <div className="rounded-full bg-primary/30 p-1">
                    <Check size={16} className="text-primary" />
                  </div>
                ) : (
                  <div className="rounded-full bg-muted p-1">
                    <X size={16} className="text-muted-foreground" />
                  </div>
                )}
              </div>
            ) : (
              <span className="text-lg whitespace-pre-line text-foreground">{free}</span>
            )}
          </div>

          <div className="text-center">
            {typeof pro === "boolean" ? (
              <div className="flex justify-center">
                {pro ? (
                  <div className="rounded-full bg-primary/30 p-1">
                    <Check size={16} className="text-primary" />
                  </div>
                ) : (
                  <div className="rounded-full bg-muted p-1">
                    <X size={16} className="text-muted-foreground" />
                  </div>
                )}
              </div>
            ) : (
              <span className="text-lg whitespace-pre-line text-foreground">{pro}</span>
            )}
          </div>

          <div className="text-center">
            {typeof team === "boolean" ? (
              <div className="flex justify-center">
                {team ? (
                  <div className="rounded-full bg-primary/30 p-1">
                    <Check size={16} className="text-primary" />
                  </div>
                ) : (
                  <div className="rounded-full bg-muted p-1">
                    <X size={16} className="text-muted-foreground" />
                  </div>
                )}
              </div>
            ) : (
              <span className="text-lg whitespace-pre-line text-foreground">{team}</span>
            )}
          </div>
        </>
      )}
    </div>
  );
};

// Pricing tier component
const PricingTier = ({
  name,
  price,
  description,
  buttonText,
  buttonLink,
  customButton,
  badge,
  variant = "default",
}: {
  name: string;
  price: string;
  description: string;
  buttonText?: string;
  buttonLink?: string;
  customButton?: React.ReactNode;
  badge?: "Open Beta" | "Closed Beta";
  variant?: "default" | "outline";
}) => (
  <div className="overflow-hidden rounded-lg border border-border bg-background shadow-sm">
    <div className={cn("bg-background px-6 py-8")}>
      <div className="mb-2 flex items-center gap-2">
        <h3 className={cn("text-xl font-semibold text-foreground")}>{name}</h3>
        {badge && (
          <span
            className={cn(
              "rounded-md px-2 py-1 text-xs font-medium",
              badge === "Open Beta"
                ? "bg-primary/20 text-primary"
                : "bg-muted text-muted-foreground"
            )}
          >
            {badge}
          </span>
        )}
      </div>
      <p className="mb-5 text-muted-foreground">{description}</p>
      <div className="mb-6">
        <span className="text-3xl font-bold text-foreground">{price}</span>
        {price !== "TBD" && price !== "N/A" && (
          <span className="ml-1 text-sm text-muted-foreground">/ month</span>
        )}
      </div>
      {customButton ?? (
        <ButtonLink href={buttonLink ?? "/"} className="w-full" variant={variant}>
          {buttonText}
        </ButtonLink>
      )}
    </div>
  </div>
);

// Feature comparison table component
const FeatureComparisonTable = ({
  features,
}: {
  features: {
    feature: string;
    free: string | boolean;
    pro: string | boolean;
    team: string | boolean;
  }[];
}) => (
  <div className="overflow-hidden rounded-lg border border-border bg-background shadow-sm">
    <div className="border-b border-border bg-accent px-4 py-5 sm:px-6">
      <h3 className="text-lg font-medium text-accent-foreground">Feature Comparison</h3>
    </div>
    <div className="overflow-x-auto bg-background px-4 py-5 sm:p-6">
      {/* Table header */}
      <div className="grid grid-cols-4 gap-4 border-b border-border pb-4">
        <div className="text-lg font-medium text-muted-foreground">Feature</div>
        <div className="text-center text-lg font-medium text-muted-foreground">Free</div>
        <div className="text-center text-lg font-medium text-muted-foreground">Pro</div>
        <div className="text-center text-lg font-medium text-muted-foreground">Team</div>
      </div>

      {/* Table rows */}
      {features.map((feat, i) => (
        <FeatureRow
          key={i}
          feature={feat.feature}
          free={feat.free}
          pro={feat.pro}
          team={feat.team}
        />
      ))}
    </div>
  </div>
);

interface TierAction {
  buttonText?: string;
  buttonLink?: string;
  variant?: "default" | "outline";
  customButton?: React.ReactNode;
}

interface PricingActions {
  hosted: {
    free: TierAction;
    pro: TierAction;
    team: TierAction;
  };
  selfHosted: {
    free: TierAction;
    pro: TierAction;
    team: TierAction;
  };
}

interface LilypadPricingProps {
  actions: PricingActions;
}

export function LilypadPricing({ actions }: LilypadPricingProps) {
  // Cloud hosted features
  const cloudHostedFeatures = [
    { feature: "Projects", free: "Unlimited", pro: "Unlimited", team: "Unlimited" },
    { feature: "Users", free: "2", pro: "10", team: "Unlimited" },
    {
      feature: "Tracing",
      free: "30k spans / month",
      pro: "100k spans / month (thereafter $1 per 10k)",
      team: "1M spans / month (thereafter $1 per 10k)",
    },
    { feature: "Data Retention", free: "30 days", pro: "90 days", team: "180 days" },
    { feature: "Versioned Functions", free: true, pro: true, team: true },
    { feature: "Playground", free: true, pro: true, team: true },
    { feature: "Comparisons", free: true, pro: true, team: true },
    { feature: "Annotations", free: true, pro: true, team: true },
    { feature: "Support (Community)", free: true, pro: true, team: true },
    { feature: "Support (Chat / Email)", free: false, pro: true, team: true },
    { feature: "Support (Private Slack)", free: false, pro: false, team: true },
    { feature: "API Rate Limits", free: "10 / minute", pro: "100 / minute", team: "1000 / minute" },
  ];

  // Self-hosted features
  const selfHostedFeatures = [
    { feature: "Projects", free: "Unlimited", pro: "Unlimited", team: "Unlimited" },
    { feature: "Users", free: "Unlimited", pro: "As licensed", team: "As licensed" },
    { feature: "Tracing", free: "No limits", pro: "No limits", team: "No limits" },
    { feature: "Data Retention", free: "No limits", pro: "No limits", team: "No limits" },
    { feature: "Versioned Functions", free: true, pro: true, team: true },
    { feature: "Playground", free: false, pro: true, team: true },
    { feature: "Comparisons", free: false, pro: true, team: true },
    { feature: "Annotations", free: false, pro: true, team: true },
    { feature: "Support (Community)", free: true, pro: true, team: true },
    { feature: "Support (Chat / Email)", free: false, pro: true, team: true },
    { feature: "Support (Private Slack)", free: false, pro: false, team: true },
    { feature: "API Rate Limits", free: "No limits", pro: "No limits", team: "No limits" },
  ];

  return (
    <div className="px-4 py-4">
      <div className="mx-auto max-w-4xl">
        <div className="mb-4 text-center">
          <h1 className="mb-4 text-center text-4xl font-bold text-foreground">Lilypad Pricing</h1>
          <p className="mx-auto mb-2 max-w-2xl text-xl text-foreground">
            Get started with the Free plan today.
          </p>
          <p className="mx-auto max-w-2xl text-sm text-muted-foreground italic">
            No credit card required.
          </p>
        </div>

        <Tabs defaultValue="hosted" className="mb-10 w-full">
          <div className="mb-8 flex justify-center">
            <TabsList className="bg-muted px-1 py-5">
              <TabsTrigger value="hosted">Hosted By Us</TabsTrigger>
              <TabsTrigger value="selfhosted">Self Hosting</TabsTrigger>
            </TabsList>
          </div>

          {/* Hosted By Us Tab Content */}
          <TabsContent value="hosted">
            <div className="mb-10 grid gap-8 md:grid-cols-3">
              <PricingTier
                name="Free"
                price="$0"
                description="For individuals just getting started"
                buttonText={actions.hosted.free.buttonText}
                buttonLink={actions.hosted.free.buttonLink}
                badge="Open Beta"
                variant={actions.hosted.free.variant}
                customButton={actions.hosted.free.customButton}
              />
              <PricingTier
                name="Pro"
                price="TBD"
                description="For teams with more advanced needs"
                buttonText={actions.hosted.pro.buttonText}
                buttonLink={actions.hosted.pro.buttonLink}
                badge="Closed Beta"
                variant={actions.hosted.pro.variant ?? "outline"}
                customButton={actions.hosted.pro.customButton}
              />
              <PricingTier
                name="Team"
                price="TBD"
                description="For larger teams requiring dedicated support"
                buttonText={actions.hosted.team.buttonText}
                buttonLink={actions.hosted.team.buttonLink}
                badge="Closed Beta"
                variant={actions.hosted.team.variant ?? "outline"}
                customButton={actions.hosted.team.customButton}
              />
            </div>

            {/* Feature comparison table */}
            <FeatureComparisonTable features={cloudHostedFeatures} />
          </TabsContent>

          {/* Self Hosting Tab Content */}
          <TabsContent value="selfhosted">
            <div className="mb-10 grid gap-8 md:grid-cols-3">
              <PricingTier
                name="Free"
                price="$0"
                description="For individuals just getting started"
                buttonText={actions.selfHosted.free.buttonText}
                buttonLink={actions.selfHosted.free.buttonLink}
                badge="Open Beta"
                variant={actions.selfHosted.free.variant}
              />
              <PricingTier
                name="Pro"
                price="TBD"
                description="For teams with more advanced needs"
                buttonText={actions.selfHosted.pro.buttonText}
                buttonLink={actions.selfHosted.pro.buttonLink}
                badge="Closed Beta"
                variant={actions.selfHosted.pro.variant ?? "outline"}
              />
              <PricingTier
                name="Team"
                price="TBD"
                description="For larger teams requiring dedicated support"
                buttonText={actions.selfHosted.team.buttonText}
                buttonLink={actions.selfHosted.team.buttonLink}
                badge="Closed Beta"
                variant={actions.selfHosted.team.variant ?? "outline"}
              />
            </div>

            {/* Feature comparison table */}
            <FeatureComparisonTable features={selfHostedFeatures} />
          </TabsContent>
        </Tabs>

        {/* FAQ Section */}
        <div className="mt-16 rounded-lg border border-border bg-card p-8">
          <h2 className="mb-4 text-2xl font-semibold text-foreground">
            Frequently Asked Questions
          </h2>
          <div className="space-y-6">
            <div>
              <h3 className="mb-2 text-lg font-medium text-foreground">
                How long will the open beta last?
              </h3>
              <p className="text-muted-foreground">
                The open beta period is ongoing, and we'll provide advance notice before moving to
                paid plans.
              </p>
            </div>
            <div>
              <h3 className="mb-2 text-lg font-medium text-foreground">
                What happens when the beta ends?
              </h3>
              <p className="text-muted-foreground">
                All existing users will receive a grace period to evaluate which plan is right for
                them before making any changes.
              </p>
            </div>
          </div>
        </div>

        <div className="mt-16 text-center">
          <h2 className="mb-4 text-2xl font-semibold text-foreground">
            Have questions about our pricing?
          </h2>
          <p className="text-muted-foreground">
            Join our{" "}
            <ButtonLink
              href="https://join.slack.com/t/mirascope-community/shared_invite/zt-2ilqhvmki-FB6LWluInUCkkjYD3oSjNA"
              variant="link"
              className="h-auto p-0"
            >
              community
            </ButtonLink>{" "}
            and ask the team directly!
          </p>
        </div>
      </div>
    </div>
  );
}
