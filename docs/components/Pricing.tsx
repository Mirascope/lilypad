import Link from "next/link";
import { useEffect, useState } from "react";
import { cn } from "../lib/utils";
import { Button } from "./ui/button";

interface PlanFeature {
  name: string;
  included: boolean;
}

interface PricingTier {
  name: string;
  price: string;
  description: string;
  features: PlanFeature[];
  buttonText: string;
  buttonLink: string;
  highlight?: boolean;
  closedBeta?: boolean;
  comingSoon?: boolean;
}

export const Pricing = () => {
  const [activeTab, setActiveTab] = useState(0);
  const [isMobile, setIsMobile] = useState(false);

  useEffect(() => {
    // Function to check if screen is mobile width
    const checkIfMobile = () => {
      setIsMobile(window.innerWidth < 1280); // lg breakpoint is 1024px
    };

    // Check on initial load
    checkIfMobile();

    // Listen for window resize events
    window.addEventListener("resize", checkIfMobile);

    // Cleanup listener on component unmount
    return () => window.removeEventListener("resize", checkIfMobile);
  }, []);

  const pricingTiers: PricingTier[] = [
    {
      name: "Free",
      price: "$0",
      description:
        "Everything individual developers need to get started for small projects.",
      features: [
        { name: "Automatic Versioning & Tracing", included: true },
        { name: "10K Traces / Month", included: true },
        { name: "Single User", included: true },
        { name: "Unlimited Projects", included: true },
        { name: "Private Slack Channel", included: false },
        { name: "Managed Generations", included: false },
        { name: "Analysis Tooling", included: false },
        { name: "Annotations", included: false },
        { name: "SSO", included: false },
      ],
      buttonText: "Get Started",
      buttonLink: "/docs/quickstart",
    },
    {
      name: "Pro",
      price: "$500 / month",
      description:
        "Enhanced features for teams that need collaboration tools and higher limits.",
      features: [
        { name: "Automatic Versioning & Tracing", included: true },
        { name: "100K Traces / month", included: true },
        { name: "10 Users", included: true },
        { name: "Unlimited Projects", included: true },
        { name: "Private Slack Channel", included: true },
        { name: "Managed Generations", included: true },
        { name: "Analysis Tooling", included: true },
        { name: "Annotations", included: true },
        { name: "SSO", included: false },
      ],
      buttonText: "Contact Us",
      buttonLink: "mailto:sales@mirascope.com",
      highlight: true,
      closedBeta: true,
    },
    {
      name: "Enterprise",
      price: "Custom",
      description:
        "Custom solutions for large organizations with enterprise needs like compliance.",
      features: [
        { name: "Automatic Versioning & Tracing", included: true },
        { name: "Custom Trace Limits", included: true },
        { name: "Unlimited Users", included: true },
        { name: "Unlimited Projects", included: true },
        { name: "Private Slack Channel", included: true },
        { name: "Managed Generations", included: true },
        { name: "Analysis Tooling", included: true },
        { name: "Annotations", included: true },
        { name: "SSO", included: true },
      ],
      buttonText: "Contact Us",
      buttonLink: "mailto:sales@mirascope.com",
      comingSoon: true,
    },
  ];

  const renderPricingCard = (
    tier: PricingTier,
    index: number,
    isMobileView = false
  ) => (
    <div
      key={tier.name}
      className={cn(
        "rounded-lg border bg-background p-6 shadow-sm flex flex-col h-auto min-w-fit w-[350px]",
        tier.highlight
          ? "border-primary relative ring-1 ring-primary"
          : "border-border"
      )}
    >
      {tier.highlight && (
        <div className="absolute -top-4 left-0 right-0 flex justify-center">
          <div className="bg-primary text-primary-foreground text-xs font-medium py-1 px-3 rounded-full">
            Recommended
          </div>
        </div>
      )}

      <div className="mb-2">
        <div className="flex sm:flex-row flex-col items-start sm:items-center gap-2">
          <h3 className="text-2xl font-bold">{tier.name}</h3>
          {tier.closedBeta && (
            <div className="inline-block border text-secondary-foreground text-xs font-medium py-1 px-2 rounded min-w-fit">
              Closed Beta
            </div>
          )}
          {tier.comingSoon && (
            <div className="inline-block border text-secondary-foreground text-xs font-medium py-1 px-2 rounded min-w-fit">
              Coming Soon
            </div>
          )}
        </div>
        <div className="mt-2 flex items-baseline">
          <span className="text-2xl font-medium tracking-tight text-gray-600">
            {tier.price}
          </span>
        </div>
        <p className="mt-3 text-gray-500 min-h-[60px] max-w-xs">
          {tier.description}
        </p>
      </div>

      <div className="mb-6">
        <div className="w-full">
          {tier.features.map((feature) => (
            <div key={feature.name} className="flex items-center py-2 w-full">
              <div
                className={cn(
                  "mr-3 h-4 w-4 flex-shrink-0 rounded-full flex items-center justify-center",
                  feature.included ? "bg-green-500" : "bg-gray-300"
                )}
              >
                {feature.included ? (
                  <svg
                    className="h-4 w-4 text-white"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M5 13l4 4L19 7"
                    />
                  </svg>
                ) : (
                  <svg
                    className="h-4 w-4 text-gray-400"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M6 18L18 6M6 6l12 12"
                    />
                  </svg>
                )}
              </div>
              <span
                className={cn(
                  "text-sm whitespace-nowrap",
                  feature.included ? "text-gray-700" : "text-gray-500"
                )}
              >
                {feature.name}
              </span>
            </div>
          ))}
        </div>
      </div>

      <div className="mt-auto">
        <Button
          className="w-full"
          variant={tier.highlight ? "default" : "outline"}
          asChild
        >
          <Link href={tier.buttonLink}>{tier.buttonText}</Link>
        </Button>
      </div>
    </div>
  );

  return (
    <div className="py-12 flex flex-col justify-center mx-auto px-4 sm:px-6 lg:px-8">
      <div className="text-center mb-16 self-center">
        <h1 className="text-4xl font-bold tracking-tight text-gray-900 sm:text-5xl">
          Simple, transparent pricing
        </h1>
        <p className="mt-4 text-xl text-gray-600">
          Choose the right plan for your needs
        </p>
      </div>

      {/* Mobile tabs */}
      {isMobile && (
        <div className="flex flex-col items-center mb-8">
          <div className="flex w-full max-w-sm rounded-md shadow-sm mb-10">
            {pricingTiers.map((tier, index) => (
              <button
                key={tier.name}
                type="button"
                onClick={() => setActiveTab(index)}
                className={cn(
                  "flex-1 justify-center relative flex items-center px-4 py-2 text-sm font-medium border",
                  index === 0 && "rounded-l-md",
                  index === pricingTiers.length - 1 && "rounded-r-md",
                  activeTab === index
                    ? "z-10 bg-primary border-primary text-white"
                    : "bg-background border-gray-300 text-gray-700 hover:bg-gray-50"
                )}
              >
                {tier.name}
              </button>
            ))}
          </div>
          <div className="w-full flex justify-center">
            {renderPricingCard(pricingTiers[activeTab], activeTab, true)}
          </div>
        </div>
      )}

      {/* Desktop layout */}
      {!isMobile && (
        <div className="flex justify-center gap-8 w-full">
          {pricingTiers.map((tier, index) => renderPricingCard(tier, index))}
        </div>
      )}

      <div className="mt-24 text-center">
        <h2 className="text-2xl font-bold tracking-tight text-gray-900 mb-2">
          Need to self-host?
        </h2>
        <p className="text-lg text-gray-600 max-w-2xl mx-auto mb-6">
          Self-hosted deployments use the same pricing tiers with identical
          features.
        </p>
        <Button size="lg" variant="outline" asChild>
          <Link href="/self-hosting">View Self-Hosting Docs</Link>
        </Button>
      </div>
    </div>
  );
};
