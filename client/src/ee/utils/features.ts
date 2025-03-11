interface FeatureSettings {
  users: number;
  traces: boolean;
  generations: boolean;
  managedGenerations: boolean;
  diffTooling: boolean;
  annotations: boolean;
  vibeSynthesis: boolean;
}

export const features: FeatureSettings[] = [
  {
    users: 1,
    traces: true,
    generations: true,
    managedGenerations: false,
    diffTooling: false,
    annotations: false,
    vibeSynthesis: false,
  },
  {
    users: 5,
    traces: true,
    generations: true,
    managedGenerations: true,
    diffTooling: true,
    annotations: true,
    vibeSynthesis: false,
  },
  {
    users: Infinity,
    traces: true,
    generations: true,
    managedGenerations: true,
    diffTooling: true,
    annotations: true,
    vibeSynthesis: true,
  },
  {
    users: Infinity,
    traces: true,
    generations: true,
    managedGenerations: true,
    diffTooling: true,
    annotations: true,
    vibeSynthesis: true,
  },
];
