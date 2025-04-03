export const isLilypadCloud = (): boolean => {
  const hostname = window.location.hostname;
  const domainSuffix = ".lilypad.so";
  return hostname.endsWith(domainSuffix);
};
