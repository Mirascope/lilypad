export const isLilypadCloud = (): boolean => {
  const hostname = window.location.hostname;
  const domainSuffix = ".lilypad.so";
  const mirascopeDomainSuffix = ".mirascope.com";
  return hostname.endsWith(domainSuffix) || hostname.endsWith(mirascopeDomainSuffix);
};
