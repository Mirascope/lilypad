export function invariant(cond?: boolean, message?: string, ..._args: string[]): asserts cond {
  if (cond) {
    return;
  }

  throw new Error(
    "Internal Lexical error: invariant() is meant to be replaced at compile " +
      "time. There is no runtime version. Error: " +
      message
  );
}

export function setDomHiddenUntilFound(dom: HTMLElement): void {
  // @ts-expect-error
  dom.hidden = "until-found";
}

export function domOnBeforeMatch(dom: HTMLElement, callback: () => void): void {
  // @ts-expect-error
  dom.onbeforematch = callback;
}
