import { JSX } from "react";

export enum TraceTab {
  CODE = "code",
  SIGNATURE = "signature",
}

export interface Tab {
  label: string;
  value: TraceTab;
  component?: JSX.Element | null;
}
