import { Tier } from "@/ee/types/types";

interface FeatureSettings {
  users: number;
  managedGenerations: boolean;
  diffTooling: boolean;
  annotations: boolean;
  vibeSynthesis: boolean;
}

// Define the type for the features object
type FeaturesConfig = {
  [key in Tier]: FeatureSettings;
};

export const features: FeaturesConfig = {
  [Tier.FREE]: {
    users: 1,
    managedGenerations: false,
    diffTooling: false,
    annotations: false,
    vibeSynthesis: false,
  },
  [Tier.PRO]: {
    users: 5,
    managedGenerations: true,
    diffTooling: true,
    annotations: true,
    vibeSynthesis: false,
  },
  [Tier.TEAM]: {
    users: Infinity,
    managedGenerations: true,
    diffTooling: true,
    annotations: true,
    vibeSynthesis: true,
  },
  [Tier.ENTERPRISE]: {
    users: Infinity,
    managedGenerations: true,
    diffTooling: true,
    annotations: true,
    vibeSynthesis: true,
  },
};
