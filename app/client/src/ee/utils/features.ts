interface FeatureSettings {
  users: number;
  traces: boolean;
  functions: boolean;
  diffTooling: boolean;
  playground: boolean;
  annotations: boolean;
  vibeSynthesis: boolean;
}

export const selfHostedFeatures: FeatureSettings[] = [
  {
    users: Infinity,
    traces: true,
    functions: true,
    diffTooling: true,
    playground: false,
    annotations: false,
    vibeSynthesis: false,
  },
  {
    users: Infinity, // By license
    traces: true,
    functions: true,
    diffTooling: true,
    playground: true,
    annotations: true,
    vibeSynthesis: false,
  },
  {
    users: Infinity, // By license
    traces: true,
    functions: true,
    diffTooling: true,
    playground: true,
    annotations: true,
    vibeSynthesis: true,
  },
  {
    users: Infinity, // By license
    traces: true,
    functions: true,
    diffTooling: true,
    playground: true,
    annotations: true,
    vibeSynthesis: true,
  },
];
export const cloudFeatures: FeatureSettings[] = [
  {
    users: 1,
    traces: true,
    functions: true,
    diffTooling: true,
    playground: true,
    annotations: true,
    vibeSynthesis: true,
  },
  {
    users: 5,
    traces: true,
    functions: true,
    diffTooling: true,
    playground: true,
    annotations: true,
    vibeSynthesis: true,
  },
  {
    users: Infinity,
    traces: true,
    functions: true,
    diffTooling: true,
    playground: true,
    annotations: true,
    vibeSynthesis: true,
  },
  {
    users: Infinity,
    traces: true,
    functions: true,
    diffTooling: true,
    playground: true,
    annotations: true,
    vibeSynthesis: true,
  },
];
